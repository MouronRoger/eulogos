"""Read router for Eulogos application.

This module provides routes for reading texts and navigating by references.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.services.catalog_service import CatalogService, get_catalog_service
from app.services.xml_service import XMLService

# Initialize router
router = APIRouter(
    prefix="/read",
    tags=["read"],
)

# Templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/{path:path}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    path: str,
    reference: Optional[str] = None,
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLService = Depends(lambda: XMLService())
):
    """Read a specific text by path."""
    # Get text metadata from catalog
    text = catalog_service.get_text_by_path(path)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {path}")
    
    try:
        # Load XML content
        xml_root = xml_service.load_xml(path)
        if not xml_root:
            raise HTTPException(status_code=404, detail=f"Failed to load XML for: {path}")
        
        # Get metadata from XML
        xml_metadata = xml_service.get_metadata(xml_root)
        
        # Transform to HTML
        html_content = xml_service.transform_to_html(xml_root, reference)
        
        # Get references for navigation
        references = xml_service.extract_references(xml_root)
        
        # Get adjacent references if viewing a specific section
        if reference:
            adjacent_refs = xml_service.get_adjacent_references(xml_root, reference)
        else:
            adjacent_refs = {"prev": None, "next": None}
        
        # Render reader template
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "content": html_content,
                "path": path,
                "reference": reference,
                "prev_ref": adjacent_refs["prev"],
                "next_ref": adjacent_refs["next"],
                "metadata": xml_metadata,
                "has_references": len(references) > 0,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")


@router.get("/references/{path:path}", response_class=HTMLResponse)
async def get_references(
    request: Request,
    path: str,
    xml_service: XMLService = Depends(lambda: XMLService())
):
    """Get references for a text as HTML partial."""
    try:
        # Load XML content
        xml_root = xml_service.load_xml(path)
        if not xml_root:
            raise HTTPException(status_code=404, detail=f"Failed to load XML for: {path}")
        
        # Extract references
        references = xml_service.extract_references(xml_root)
        
        # Sort references
        def sort_key(ref):
            return [int(p) if p.isdigit() else p for p in ref.split(".")]
        
        sorted_refs = sorted(references.keys(), key=sort_key)
        
        # Render references partial
        return templates.TemplateResponse(
            "partials/references.html",
            {
                "request": request,
                "references": sorted_refs,
                "path": path,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading references: {str(e)}") 