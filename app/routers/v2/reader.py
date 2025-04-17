"""Router for text reading operations (v2 API).

This module provides enhanced endpoints for text reading functionality including:
- Text display with reference-based navigation
- Hierarchical reference extraction and browsing
- XML to HTML transformation with enhanced styling options
- Metadata exposure with rich context
- Token-level text processing
"""

from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_enhanced_catalog_service, get_enhanced_xml_service
from app.models.enhanced_urn import EnhancedURN
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService

# Templates
templates = Jinja2Templates(directory="app/templates")

# Create router
router = APIRouter(
    prefix="/api/v2",
    tags=["reader"],
    responses={404: {"description": "Not found"}},
)


@router.get("/read/{urn}", response_class=HTMLResponse, response_model=None)
async def read_text(
    request: Request,
    urn: str,
    reference: Optional[str] = None,
    format_options: Optional[Dict] = None,
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
):
    """Read a text with optional reference navigation.

    Args:
        request: FastAPI request object
        urn: The URN of the text to read
        reference: Optional reference to navigate to
        format_options: Optional formatting options
        catalog_service: EnhancedCatalogService instance
        xml_service: EnhancedXMLService instance

    Returns:
        HTMLResponse with rendered template

    Raises:
        HTTPException: If text is not found
    """
    # Parse URN using enhanced URN model
    try:
        EnhancedURN.from_string(urn)  # Validate URN format
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URN: {e}")

    # Get text from catalog
    text = catalog_service.get_text_by_urn(urn)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {urn}")

    try:
        # Load XML document
        document = xml_service.load_document(urn)

        # Get adjacent references
        adjacent_refs = xml_service.get_adjacent_references(document, reference)

        # Transform to HTML with reference highlighting
        html_content = xml_service.transform_to_html(document, reference, format_options)

        # Get document metadata
        metadata = xml_service.extract_metadata(document)

        # Render template
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "content": html_content,
                "urn": urn,
                "current_ref": reference,
                "prev_ref": adjacent_refs["prev"],
                "next_ref": adjacent_refs["next"],
                "metadata": metadata,
                "references_available": True,
            },
        )
    except Exception as e:
        # Return error message
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "content": f"<p><em>Error processing text: {str(e)}</em></p>",
                "file_path": text.path if text else "Unknown",
                "references_available": False,
            },
            status_code=500,
        )


@router.get("/references/{urn}", response_model=None)
async def get_references(
    urn: str,
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
    html_output: bool = Query(True, description="Return HTML output for direct rendering"),
):
    """Get references for a text.

    Args:
        urn: The URN of the text
        xml_service: EnhancedXMLService instance
        html_output: Whether to return HTML or JSON

    Returns:
        HTML or JSON with references
    """
    try:
        # Parse URN
        EnhancedURN.from_string(urn)  # Validate URN format

        # Load XML document
        document = xml_service.load_document(urn)

        # Extract references
        references = xml_service.extract_references(document)

        if not html_output:
            # Return JSON response
            return JSONResponse(content={"urn": urn, "references": references, "count": len(references)})

        # Sort references naturally
        sorted_refs = sorted(references.keys(), key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])

        # Build reference tree HTML
        html = ['<ul class="space-y-1">']

        for ref in sorted_refs:
            html.append('<li class="hover:bg-gray-100 rounded">')
            html.append(f'<a href="/read/{urn}?reference={ref}" class="block px-2 py-1">')
            html.append(f'<span class="font-medium">{ref}</span>')
            html.append("</a>")
            html.append("</li>")

        html.append("</ul>")

        return HTMLResponse(content="".join(html))

    except Exception as e:
        if not html_output:
            return JSONResponse(content={"error": f"Error loading references: {str(e)}"}, status_code=500)
        return HTMLResponse(
            content=f'<div class="text-red-500">Error loading references: {str(e)}</div>', status_code=500
        )


@router.get("/document/{urn}", response_model=None)
async def get_document_info(
    urn: str,
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
):
    """Get document information.

    Args:
        urn: The URN of the document
        catalog_service: EnhancedCatalogService instance
        xml_service: EnhancedXMLService instance

    Returns:
        JSONResponse with document information
    """
    try:
        # Get text from catalog
        text = catalog_service.get_text_by_urn(urn)
        if not text:
            raise HTTPException(status_code=404, detail=f"Text not found: {urn}")

        # Load document
        document = xml_service.load_document(urn)

        # Extract metadata
        metadata = xml_service.extract_metadata(document)

        # Extract references
        references = xml_service.extract_references(document)

        # Get document statistics
        stats = xml_service.get_document_statistics(document)

        return JSONResponse(
            content={
                "urn": urn,
                "text": text.dict(),
                "metadata": metadata,
                "reference_count": len(references),
                "statistics": stats,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/passage/{urn}", response_model=None)
async def get_passage(
    urn: str,
    reference: str,
    format: str = Query("html", description="Output format: html, text, xml"),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
):
    """Get a specific passage from a document.

    Args:
        urn: The URN of the document
        reference: The reference to retrieve
        format: Output format (html, text, xml)
        xml_service: EnhancedXMLService instance

    Returns:
        Response with passage content in requested format
    """
    try:
        # Load document
        document = xml_service.load_document(urn)

        # Get passage by reference
        passage = xml_service.get_passage_by_reference(document, reference)

        if not passage:
            raise HTTPException(status_code=404, detail=f"Reference not found: {reference}")

        # Return in requested format
        if format == "html":
            html_content = xml_service.transform_element_to_html(passage)
            return HTMLResponse(content=html_content)
        elif format == "text":
            text_content = xml_service.extract_text_from_element(passage)
            return JSONResponse(content={"text": text_content, "reference": reference})
        elif format == "xml":
            xml_content = xml_service.serialize_element(passage)
            return JSONResponse(content={"xml": xml_content, "reference": reference})
        else:
            raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving passage: {str(e)}")
