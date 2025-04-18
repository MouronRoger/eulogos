"""Router for text reading operations (v2 API).

This module provides enhanced endpoints for text reading functionality including:
- Text display with reference-based navigation
- Hierarchical reference extraction and browsing
- XML to HTML transformation with enhanced styling options
- Metadata exposure with rich context
- Token-level text processing
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from app.dependencies import get_simple_catalog_service
from app.models.simple_urn import SimpleURN
from app.services.simple_catalog_service import SimpleCatalogService

# Configure logging
log = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="app/templates")

# Create router
router = APIRouter(
    prefix="/api/v2",
    tags=["reader"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{urn}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    urn: str = Path(..., description="The URN of the text to read"),
    ref: Optional[str] = Query(None, description="Text reference (e.g., '1.1' for Book 1, Chapter 1)"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Render the reader view for a text.

    Args:
        request: FastAPI request object
        urn: URN of the text to read
        ref: Optional text reference
        catalog_service: Catalog service for text lookups

    Returns:
        HTMLResponse with the reader view
    """
    try:
        # Validate URN format
        SimpleURN.from_string(urn)  # Validate URN format
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URN format: {str(e)}")

    # Get text metadata
    text = catalog_service.get_text_by_urn(urn)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {urn}")

    # Get file path
    try:
        file_path = catalog_service.resolve_urn_to_path(urn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving text path: {str(e)}")

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Text file not found: {file_path}")

    # Get author if available
    author = None
    if text.author_id:
        author = catalog_service.get_author_by_id(text.author_id)

    # Render template
    return templates.TemplateResponse(
        "reader.html",
        {
            "request": request,
            "urn": urn,
            "text": text,
            "author": author,
            "reference": ref,
            "file_path": str(file_path),
        },
    )


@router.get("/text/{urn}/content", response_class=HTMLResponse)
async def get_text_content(
    urn: str = Path(..., description="The URN of the text"),
    ref: Optional[str] = Query(None, description="Text reference"),
    format: str = Query("html", description="Output format (html, text, xml)"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get the content of a text.

    Args:
        urn: URN of the text
        ref: Optional text reference
        format: Output format
        catalog_service: Catalog service for text lookups

    Returns:
        Response with text content
    """
    try:
        # Validate URN format
        SimpleURN.from_string(urn)  # Validate URN format
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URN format: {str(e)}")

    # Get file path
    try:
        file_path = catalog_service.resolve_urn_to_path(urn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving text path: {str(e)}")

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Text file not found: {file_path}")

    # Read the XML file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading text file: {str(e)}")

    # Process content based on format
    if format == "xml":
        return Response(content=content, media_type="application/xml")
    elif format == "text":
        # Simple XML to text conversion (placeholder)
        # In a real implementation, you would use a proper XML parser
        import re

        text_content = re.sub(r"<[^>]+>", "", content)
        return Response(content=text_content, media_type="text/plain")
    else:  # HTML format
        # Simple XML to HTML conversion (placeholder)
        # In a real implementation, you would use XSLT or a proper XML parser
        html_content = f"""
        <div class="text-content">
            <pre>{content}</pre>
        </div>
        """
        return HTMLResponse(content=html_content)


@router.get("/text/{urn}/metadata")
async def get_text_metadata(
    urn: str = Path(..., description="The URN of the text"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get metadata for a text.

    Args:
        urn: URN of the text
        catalog_service: Catalog service for text lookups

    Returns:
        Dictionary with text metadata
    """
    # Get text metadata
    text = catalog_service.get_text_by_urn(urn)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {urn}")

    # Get author if available
    author = None
    if text.author_id:
        author = catalog_service.get_author_by_id(text.author_id)

    # Get file path
    try:
        file_path = catalog_service.resolve_urn_to_path(urn)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving text path: {str(e)}")

    return {
        "urn": urn,
        "text": text.model_dump(),
        "author": author.model_dump() if author else None,
        "file_path": str(file_path),
        "file_exists": file_path.exists(),
    }


@router.get("/references/{urn}", response_model=None)
async def get_references(
    urn: str,
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
    html_output: bool = Query(True, description="Return HTML output for direct rendering"),
):
    """Get references for a text.

    Args:
        urn: The URN of the text
        catalog_service: SimpleCatalogService instance
        html_output: Whether to return HTML or JSON

    Returns:
        HTML or JSON with references
    """
    try:
        # Validate URN format
        SimpleURN.from_string(urn)

        # Get file path
        file_path = catalog_service.resolve_urn_to_path(urn)

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Text file not found: {file_path}")

        # For now, return a simplified response
        # In a real implementation, you would parse the XML and extract references

        # Placeholder references
        references = {
            "1": "Book 1",
            "1.1": "Book 1, Chapter 1",
            "1.2": "Book 1, Chapter 2",
            "2": "Book 2",
            "2.1": "Book 2, Chapter 1",
        }

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
        error_msg = f"Error loading references: {str(e)}"

        if not html_output:
            return JSONResponse(content={"error": error_msg}, status_code=500)
        return HTMLResponse(content=f'<div class="text-red-500"><p>{error_msg}</p></div>', status_code=500)


@router.get("/document/{urn}", response_model=None)
async def get_document_info(
    urn: str,
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get document information.

    Args:
        urn: The URN of the document
        catalog_service: SimpleCatalogService instance

    Returns:
        JSONResponse with document information
    """
    try:
        # Get text from catalog
        text = catalog_service.get_text_by_urn(urn)
        if not text:
            raise HTTPException(status_code=404, detail=f"Text not found: {urn}")

        # Get file path
        file_path = catalog_service.resolve_urn_to_path(urn)

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Text file not found: {file_path}")

        # Simplified placeholder metadata
        metadata = {
            "title": text.work_name,
            "author": text.group_name,
            "language": text.language,
            "wordcount": text.wordcount,
        }

        # Simplified placeholder stats
        stats = {
            "wordCount": text.wordcount,
            "characterCount": text.wordcount * 5,  # Rough estimate
            "paragraphCount": text.wordcount // 100,  # Rough estimate
        }

        return JSONResponse(
            content={
                "urn": urn,
                "text": text.model_dump(),
                "metadata": metadata,
                "reference_count": 5,  # Placeholder
                "statistics": stats,
                "file_path": str(file_path),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/passage/{urn}", response_model=None)
async def get_passage(
    urn: str,
    reference: str,
    format: str = Query("html", description="Output format: html, text, xml"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get a specific passage from a document.

    Args:
        urn: The URN of the document
        reference: The reference to retrieve
        format: Output format (html, text, xml)
        catalog_service: SimpleCatalogService instance

    Returns:
        Response with passage content in requested format
    """
    try:
        # Validate URN
        SimpleURN.from_string(urn)

        # Get file path
        file_path = catalog_service.resolve_urn_to_path(urn)

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Text file not found: {file_path}")

        # For now, return a simplified placeholder response
        # In a real implementation, you would parse the XML and extract the specific passage

        # Placeholder passage content
        passage_text = f"Sample passage content for reference {reference} from document {urn}"

        # Return in requested format
        if format == "html":
            html_content = f"<div><p>{passage_text}</p></div>"
            return HTMLResponse(content=html_content)
        elif format == "text":
            return JSONResponse(content={"text": passage_text, "reference": reference})
        elif format == "xml":
            xml_content = f"<passage ref='{reference}'>{passage_text}</passage>"
            return JSONResponse(content={"xml": xml_content, "reference": reference})
        else:
            raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving passage: {str(e)}")
