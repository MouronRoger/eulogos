"""Browse router for Eulogos application.

This module provides routes for browsing texts, filtering by author/language,
and searching.
"""

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.services.catalog_service import CatalogService, get_catalog_service

# Initialize router
router = APIRouter(
    prefix="",
    tags=["browse"],
)

# Templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Render home page (redirects to browse)."""
    return templates.TemplateResponse(
        "browse.html", 
        {
            "request": request,
            "texts": catalog_service.get_all_texts(),
            "authors": catalog_service.get_all_authors(),
            "languages": catalog_service.get_all_languages(),
        }
    )


@router.get("/browse", response_class=HTMLResponse)
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


@router.get("/search", response_class=HTMLResponse)
async def search_texts_htmx(
    request: Request,
    q: Optional[str] = Query(None, description="Search query"),
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


@router.post("/favorite/{path:path}")
async def toggle_favorite(
    path: str,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Toggle favorite status for a text."""
    success = catalog_service.toggle_favorite(path)
    if not success:
        return {"success": False, "message": f"Text not found: {path}"}
    
    # Get updated status
    text = catalog_service.get_text_by_path(path)
    return {"success": True, "favorite": text.favorite if text else False}


@router.post("/archive/{path:path}")
async def set_archived(
    path: str,
    archived: bool = True,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Set archived status for a text."""
    success = catalog_service.set_archived(path, archived)
    if not success:
        return {"success": False, "message": f"Text not found: {path}"}
    
    return {"success": True, "archived": archived} 