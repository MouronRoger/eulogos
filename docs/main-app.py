"""Main FastAPI application module for Eulogos.

This module initializes the FastAPI application and sets up the
dependencies, routes, and services needed by the application.
"""

import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional

from app.services.catalog_service import CatalogService, get_catalog_service
from app.services.xml_service import XMLService
from app.config import Settings, get_settings

# Initialize FastAPI
app = FastAPI(
    title="Eulogos",
    description="Ancient Greek Text Repository",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Get settings
settings = get_settings()

# Initialize service dependencies
def get_xml_service(settings: Settings = Depends(get_settings)) -> XMLService:
    """Get XML service dependency."""
    return XMLService(data_dir=settings.data_dir)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Add some utility context processors for templates
@app.middleware("http")
async def add_template_context(request: Request, call_next):
    """Add common template context variables."""
    response = await call_next(request)
    
    # Only process HTML responses going to templates
    if isinstance(response, HTMLResponse) and hasattr(response, "context"):
        # Add current year for copyright
        import datetime
        response.context["current_year"] = datetime.datetime.now().year
        
    return response


@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Render home page."""
    # Redirect to browse page
    return templates.TemplateResponse(
        "browse.html", 
        {
            "request": request,
            "texts": catalog_service.get_all_texts(),
            "authors": catalog_service.get_all_authors(),
            "languages": catalog_service.get_all_languages(),
        }
    )


@app.get("/browse", response_class=HTMLResponse)
async def browse_texts(
    request: Request,
    author: Optional[str] = None,
    language: Optional[str] = None,
    query: Optional[str] = None,
    show_favorites: bool = False,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Browse texts with optional filtering."""
    # Determine which texts to show based on filters
    texts = []
    
    if show_favorites:
        texts = catalog_service.get_favorite_texts()
    elif author:
        texts = catalog_service.get_texts_by_author(author)
    elif language:
        texts = catalog_service.get_texts_by_language(language)
    elif query:
        texts = catalog_service.search_texts(query)
    else:
        texts = catalog_service.get_all_texts()
    
    # Render browse template
    return templates.TemplateResponse(
        "browse.html", 
        {
            "request": request,
            "texts": texts,
            "authors": catalog_service.get_all_authors(),
            "languages": catalog_service.get_all_languages(),
            "current_author": author,
            "current_language": language,
            "query": query,
            "show_favorites": show_favorites,
        }
    )


@app.get("/read/{path:path}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    path: str,
    reference: Optional[str] = None,
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLService = Depends(get_xml_service)
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


@app.get("/references/{path:path}", response_class=HTMLResponse)
async def get_references(
    request: Request,
    path: str,
    xml_service: XMLService = Depends(get_xml_service)
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


@app.post("/favorite/{path:path}")
async def toggle_favorite(
    path: str,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Toggle favorite status for a text."""
    success = catalog_service.toggle_favorite(path)
    if not success:
        raise HTTPException(status_code=404, detail=f"Text not found: {path}")
    
    # Get updated status
    text = catalog_service.get_text_by_path(path)
    return {"success": success, "favorite": text.favorite if text else False}


@app.post("/archive/{path:path}")
async def set_archived(
    path: str,
    archived: bool = True,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Set archived status for a text."""
    success = catalog_service.set_archived(path, archived)
    if not success:
        raise HTTPException(status_code=404, detail=f"Text not found: {path}")
    
    return {"success": success, "archived": archived}


@app.get("/search", response_class=HTMLResponse)
async def search_texts_htmx(
    request: Request,
    q: Optional[str] = None,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Search texts for HTMX partial template."""
    if not q:
        return templates.TemplateResponse(
            "partials/search_results.html",
            {"request": request, "texts": [], "query": ""}
        )
    
    texts = catalog_service.search_texts(q)
    
    return templates.TemplateResponse(
        "partials/search_results.html",
        {"request": request, "texts": texts, "query": q}
    )


@app.get("/api/catalog")
async def get_catalog(catalog_service: CatalogService = Depends(get_catalog_service)):
    """API endpoint to get the full catalog."""
    return catalog_service._catalog


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0",
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler."""
    return templates.TemplateResponse(
        "errors/404.html", {"request": request}, status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    """Custom 500 handler."""
    return templates.TemplateResponse(
        "errors/500.html", {"request": request, "error": str(exc.detail)}, status_code=500
    )
