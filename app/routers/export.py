"""Export router for the Eulogos API.

This module provides endpoints for text export functionality.
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from app.dependencies import get_enhanced_catalog_service, get_enhanced_xml_service
from app.middleware.validation import ExportOptions
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_export_service import EnhancedExportService
from app.services.enhanced_xml_service import EnhancedXMLService

router = APIRouter(
    prefix="/export",
    tags=["export"],
)


def get_export_service(
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
) -> EnhancedExportService:
    """Get an instance of the enhanced export service."""
    # Create temporary directory for exports
    temp_dir = tempfile.mkdtemp(prefix="eulogos_export_")
    return EnhancedExportService(catalog_service=catalog_service, xml_service=xml_service, output_dir=temp_dir)


def cleanup_export_file(file_path: Path):
    """Clean up exported file and its parent directory."""
    try:
        if file_path.exists():
            file_path.unlink()
        if file_path.parent.exists():
            file_path.parent.rmdir()
    except Exception as e:
        logger.error(f"Error cleaning up export file {file_path}: {e}")


@router.post("/export/{urn}/html", response_class=FileResponse)
async def export_to_html(
    urn: str,
    options: ExportOptions,
    background_tasks: BackgroundTasks,
    export_service: EnhancedExportService = Depends(get_export_service),
):
    """Export text to HTML."""
    try:
        # Validate URN
        try:
            urn_obj = EnhancedURN(value=urn)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid URN: {e}")

        # Export to HTML
        html_path = export_service.export_to_html(urn_obj, options.dict(exclude_unset=True))

        # Schedule cleanup
        background_tasks.add_task(cleanup_export_file, html_path)

        return FileResponse(html_path, media_type="text/html", filename=html_path.name, background=background_tasks)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Text not found: {urn}")
    except Exception as e:
        logger.error(f"Error exporting {urn} to HTML: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/{urn}/markdown", response_class=FileResponse)
async def export_to_markdown(
    urn: str,
    options: ExportOptions,
    background_tasks: BackgroundTasks,
    export_service: EnhancedExportService = Depends(get_export_service),
):
    """Export text to Markdown."""
    try:
        # Validate URN
        try:
            urn_obj = EnhancedURN(value=urn)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid URN: {e}")

        # Export to Markdown
        md_path = export_service.export_to_markdown(urn_obj, options.dict(exclude_unset=True))

        # Schedule cleanup
        background_tasks.add_task(cleanup_export_file, md_path)

        return FileResponse(md_path, media_type="text/markdown", filename=md_path.name, background=background_tasks)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Text not found: {urn}")
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting {urn} to Markdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/{urn}/latex", response_class=FileResponse)
async def export_to_latex(
    urn: str,
    options: ExportOptions,
    background_tasks: BackgroundTasks,
    export_service: EnhancedExportService = Depends(get_export_service),
):
    """Export text to LaTeX."""
    try:
        # Validate URN
        try:
            urn_obj = EnhancedURN(value=urn)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid URN: {e}")

        # Export to LaTeX
        latex_path = export_service.export_to_latex(urn_obj, options.dict(exclude_unset=True))

        # Schedule cleanup
        background_tasks.add_task(cleanup_export_file, latex_path)

        return FileResponse(
            latex_path, media_type="application/x-latex", filename=latex_path.name, background=background_tasks
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Text not found: {urn}")
    except Exception as e:
        logger.error(f"Error exporting {urn} to LaTeX: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/formats")
async def get_export_formats():
    """Get available export formats."""
    return {
        "formats": [
            {
                "id": "html",
                "name": "HTML",
                "description": "Export as standalone HTML file",
                "mime_type": "text/html",
                "extension": ".html",
            },
            {
                "id": "markdown",
                "name": "Markdown",
                "description": "Export as Markdown file",
                "mime_type": "text/markdown",
                "extension": ".md",
            },
            {
                "id": "latex",
                "name": "LaTeX",
                "description": "Export as LaTeX document",
                "mime_type": "application/x-latex",
                "extension": ".tex",
            },
        ]
    }
