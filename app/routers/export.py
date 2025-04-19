"""Export router for the Eulogos API.

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

from app.dependencies import get_catalog_service, get_export_service, get_xml_service
from app.middleware.security import User, get_current_user, requires_scope
from app.middleware.validation import ExportOptions, RequestValidators
from app.services.catalog_service import CatalogService
from app.services.export_service import ExportService
from app.services.xml_processor_service import XMLProcessorService

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

# Export progress tracker class
class ExportProgress:
    """Track progress of a batch export operation."""

    def __init__(self, total_files: int):
        """Initialize progress tracker.
        
        Args:
            total_files: Total number of files to export
        """
        self.job_id = str(uuid.uuid4())
        self.total_files = total_files
        self.completed_files = 0
        self.failed_files = 0
        self.errors: Dict[str, str] = {}
        self.files: List[Dict[str, str]] = []
        self.status = "IN_PROGRESS"
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        
        # Store in global progress tracker
        export_progress[self.job_id] = self.to_dict()
        
    def increment_completed(self):
        """Increment completed files counter."""
        self.completed_files += 1
        self._update_status()
        
    def add_error(self, text_id: str, error: str):
        """Add error for a text.
        
        Args:
            text_id: ID of the text that failed
            error: Error message
        """
        self.failed_files += 1
        self.errors[text_id] = error
        self._update_status()
        
    def add_file(self, text_id: str, path: str, format: str):
        """Add exported file.
        
        Args:
            text_id: ID of the text
            path: Path to the exported file
            format: Format of the exported file
        """
        self.files.append({
            "text_id": text_id,
            "path": path,
            "format": format
        })
        self._update_status()
        
    def _update_status(self):
        """Update status based on progress."""
        if self.completed_files + self.failed_files >= self.total_files:
            self.status = "COMPLETED"
            self.end_time = datetime.now()
        
        # Update in global tracker
        export_progress[self.job_id] = self.to_dict()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "job_id": self.job_id,
            "total_files": self.total_files,
            "completed_files": self.completed_files,
            "failed_files": self.failed_files,
            "errors": self.errors,
            "files": self.files,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "progress": f"{self.completed_files}/{self.total_files} ({self.completed_files/self.total_files*100:.1f}%)"
        }


async def process_export(
    text_id: str, options: ExportOptions, export_service: ExportService, progress: ExportProgress
) -> Optional[Path]:
    """Process single export."""
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
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
    validators: RequestValidators = Depends(),
) -> Dict[str, Any]:
    """Start batch export process."""
    # Validate all text IDs and options
    # No validation needed for text IDs

    # Create progress tracker
    progress = ExportProgress(len(text_ids))

    # Create export service with temp directory
    export_service = ExportService(
        catalog_service=catalog_service, xml_service=xml_service, output_dir=f"exports/{progress.job_id}"
    )

    # Start background task
    background_tasks.add_task(process_batch_export, text_ids, options, export_service, progress)

    return {"message": "Batch export started", "job_id": progress.job_id}


async def process_batch_export(
    text_ids: List[str],
    options: ExportOptions, 
    export_service: ExportService, 
    progress: ExportProgress
):
    """Process batch export in background.
    
    Args:
        text_ids: List of text IDs to export
        options: Export options
        export_service: Export service instance
        progress: Progress tracker
    """
    # Process all text IDs
    paths = []
    for text_id in text_ids:
        try:
            path = await process_export(text_id, options, export_service, progress)
            if path:
                paths.append(path)
                progress.add_file(text_id, str(path), options.format)
        except Exception as e:
            logger.error(f"Error exporting {text_id}: {e}")
            progress.add_error(text_id, str(e))
    
    # If zip option is set, create a ZIP file with all exports
    if options.batch_zip and paths:
        try:
            zip_path = f"exports/{progress.job_id}/batch_export.zip"
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                for path in paths:
                    zip_file.write(path, os.path.basename(path))
            progress.files.append({
                "text_id": "batch",
                "path": zip_path,
                "format": "zip"
            })
        except Exception as e:
            logger.error(f"Error creating batch ZIP: {e}")
            progress.add_error("batch_zip", str(e))


@router.get("/status/{job_id}")
@requires_scope(["export:texts"])
async def get_export_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get export status."""
    if job_id not in export_progress:
        raise HTTPException(status_code=404, detail=f"Export job not found: {job_id}")

    return export_progress[job_id]


@router.get("/download/{job_id}")
@requires_scope(["export:texts"])
async def download_export(
    job_id: str,
    file_index: int = 0,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Download exported file."""
    if job_id not in export_progress:
        raise HTTPException(status_code=404, detail=f"Export job not found: {job_id}")

    progress = export_progress[job_id]
    
    if file_index >= len(progress["files"]):
        raise HTTPException(status_code=404, detail=f"File index out of range: {file_index}")
    
    file_info = progress["files"][file_index]
    file_path = file_info["path"]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    return StreamingResponse(
        open(file_path, "rb"),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={os.path.basename(file_path)}"}
    )


@router.post("/{text_id}")
@requires_scope(["export:texts"])
async def export_single(
    text_id: str,
    options: ExportOptions,
    current_user: User = Depends(get_current_user),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
    validators: RequestValidators = Depends(),
) -> Dict[str, Any]:
    """Export single text."""
    # Validate text ID and options
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    # Create export service
    export_service = ExportService(
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
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
) -> Dict[str, Any]:
    """Export single text by ID.
    
    Args:
        text_id: The stable ID of the text to export
        options: Export options
        current_user: Current authenticated user
        catalog_service: Catalog service
        xml_service: XML service
        
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
    export_service = ExportService(
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


@router.post("/path/{path:path}")
@requires_scope(["export:texts"])
async def export_single_by_path(
    path: str = PathParam(..., description="The canonical path to the text from catalog"),
    options: ExportOptions = None,
    current_user: User = Depends(get_current_user),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
) -> Dict[str, Any]:
    """Export single text by its canonical path.
    
    Args:
        path: The canonical path to the text (as found in catalog)
        options: Export options
        current_user: Current authenticated user
        catalog_service: Catalog service
        xml_service: XML service
        
    Returns:
        Export result with path and format
        
    Raises:
        HTTPException: If text not found or export fails
    """
    # Find the text by path in the catalog
    text = None
    for t in catalog_service._texts_by_id.values():
        if t.path == path:
            text = t
            break
    
    text_id = text.id if text else None
        
    # Create export service
    export_service = ExportService(
        catalog_service=catalog_service, xml_service=xml_service, output_dir="exports/single"
    )

    try:
        # Can we directly load XML from path?
        xml_root = xml_service.load_xml_from_path(path)
        
        # Set options for use in metadata
        options_dict = options.dict() if options else {}
        
        # Check if we need to modify the ExportService to handle paths directly
        # For now, we'll use the text ID if available, or work with the path directly
        if text_id:
            if options.format == "html":
                output_path = export_service.export_to_html(text_id, options_dict)
            elif options.format == "markdown":
                output_path = export_service.export_to_markdown(text_id, options_dict)
            elif options.format == "latex":
                output_path = export_service.export_to_latex(text_id, options_dict)
            elif options.format == "pdf":
                output_path = export_service.export_to_pdf(text_id, options_dict)
            elif options.format == "epub":
                output_path = export_service.export_to_epub(text_id, options_dict)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported format: {options.format}")
        else:
            # For direct path handling, we might need to extend ExportService
            # This is a placeholder that needs implementation in the service
            raise HTTPException(status_code=501, detail="Direct path-based export not implemented")

        return {
            "message": "Export successful", 
            "path": str(output_path), 
            "format": options.format, 
            "text_path": path,
            "text_id": text_id
        }
    except Exception as e:
        logger.error(f"Error exporting path {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}") 