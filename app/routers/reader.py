"""Router for text reading operations."""

from pathlib import Path
import re
import xml.etree.ElementTree as ET
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService

# Dependency to get catalog service
def get_catalog_service():
    """Get instance of catalog service.
    
    Returns:
        CatalogService instance
    """
    service = CatalogService(
        catalog_path="integrated_catalog.json",
        data_dir="data"
    )
    service.create_unified_catalog()
    return service

# Dependency to get XML processor service
def get_xml_processor():
    """Get instance of XML processor service.
    
    Returns:
        XMLProcessorService instance
    """
    return XMLProcessorService(data_path="data")

# Templates
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["reader"])

@router.get("/read/{urn}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    urn: str,
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_processor: XMLProcessorService = Depends(get_xml_processor)
):
    """Read a text.
    
    Args:
        request: FastAPI request object
        urn: The URN of the text to read
        catalog_service: CatalogService instance
        xml_processor: XMLProcessorService instance
        
    Returns:
        HTMLResponse with rendered template
        
    Raises:
        HTTPException: If text is not found
    """
    # Get text from catalog
    text = catalog_service.get_text_by_urn(urn)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {urn}")
    
    try:
        # Get file path from URN
        file_path = xml_processor.get_file_path(urn)
        
        # Check if file exists
        if not file_path.exists():
            return templates.TemplateResponse(
                "reader.html",
                {
                    "request": request,
                    "text": text,
                    "content": f"<p><em>XML file not found: {file_path}</em></p>",
                    "file_path": str(file_path)
                },
                status_code=404
            )
        
        # Extract text content
        content = xml_processor.extract_text_content(file_path)
        
        # Render template
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "content": content,
                "file_path": str(file_path)
            }
        )
    except Exception as e:
        # Return error message
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "content": f"<p><em>Error processing text: {str(e)}</em></p>",
                "file_path": "Unknown"
            },
            status_code=500
        ) 