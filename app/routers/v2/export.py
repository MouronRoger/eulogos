"""Export router for version 2 of the Eulogos API.

This module provides endpoints for text export functionality including:
- Single text export in various formats (HTML, Markdown, LaTeX, PDF, EPUB)
- Batch export with progress tracking
- Export status monitoring
- Export file download
- Support for compression and custom formatting options
"""

import asyncio
import logging
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path as PathParam
from fastapi.responses import StreamingResponse

from app.dependencies import get_enhanced_catalog_service, get_enhanced_xml_service
from app.middleware.security import User, get_current_user, requires_scope
from app.middleware.validation import ExportOptions, RequestValidators
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_export_service import EnhancedExportService
from app.services.enhanced_xml_service import EnhancedXMLService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v2/export",
    tags=["export"],
    responses={404: {"description": "Not found"}},
)

# In-memory storage for export progress
# In production, use Redis or similar
export_progress: Dict[str, Dict[str, Any]] = {}


class ExportProgress:
    """Track export progress."""

    def __init__(self, total_items: int):
        """Initialize progress tracker."""
        self.job_id = str(uuid.uuid4())
        self.total_items = total_items
        self.completed_items = 0
        self.failed_items = 0
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.status = "in_progress"
        self.errors: List[Dict[str, str]] = []

        # Store in global progress tracker
        export_progress[self.job_id] = self.to_dict()

    def increment_completed(self):
        """Increment completed items."""
        self.completed_items += 1
        self._update_progress()

    def add_error(self, text_id: str, error: str):
        """Add error for text ID."""

        self.errors.append({"text_id": text_id, "error": error})
        self._update_progress()

    def complete(self):
        """Mark export as complete."""
        self.end_time = datetime.utcnow()
        self.status = "completed"
        self._update_progress()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "progress": self.get_progress(),
            "errors": self.errors,
        }

    def get_progress(self) -> float:
        """Get progress percentage."""
        return (self.completed_items + self.failed_items) / self.total_items * 100

    def _update_progress(self):
        """Update progress in storage."""
        export_progress[self.job_id] = self.to_dict()


async def process_export(
    text_id: str, options: ExportOptions, export_service: EnhancedExportService, progress: ExportProgress
) -> Optional[Path]:
    """Process single export."""
    try:
        if options.format == "html":
            text = export_service.catalog_service.get_text_by_id(text_id)
    if not text:
        progress.add_error(text_id, f"Text not found: {text_id}")
        progress.increment_failed()
        return None

    path = export_service.export_to_html(text_id, options.dict())
        elif options.format == "markdown":
            path = export_service.export_to_markdown(text_id, options.dict())
        elif options.format == "latex":
            path = export_service.export_to_latex(text_id, options.dict())
        elif options.format == "pdf":
            path = export_service.export_to_pdf(text_id, options.dict())
        elif options.format == "epub":
            path = export_service.export_to_epub(text_id, options.dict())
        else:
            raise ValueError(f"Unsupported format: {options.format}")

        progress.increment_completed()
        return path
    except Exception as e:
        logger.error(f"Error exporting {text_id}: {e}")
        progress.add_error(text_id, str(e))
        return None


@router.post("/batch")
@requires_scope(["export:texts"])
async def batch_export(
    text_ids: List[str],
    options: ExportOptions,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
    validators: RequestValidators = Depends(),
) -> Dict[str, Any]:
    """Start batch export process."""
    # Validate all text IDs and options
    # No validation needed for text IDs

    # Create progress tracker
    progress = ExportProgress(len(text_ids))

    # Create export service with temp directory
    export_service = EnhancedExportService(
        catalog_service=catalog_service, xml_service=xml_service, output_dir=f"exports/{progress.job_id}"
    )

    # Start background task
    background_tasks.add_task(process_batch_export, text_ids, options, export_service, progress)

    return {"message": "Batch export started", "job_id": progress.job_id}


async def process_batch_export(
    text_ids: List[str], options: ExportOptions, export_service: EnhancedExportService, progress: ExportProgress
):
    """Process batch export in background."""
    try:
        # Process exports concurrently
        tasks = [process_export(text_id, options, export_service, progress) for text_id in text_ids]
        paths = await asyncio.gather(*tasks)

        # Create zip file if needed
        if options.compression == "zip":
            zip_path = Path(export_service.output_dir) / "export.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in paths:
                    if path and path.exists():
                        zf.write(path, path.name)

        progress.complete()
    except Exception as e:
        logger.error(f"Error in batch export: {e}")
        progress.status = "failed"
        progress.errors.append({"text_id": "batch", "error": str(e)})
        progress._update_progress()


@router.get("/status/{job_id}")
@requires_scope(["export:texts"])
async def get_export_status(job_id: str, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Get status of batch export."""
    if job_id not in export_progress:
        raise HTTPException(status_code=404, detail="Export job not found")
    return export_progress[job_id]


@router.get("/download/{job_id}")
@requires_scope(["export:texts"])
async def download_export(job_id: str, current_user: User = Depends(get_current_user)) -> StreamingResponse:
    """Download completed export."""
    if job_id not in export_progress:
        raise HTTPException(status_code=404, detail="Export job not found")

    progress = export_progress[job_id]
    if progress["status"] != "completed":
        raise HTTPException(status_code=400, detail="Export not completed")

    zip_path = Path(f"exports/{job_id}/export.zip")
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")

    def iterfile():
        with open(zip_path, "rb") as f:
            yield from f

    return StreamingResponse(
        iterfile(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=export_{job_id}.zip"},
    )


@router.post("/{text_id}")
@requires_scope(["export:texts"])
async def export_single(
    text_id: str,
    options: ExportOptions,
    current_user: User = Depends(get_current_user),
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
    validators: RequestValidators = Depends(),
) -> Dict[str, Any]:
    """Export single text."""
    # Validate text ID and options
    # No validation needed for text ID

    # Create export service
    export_service = EnhancedExportService(
        catalog_service=catalog_service, xml_service=xml_service, output_dir="exports/single"
    )

    try:
        if options.format == "html":
            path = export_service.export_to_html(text_id, options.dict())
        elif options.format == "markdown":
            path = export_service.export_to_markdown(text_id, options.dict())
        elif options.format == "latex":
            path = export_service.export_to_latex(text_id, options.dict())
        elif options.format == "pdf":
            path = export_service.export_to_pdf(text_id, options.dict())
        elif options.format == "epub":
            path = export_service.export_to_epub(text_id, options.dict())
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {options.format}")

        return {"message": "Export successful", "path": str(path), "format": options.format, "text_id": text_id}
    except Exception as e:
        logger.error(f"Error exporting {text_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/id/{text_id}")
@requires_scope(["export:texts"])
async def export_single_by_id(
    text_id: str = PathParam(..., description="The stable ID of the text"),
    options: ExportOptions = None,
    current_user: User = Depends(get_current_user),
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
) -> Dict[str, Any]:
    """Export single text by ID.
    
    Args:
        text_id: The stable ID of the text to export
        options: Export options
        current_user: Current authenticated user
        catalog_service: Enhanced catalog service
        xml_service: Enhanced XML service
        
    Returns:
        Export result with path and format
        
    Raises:
        HTTPException: If text not found or export fails
    """
    # Get text from catalog by ID
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")
        
    

    # Create export service
    export_service = EnhancedExportService(
        catalog_service=catalog_service, xml_service=xml_service, output_dir="exports/single"
    )

    try:
        # Set text_id in options for use in metadata
        options_dict = options.dict() if options else {}
        options_dict["text_id"] = text_id
        
        if options.format == "html":
            path = export_service.export_to_html(text_id, options_dict)
        elif options.format == "markdown":
            path = export_service.export_to_markdown(text_id, options_dict)
        elif options.format == "latex":
            path = export_service.export_to_latex(text_id, options_dict)
        elif options.format == "pdf":
            path = export_service.export_to_pdf(text_id, options_dict)
        elif options.format == "epub":
            path = export_service.export_to_epub(text_id, options_dict)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {options.format}")

        return {"message": "Export successful", "path": str(path), "format": options.format, "text_id": text_id}
    except Exception as e:
        logger.error(f"Error exporting text ID {text_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
