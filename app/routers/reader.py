"""Router for text reading operations.

This module provides enhanced endpoints for text reading functionality including:
- Text display with reference-based navigation
- Hierarchical reference extraction and browsing
- XML to HTML transformation with enhanced styling options
- Metadata exposure with rich context
- Token-level text processing
"""

from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_catalog_service, get_xml_service
from app.services.catalog_service import CatalogService
from app.services.enhanced_xml_service import EnhancedXMLService

# Templates
templates = Jinja2Templates(directory="app/templates")

# Create router
router = APIRouter(
    prefix="/api/v2",
    tags=["reader"],
    responses={404: {"description": "Not found"}},
)


@router.get("/read/{text_id}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    text_id: str = Path(..., description="Text ID"),
    reference: Optional[str] = Query(None, description="Optional reference to navigate to"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_xml_service),
):
    """Read a text with optional reference.

    Args:
        request: FastAPI request object
        text_id: Text ID
        reference: Optional reference to navigate to
        catalog_service: CatalogService instance
        xml_service: XML service for processing text

    Returns:
        HTMLResponse with rendered text
    """
    # Look up the text in the catalog
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    try:
        # Get the actual content path
        if not text.path:
            raise HTTPException(status_code=404, detail=f"No path found for text: {text_id}")

        # Load and process the document
        xml_root = xml_service.load_xml_from_path(text.path)
        
        # Get the HTML content
        html_content = xml_service.transform_to_html(xml_root, reference)
        
        # Get adjacent references for navigation if a reference is provided
        adjacent_refs = xml_service.get_adjacent_references(xml_root, reference) if reference else {"prev": None, "next": None}

        # Get author if available
        author = None
        if text.author_id:
            for a in catalog_service.get_all_authors():
                if a.id == text.author_id:
                    author = a
                    break

        # Render the template with the processed content
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "author": author,
                "content": html_content,
                "reference": reference,
                "prev_ref": adjacent_refs["prev"],
                "next_ref": adjacent_refs["next"],
            },
        )
    except Exception as e:
        logger.exception(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")


@router.get("/document/{text_id}", response_class=JSONResponse)
async def get_document(
    text_id: str = Path(..., description="Text ID"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_xml_service),
):
    """Get document structure for a text.

    Args:
        text_id: Text ID
        catalog_service: CatalogService instance
        xml_service: XML service for processing

    Returns:
        JSONResponse with document structure
    """
    # Look up the text in the catalog
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    try:
        # Get the actual content path
        if not text.path:
            raise HTTPException(status_code=404, detail=f"No path found for text: {text_id}")

        # Load and process the document
        xml_root = xml_service.load_xml_from_path(text.path)
        
        # Get all references
        references = xml_service.extract_references(xml_root)
        
        # Convert to a list of reference objects
        ref_list = []
        for ref, element in references.items():
            ref_list.append({
                "reference": ref,
                "text": "".join(element.itertext())[:100] + "..." if len("".join(element.itertext())) > 100 else "".join(element.itertext()),
            })
        
        # Sort references
        ref_list.sort(key=lambda x: [int(n) if n.isdigit() else n for n in x["reference"].split(".")])
        
        return ref_list
    except Exception as e:
        logger.exception(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/passage/{text_id}/{reference}", response_class=HTMLResponse)
async def get_passage(
    request: Request,
    text_id: str = Path(..., description="Text ID"),
    reference: str = Path(..., description="Reference string"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_xml_service),
):
    """Get a specific passage from a text by reference.

    Args:
        request: FastAPI request object
        text_id: Text ID
        reference: Reference string
        catalog_service: CatalogService instance
        xml_service: XML service for processing

    Returns:
        HTMLResponse with the specific passage
    """
    # Look up the text in the catalog
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    try:
        # Get the actual content path
        if not text.path:
            raise HTTPException(status_code=404, detail=f"No path found for text: {text_id}")

        # Load and process the document
        xml_root = xml_service.load_xml_from_path(text.path)
        
        # Get the specific passage
        passage = xml_service.get_passage_by_reference(xml_root, reference)
        if not passage:
            raise HTTPException(status_code=404, detail=f"Reference not found: {reference}")
        
        # Transform the passage to HTML
        html_content = xml_service._process_element_to_html(passage, reference)
        
        # Get adjacent references for navigation
        adjacent_refs = xml_service.get_adjacent_references(xml_root, reference)
        
        # Render the passage template
        return templates.TemplateResponse(
            "partials/passage.html",
            {
                "request": request,
                "text": text,
                "content": html_content,
                "reference": reference,
                "prev_ref": adjacent_refs["prev"],
                "next_ref": adjacent_refs["next"],
            },
        )
    except Exception as e:
        logger.exception(f"Error processing passage: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing passage: {str(e)}")


@router.get("/references/{text_id}", response_class=JSONResponse)
async def get_references(
    text_id: str = Path(..., description="Text ID"),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_xml_service),
):
    """Get all references for a text.

    Args:
        text_id: Text ID
        catalog_service: CatalogService instance
        xml_service: XML service for processing

    Returns:
        JSONResponse with all references
    """
    # Look up the text in the catalog
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    try:
        # Get the actual content path
        if not text.path:
            raise HTTPException(status_code=404, detail=f"No path found for text: {text_id}")

        # Load and process the document
        xml_root = xml_service.load_xml_from_path(text.path)
        
        # Get all references
        references = xml_service.extract_references(xml_root)
        
        # Return just the list of reference strings
        return {"references": sorted(references.keys(), key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])}
    except Exception as e:
        logger.exception(f"Error processing references: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing references: {str(e)}")


@router.post("/texts/{text_id}/archive")
async def archive_text(
    text_id: str,
    archive: bool = Query(True, description="True to archive, False to unarchive"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Archive or unarchive a text.

    Args:
        text_id: Text ID
        archive: True to archive, False to unarchive
        catalog_service: CatalogService instance

    Returns:
        JSON response indicating success or failure
    """
    success = catalog_service.archive_text_by_id(text_id, archive)
    if not success:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")
    
    return {"success": True, "archived": archive}


@router.post("/texts/{text_id}/favorite")
async def favorite_text(
    text_id: str,
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Toggle favorite status for a text.

    Args:
        text_id: Text ID
        catalog_service: CatalogService instance

    Returns:
        JSON response indicating success and the new favorite status
    """
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")
    
    success = catalog_service.toggle_text_favorite_by_id(text_id)
    
    # Get the updated text to get the current favorite status
    text = catalog_service.get_text_by_id(text_id)
    
    return {"success": success, "favorite": text.favorite if text else False} 