"""Router for text reading operations."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.urn import URN
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService


# Dependency to get catalog service
def get_catalog_service():
    """Get instance of catalog service.

    Returns:
        CatalogService instance
    """
    service = CatalogService(catalog_path="integrated_catalog.json", data_dir="data")
    service.create_unified_catalog()
    return service


# Dependency to get XML processor service with catalog service
def get_xml_processor(catalog_service: CatalogService = Depends(get_catalog_service)):
    """Get instance of XML processor service.

    Args:
        catalog_service: CatalogService instance to use for path resolution

    Returns:
        XMLProcessorService instance
    """
    return XMLProcessorService(data_path="data", catalog_service=catalog_service)


# Templates
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["reader"])


@router.get("/read/{urn}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    urn: str,
    reference: Optional[str] = None,
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_processor: XMLProcessorService = Depends(get_xml_processor),
):
    """Read a text with optional reference navigation.

    Args:
        request: FastAPI request object
        urn: The URN of the text to read
        reference: Optional reference to navigate to
        catalog_service: CatalogService instance
        xml_processor: XMLProcessorService instance

    Returns:
        HTMLResponse with rendered template

    Raises:
        HTTPException: If text is not found
    """
    # Parse URN
    try:
        urn_obj = URN(value=urn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URN: {e}")

    # Get text from catalog
    text = catalog_service.get_text_by_urn(urn)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {urn}")

    try:
        # Simple direct path generation for debugging
        parts = urn.split(":")
        if len(parts) >= 4:
            identifier = parts[3].split("#")[0]
            id_parts = identifier.split(".")
            if len(id_parts) >= 3:
                textgroup = id_parts[0]
                work = id_parts[1]
                version = id_parts[2]
                direct_path = f"data/{textgroup}/{work}/{textgroup}.{work}.{version}.xml"
        else:
            direct_path = "Unknown path format"

        # Load XML content
        xml_root = xml_processor.load_xml(urn_obj)

        # Get adjacent references
        adjacent_refs = xml_processor.get_adjacent_references(xml_root, reference)

        # Transform to HTML with reference highlighting
        html_content = xml_processor.transform_to_html(xml_root, reference)

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
                "file_path": direct_path,  # Add file path for debugging
            },
        )
    except Exception as e:
        # Return error message with direct path for debugging
        direct_path = "Unknown"
        # Simple direct path generation for debugging
        try:
            parts = urn.split(":")
            if len(parts) >= 4:
                identifier = parts[3].split("#")[0]
                id_parts = identifier.split(".")
                if len(id_parts) >= 3:
                    textgroup = id_parts[0]
                    work = id_parts[1]
                    version = id_parts[2]
                    direct_path = f"data/{textgroup}/{work}/{textgroup}.{work}.{version}.xml"
        except Exception:
            pass

        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "content": f"<p><em>Error processing text: {str(e)}</em></p>",
                "file_path": direct_path,  # Add direct file path for debugging
                "urn": urn,
            },
            status_code=500,
        )


@router.get("/api/references/{urn}", response_model=None)
async def get_references(urn: str, xml_processor: XMLProcessorService = Depends(get_xml_processor)):
    """Get references for a text.

    Args:
        urn: The URN of the text
        xml_processor: XMLProcessorService instance

    Returns:
        HTML with references
    """
    try:
        # Parse URN
        urn_obj = URN(value=urn)

        # Load XML content
        xml_root = xml_processor.load_xml(urn_obj)

        # Extract references
        references = xml_processor.extract_references(xml_root)

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
        return HTMLResponse(
            content=f'<div class="text-red-500">Error loading references: {str(e)}</div>', status_code=500
        )
