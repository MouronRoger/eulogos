"""Router for text reading operations."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.catalog_service import CatalogService
from app.services.xml_processor import XMLProcessorService


# Dependency to get catalog service
def get_catalog_service():
    """Get instance of catalog service.

    Returns:
        CatalogService instance
    """
    service = CatalogService(catalog_path="integrated_catalog.json", data_dir="data")
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


@router.get("/data/{path:path}", response_class=HTMLResponse)
async def read_text(request: Request, path: str):
    """
    Read and format XML text for display.
    
    Args:
        request: The FastAPI request object
        path: Path to the XML file
    
    Returns:
        HTMLResponse: Formatted text for display
    """
    try:
        xml_processor = XMLProcessorService()
        xml_content = xml_processor.load_xml_from_path(path)
        
        # Get reference from query params if present
        reference = request.query_params.get("reference")
        
        # Find the text in the catalog to get metadata
        catalog_service = get_catalog_service()
        catalog = catalog_service.get_catalog()
        text_metadata = None
        
        # Look through the catalog to find this path
        for author_id, author_data in catalog.items():
            author_name = author_data.get("name", "")
            
            for work_id, work_data in author_data.get("works", {}).items():
                work_title = work_data.get("title", "")
                
                # Check editions
                for edition_id, edition_data in work_data.get("editions", {}).items():
                    if edition_data.get("path") == path:
                        text_metadata = {
                            "id": edition_id,
                            "work_id": work_id,
                            "work_name": work_title,
                            "group_name": author_name,
                            "language": edition_data.get("language", ""),
                            "label": edition_data.get("label", ""),
                            "wordcount": edition_data.get("word_count"),
                            "path": path,
                            "archived": edition_data.get("archived", False),
                            "favorite": edition_data.get("favorite", False),
                        }
                        break
                
                # Check translations
                if not text_metadata:
                    for trans_id, trans_data in work_data.get("translations", {}).items():
                        if trans_data.get("path") == path:
                            text_metadata = {
                                "id": trans_id,
                                "work_id": work_id,
                                "work_name": work_title,
                                "group_name": author_name,
                                "language": trans_data.get("language", ""),
                                "label": trans_data.get("label", ""),
                                "wordcount": trans_data.get("word_count"),
                                "path": path,
                                "archived": trans_data.get("archived", False),
                                "favorite": trans_data.get("favorite", False),
                            }
                            break
        
        if reference:
            # Handle reference display
            references = xml_processor.get_references(xml_content)
            return templates.TemplateResponse(
                "reader.html",
                {
                    "request": request,
                    "text": text_metadata,
                    "content": references,
                    "path": path,
                    "title": text_metadata.get("label") if text_metadata else path,
                    "current_ref": reference,
                },
            )
        
        # Format XML for display
        formatted_text = xml_processor.format_xml_for_display(xml_content)
        
        # Render the reader template
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text_metadata,
                "content": formatted_text,
                "path": path,
                "title": text_metadata.get("label") if text_metadata else path,
            },
        )
        
    except Exception as e:
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": {"path": path},
                "content": f"<div class='error'>Error loading text: {str(e)}</div>",
                "path": path,
                "title": "Error",
            },
            status_code=500,
        )


@router.get("/api/references/{path:path}", response_model=None)
async def get_references(path: str, xml_processor: XMLProcessorService = Depends(get_xml_processor)):
    """Get references for a text.

    Args:
        path: The path to the text file from the catalog
        xml_processor: XMLProcessorService instance

    Returns:
        HTML with references
    """
    try:
        # Load XML content directly from path
        xml_root = xml_processor.load_xml_from_path(path)

        # Extract references
        references = xml_processor.extract_references(xml_root)

        # Sort references naturally
        sorted_refs = sorted(references.keys(), key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])

        # Build reference tree HTML
        html = ['<ul class="space-y-1">']

        for ref in sorted_refs:
            html.append('<li class="hover:bg-gray-100 rounded">')
            html.append(f'<a href="/data/{path}?reference={ref}" class="block px-2 py-1">')
            html.append(f'<span class="font-medium">{ref}</span>')
            html.append("</a>")
            html.append("</li>")

        html.append("</ul>")

        return HTMLResponse(content="".join(html))

    except Exception as e:
        return HTMLResponse(
            content=f'<div class="text-red-500">Error loading references: {str(e)}</div>', status_code=500
        )
