"""
Integration Guide for XMLProcessorService in a FastAPI Application

This guide details how to integrate the XMLProcessorService for TEI XML processing
in a FastAPI application. It covers typical usage patterns, dependency injection,
endpoint design, and template integration.

Key architectural principle: 
- text_id is ALWAYS the full data path including filename
- The catalog is the ONLY source of truth for path resolution
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.services.xml_processor_service import XMLProcessorService
from app.services.catalog_service import CatalogService
from app.dependencies import get_catalog_service, get_xml_service

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Create router
router = APIRouter(
    prefix="/read",
    tags=["reader"],
)

# Example endpoint for reading a text
@router.get("/{text_id}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    text_id: str = Path(..., description="Text ID (full data path)"),
    reference: Optional[str] = Query(None, description="Optional reference to navigate to"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Read a text with optional reference.

    The text_id parameter represents the full path to the text file
    in the data directory, as stored in the catalog.

    Args:
        request: FastAPI request object
        text_id: Full data path to the text file, used as ID
        reference: Optional reference to navigate to
        catalog_service: CatalogService instance
        xml_service: XML service for processing text

    Returns:
        HTMLResponse with rendered text
    """
    try:
        # Get text from catalog - text_id is the full path to the file
        logger.debug(f"Looking up text with ID (path): {text_id}")
        text = catalog_service.get_text_by_id(text_id)
        if not text:
            logger.error(f"Text not found for ID (path): {text_id}")
            raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

        # Validate that text.id == text.path (they should always be the same)
        if text.id != text.path:
            logger.warning(f"Text ID {text.id} does not match path {text.path}")
            text.id = text.path  # Ensure ID and path are synchronized

        # Load document
        xml_root = xml_service.load_document(text_id)
        if xml_root is None:
            raise HTTPException(status_code=500, detail="Failed to load document")

        # Process the document
        html_content = xml_service.transform_to_html(text_id, reference)
        
        # Get adjacent references if a reference is provided
        adjacent_refs = {}
        if reference:
            adjacent_refs = xml_service.get_adjacent_references(xml_root, reference)
            
        # Extract metadata
        metadata = xml_service.extract_metadata(xml_root)
        
        # Get document statistics
        stats = xml_service.get_document_statistics(xml_root)
        
        # Combine text info with metadata
        text_data = {
            "id": text_id,  # text_id is the path
            "path": text.path,
            "title": metadata.get("title", text.work_name if hasattr(text, "work_name") else "Untitled"),
            "author": metadata.get("author", text.group_name if hasattr(text, "group_name") else "Unknown"),
            "language": metadata.get("language", getattr(text, "language", "Unknown")),
            "editor": metadata.get("editor", ""),
            "word_count": stats.get("word_count", 0),
        }

        # Render the template
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text_data,
                "content": html_content,
                "current_ref": reference,
                "prev_ref": adjacent_refs.get("prev"),
                "next_ref": adjacent_refs.get("next"),
                "metadata": metadata,
                "stats": stats,
            },
        )
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")


# Example endpoint for getting references
@router.get("/references/{text_id}")
async def get_references(
    text_id: str = Path(..., description="Text ID (full data path)"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Get references for a text.

    Args:
        text_id: Full data path to the text file, used as ID
        catalog_service: CatalogService instance
        xml_service: XML service for processing text

    Returns:
        List of references
    """
    try:
        # Get text from catalog - text_id is the full path to the file
        text = catalog_service.get_text_by_id(text_id)
        if not text:
            raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

        # Load document
        xml_root = xml_service.load_document(text_id)
        if xml_root is None:
            raise HTTPException(status_code=500, detail="Failed to load document")

        # Extract references
        references = xml_service.extract_references(xml_root)
        
        # Format for output
        result = []
        for ref, element in references.items():
            # Extract first few words of content for display
            text_content = "".join(element.itertext())
            preview = text_content[:50] + "..." if len(text_content) > 50 else text_content
            
            result.append({
                "reference": ref,
                "text": preview.strip(),
                "url": f"/read/{text_id}?reference={ref}",  # text_id is the path
            })
            
        # Sort references
        result.sort(key=lambda x: [int(t) if t.isdigit() else t.lower() for t in x["reference"].split(".")])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting references: {str(e)}")


# Example endpoint for getting a specific passage
@router.get("/passage/{text_id}/{reference}", response_class=HTMLResponse)
async def get_passage(
    request: Request,
    text_id: str = Path(..., description="Text ID (full data path)"),
    reference: str = Path(..., description="Reference string"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Get a specific passage from a text.

    Args:
        request: FastAPI request object
        text_id: Full data path to the text file, used as ID
        reference: Reference string
        catalog_service: CatalogService instance
        xml_service: XML service for processing text

    Returns:
        HTMLResponse with the passage content
    """
    try:
        # Get text from catalog - text_id is the full path to the file
        text = catalog_service.get_text_by_id(text_id)
        if not text:
            raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

        # Load document
        xml_root = xml_service.load_document(text_id)
        if xml_root is None:
            raise HTTPException(status_code=500, detail="Failed to load document")

        # Get the passage
        passage = xml_service.get_passage_by_reference(xml_root, reference)
        if passage is None:
            raise HTTPException(status_code=404, detail=f"Reference not found: {reference}")

        # Transform to HTML
        html_content = xml_service._process_element_to_html(passage, reference)
        
        # Get adjacent references
        adjacent_refs = xml_service.get_adjacent_references(xml_root, reference)
        
        # Render template
        return templates.TemplateResponse(
            "partials/passage.html",
            {
                "request": request,
                "text": text,
                "content": html_content,
                "reference": reference,
                "prev_ref": adjacent_refs.get("prev"),
                "next_ref": adjacent_refs.get("next"),
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting passage: {str(e)}")


# Example endpoint for exporting a text
@router.get("/export/{text_id}")
async def export_text(
    text_id: str = Path(..., description="Text ID (full data path)"),
    format: str = Query("html", description="Export format"),
    reference: Optional[str] = Query(None, description="Optional reference to export"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
):
    """Export a text in various formats.

    Args:
        text_id: Full data path to the text file, used as ID
        format: Export format (html, pdf, epub, etc.)
        reference: Optional reference to export
        catalog_service: CatalogService instance
        xml_service: XML service for processing text

    Returns:
        Export result with download link
    """
    try:
        # Get text from catalog - text_id is the full path to the file
        text = catalog_service.get_text_by_id(text_id)
        if not text:
            raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

        # Validate that text_id == text.path (they should always be the same)
        if text_id != text.path:
            logger.warning(f"Text ID {text_id} does not match path {text.path} - using path from catalog")
            text_id = text.path

        # Get export options
        options = {
            "format": format,
            "reference": reference,
            "text_id": text_id,  # Include text_id (path) in metadata
        }

        # Here you would call your export service
        # For demonstration, just return the options
        return {
            "message": "Export options prepared",
            "text_id": text_id,
            "options": options,
            "download_url": f"/api/download/export?path={text_id}&format={format}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preparing export: {str(e)}")
