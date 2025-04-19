"""Main FastAPI application module for Eulogos."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.routers import reader

# Set up the application
app = FastAPI(
    title="Eulogos API",
    description="API for exploring and managing ancient Greek texts from the First 1000 Years Project",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Include routers
app.include_router(reader.router)

# Set up static files and templates
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Configure logging
logger.add("logs/eulogos.log", rotation="10 MB", level="INFO")

# Path to catalog file - using absolute path
CATALOG_PATH = Path("/Users/james/Documents/GitHub/eulogos/integrated_catalog.json")
DATA_DIR = Path("/Users/james/Documents/GitHub/eulogos/data")


def load_catalog():
    """Load the catalog data from the integrated_catalog.json file."""
    if not CATALOG_PATH.exists():
        logger.error(f"Catalog file not found: {CATALOG_PATH}")
        return {}

    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)
            logger.info(f"Loaded catalog from {CATALOG_PATH}")
            return catalog_data
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        return {}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the browse page."""
    # Pre-load catalog data
    catalog = load_catalog()

    # Process catalog to get a list of authors with works
    authors = []
    for author_id, author_data in catalog.items():
        works_data = author_data.get("works", {})
        works = []

        for work_id, work_data in works_data.items():
            work = {"id": work_id, "title": work_data.get("title", ""), "editions": [], "translations": []}

            for edition_id, edition_data in work_data.get("editions", {}).items():
                work["editions"].append(
                    {
                        "id": edition_id,
                        "label": edition_data.get("label", ""),
                        "language": edition_data.get("language", ""),
                        "path": edition_data.get("path", ""),
                    }
                )

            for translation_id, translation_data in work_data.get("translations", {}).items():
                work["translations"].append(
                    {
                        "id": translation_id,
                        "label": translation_data.get("label", ""),
                        "language": translation_data.get("language", ""),
                        "path": translation_data.get("path", ""),
                    }
                )

            if work["editions"] or work["translations"]:
                works.append(work)

        if works:
            authors.append(
                {
                    "id": author_id,
                    "name": author_data.get("name", ""),
                    "century": author_data.get("century", ""),
                    "type": author_data.get("type", ""),
                    "works": works,
                }
            )

    # Sort authors by name
    authors.sort(key=lambda x: x["name"])

    return templates.TemplateResponse(
        "browse.html",
        {
            "request": request,
            "authors": authors,
            "author_count": len(authors),
            "current_year": datetime.now().year,
        },
    )


@app.get("/health")
async def health_check():
    """Return health check information."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/catalog")
async def get_catalog():
    """Get the full catalog data."""
    catalog = load_catalog()
    return JSONResponse(content=catalog)


@app.get("/api/authors")
async def get_authors():
    """Get all authors."""
    catalog = load_catalog()
    authors = []

    for author_id, author_data in catalog.items():
        authors.append(
            {
                "id": author_id,
                "name": author_data.get("name"),
                "century": author_data.get("century"),
                "type": author_data.get("type"),
            }
        )

    return JSONResponse(content={"authors": authors})


@app.get("/api/authors/{author_id}")
async def get_author(author_id: str):
    """Get a specific author by ID."""
    catalog = load_catalog()

    if author_id not in catalog:
        return JSONResponse(content={"error": "Author not found"}, status_code=404)

    return JSONResponse(content=catalog[author_id])


@app.get("/api/works/{author_id}/{work_id}")
async def get_work(author_id: str, work_id: str):
    """Get a specific work by author ID and work ID."""
    catalog = load_catalog()

    if author_id not in catalog:
        return JSONResponse(content={"error": "Author not found"}, status_code=404)

    works = catalog[author_id].get("works", {})
    if work_id not in works:
        return JSONResponse(content={"error": "Work not found"}, status_code=404)

    return JSONResponse(content=works[work_id])


@app.get("/data/{path:path}")
async def get_file_by_path(path: str):
    """Get a file directly using its path from the catalog.

    This is the canonical method for accessing XML files,
    using paths exactly as they appear in the integrated_catalog.json.
    The integrated_catalog.json is the single source of truth for all paths.
    """
    # Build the full path by joining the data directory with the path
    full_path = DATA_DIR / path

    # Check if the file exists
    if not full_path.exists():
        logger.error(f"File not found: {full_path}")
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    # Determine the media type based on file extension
    if path.endswith(".xml"):
        media_type = "application/xml"
    elif path.endswith(".json"):
        media_type = "application/json"
    elif path.endswith(".txt"):
        media_type = "text/plain"
    else:
        media_type = "application/octet-stream"

    # Return the file content
    return FileResponse(full_path, media_type=media_type)


@app.get("/api/paths")
async def get_all_paths():
    """Get all file paths from the catalog."""
    catalog = load_catalog()
    paths = []

    for author_id, author_data in catalog.items():
        works = author_data.get("works", {})

        for work_id, work_data in works.items():
            editions = work_data.get("editions", {})

            for edition_id, edition_data in editions.items():
                path = edition_data.get("path")
                if path:
                    paths.append(
                        {
                            "author_id": author_id,
                            "work_id": work_id,
                            "edition_id": edition_id,
                            "path": path,
                            "full_path": str(DATA_DIR / path),
                        }
                    )

            translations = work_data.get("translations", {})
            for translation_id, translation_data in translations.items():
                path = translation_data.get("path")
                if path:
                    paths.append(
                        {
                            "author_id": author_id,
                            "work_id": work_id,
                            "translation_id": translation_id,
                            "path": path,
                            "full_path": str(DATA_DIR / path),
                        }
                    )

    return JSONResponse(content={"paths": paths, "count": len(paths)})


@app.get("/api/debug/file/{path:path}")
async def debug_file(path: str):
    """Debug endpoint to check a specific file path.

    This uses the same path format as the canonical file access method.
    """
    # Build the full path by joining the data directory with the path
    full_path = DATA_DIR / path

    return JSONResponse(
        content={
            "path": path,
            "full_path": str(full_path),
            "exists": full_path.exists(),
            "is_file": full_path.is_file() if full_path.exists() else None,
            "size": full_path.stat().st_size if full_path.exists() else None,
        }
    )


@app.get("/api/v2/search")
async def search_texts(request: Request, q: str = ""):
    """Search for texts and authors in the catalog."""
    catalog = load_catalog()
    results = []

    # Convert query to lowercase for case-insensitive search
    query = q.lower()

    for author_id, author_data in catalog.items():
        author_name = author_data.get("name", "").lower()
        author_matches = query in author_name

        # Process works
        matching_works = []
        for work_id, work_data in author_data.get("works", {}).items():
            work_title = work_data.get("title", "").lower()
            work_matches = query in work_title

            if work_matches or author_matches:
                # Add matching editions
                for edition_id, edition_data in work_data.get("editions", {}).items():
                    matching_works.append({
                        "id": f"{author_id}.{work_id}.{edition_id}",
                        "title": edition_data.get("label", work_data.get("title", "")),
                        "type": "edition",
                        "language": edition_data.get("language", ""),
                        "path": edition_data.get("path", ""),
                        "author": author_data.get("name", "")
                    })

                # Add matching translations
                for trans_id, trans_data in work_data.get("translations", {}).items():
                    matching_works.append({
                        "id": f"{author_id}.{work_id}.{trans_id}",
                        "title": trans_data.get("label", work_data.get("title", "")),
                        "type": "translation",
                        "language": trans_data.get("language", ""),
                        "path": trans_data.get("path", ""),
                        "author": author_data.get("name", "")
                    })

        if matching_works:
            results.extend(matching_works)

    # Return partial template for HTMX
    if "HX-Request" in request.headers:
        return templates.TemplateResponse(
            "partials/search_results.html",
            {
                "request": request,
                "results": results[:10],  # Limit to top 10 results
                "query": q
            }
        )

    # Return JSON for API requests
    return JSONResponse(content={"results": results})


# Non-prefixed search endpoint for compatibility
@app.get("/search")
async def search_texts_no_prefix(request: Request, q: str = ""):
    """Non-prefixed search endpoint."""
    return await search_texts(request, q)


@app.get("/read/id/{text_id}", response_class=HTMLResponse)
async def read_by_id(
    request: Request,
    text_id: str,
    reference: Optional[str] = None
):
    """Read a text by its ID.
    
    This endpoint handles /read/id/{text_id} URLs from browse pages.
    The template links to /read/id/{edition.id} - reroute to API endpoint.
    """
    try:
        # Get query parameters
        reference = request.query_params.get("reference")

        # Create dependencies
        from app.dependencies import get_catalog_service, get_xml_service
        catalog_service = get_catalog_service()
        xml_service = get_xml_service()
        
        # Look up the text in the catalog
        text = catalog_service.get_text_by_id(text_id)
        if not text:
            raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

        # Continue with standard processing
        # Get the actual content path
        if not text.path:
            raise HTTPException(status_code=404, detail=f"No path found for text: {text_id}")

        # Load and process the document
        xml_root = xml_service.load_document(text_id)
        
        # Get the HTML content and transform it
        html_content = xml_service.transform_to_html(text_id, reference)
        
        # Get adjacent references for navigation if a reference is provided
        adjacent_refs = xml_service.get_adjacent_references(xml_root, reference) if reference else {"prev": None, "next": None}

        # Get author if available
        author = None
        if text.author_id:
            author = catalog_service.get_author_by_id(text.author_id)

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
                "path": text.path
            },
        )
    except Exception as e:
        logger.exception(f"Error processing text ID {text_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")


@app.get("/read/{path:path}", response_class=HTMLResponse)
async def read_formatted_text(request: Request, path: str):
    """Read and format XML text for display in a readable format.
    
    Uses the same path parameter as /data/{path} to maintain a single
    canonical reference to the data.
    
    Args:
        request: The FastAPI request object
        path: Path to the XML file from the catalog
    
    Returns:
        HTMLResponse: Formatted text in an HTML template for reading
    """
    # Build the full path by joining the data directory with the path
    full_path = DATA_DIR / path
    
    # Check if the file exists
    if not full_path.exists():
        logger.error(f"File not found: {full_path}")
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    
    try:
        # Get reference from query params if present
        reference = request.query_params.get("reference")
        
        # Find the text in the catalog to get metadata
        catalog = load_catalog()
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
        
        # Create XML processor
        from app.services.xml_processor_service import XMLProcessorService
        from app.services.catalog_service import CatalogService
        
        # Create services
        catalog_service = CatalogService(catalog_path=str(CATALOG_PATH), data_dir=str(DATA_DIR))
        catalog_service.create_unified_catalog()
        xml_processor = XMLProcessorService(catalog_service=catalog_service, data_path=str(DATA_DIR))
        
        # Load the XML content
        xml_root = xml_processor.load_xml_from_path(path)

        # Check if xml_root is None
        if xml_root is None:
            logger.error(f"Failed to load XML content from {path}")
            return templates.TemplateResponse(
                "reader.html",
                {
                    "request": request,
                    "text": text_metadata if text_metadata else {"path": path},
                    "content": f"<div class='error'>Error: XML document could not be parsed</div>",
                    "path": path,
                    "title": "Error",
                },
                status_code=500,
            )
        
        # Handle reference-based display if specified
        if reference:
            # Get passage by reference
            passage = xml_processor.get_passage_by_reference(xml_root, reference)
            if passage:
                html_content = xml_processor._process_element_to_html(passage, reference)
                adjacent_refs = xml_processor.get_adjacent_references(xml_root, reference)
            else:
                html_content = f"<p>Reference '{reference}' not found.</p>"
                adjacent_refs = {"prev": None, "next": None}
                
            return templates.TemplateResponse(
                "reader.html",
                {
                    "request": request,
                    "text": text_metadata,
                    "content": html_content,
                    "path": path,
                    "title": text_metadata.get("label") if text_metadata else path,
                    "current_ref": reference,
                    "prev_ref": adjacent_refs["prev"],
                    "next_ref": adjacent_refs["next"],
                },
            )
        
        # Format the XML for display
        try:
            html_content = xml_processor._transform_element_to_html(xml_root)
        except (TypeError, AttributeError) as e:
            logger.error(f"Error transforming XML: {e}")
            html_content = f"<div class='error'>Error: Could not transform XML. {str(e)}</div>"
        
        # Render the reader template
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text_metadata,
                "content": html_content,
                "path": path,
                "title": text_metadata.get("label") if text_metadata else path,
            },
        )
        
    except Exception as e:
        logger.error(f"Error processing XML: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text_metadata if text_metadata else {"path": path},
                "content": f"<div class='error'>Error loading text: {str(e)}</div>",
                "path": path,
                "title": "Error",
            },
            status_code=500,
        )


# Non-prefixed browse endpoint for compatibility
@app.get("/browse")
async def browse_texts_no_prefix(request: Request):
    """Non-prefixed browse endpoint."""
    from app.routers.browse import browse_texts
    show = request.query_params.get("show", "all")
    era = request.query_params.get("era", None)
    search = request.query_params.get("search", None)
    
    from app.dependencies import get_catalog_service
    catalog_service = get_catalog_service()
    
    return await browse_texts(
        request=request, 
        show=show,
        era=era,
        search=search,
        catalog_service=catalog_service
    )
