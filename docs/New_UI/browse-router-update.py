"""Browse router for Eulogos application.

This module provides routes for browsing texts with hierarchical organization by author
and filtering by various criteria.
"""

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.config import get_settings
from app.services.catalog_service import CatalogService, get_catalog_service

# Get settings
settings = get_settings()

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
    # Get hierarchical view data
    hierarchical_texts = catalog_service.get_hierarchical_texts()
    
    return templates.TemplateResponse(
        "browse.html", 
        {
            "request": request,
            "hierarchical_texts": hierarchical_texts,
            "texts": [],  # Not used in hierarchical view
            "authors": catalog_service.get_all_authors(),
            "languages": catalog_service.get_all_languages(),
            "eras": catalog_service.get_all_eras(),
            "centuries": catalog_service.get_all_centuries(),
            "author_types": catalog_service.get_all_author_types(),
        }
    )


@router.get("/browse", response_class=HTMLResponse)
async def browse_texts(
    request: Request,
    author: Optional[str] = None,
    language: Optional[str] = None,
    era: Optional[str] = None,
    century: Optional[str] = None,
    author_type: Optional[str] = None,
    query: Optional[str] = None,
    author_query: Optional[str] = None,
    show_favorites: bool = False,
    show_archived: bool = False,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Browse texts with optional filtering."""
    # Determine which texts to show based on filters
    texts = []
    hierarchical_texts = {}
    
    if author:
        # Single author view (flat list)
        texts = catalog_service.get_texts_by_author(author, include_archived=show_archived)
    elif language:
        # Single language view (flat list)
        texts = catalog_service.get_texts_by_language(language, include_archived=show_archived)
    else:
        # Hierarchical view with filtering
        hierarchical_texts = catalog_service.get_filtered_hierarchical_texts(
            era=era,
            century=century,
            author_type=author_type,
            query=query,
            author_query=author_query,
            show_favorites=show_favorites,
            include_archived=show_archived
        )
    
    # Render browse template
    return templates.TemplateResponse(
        "browse.html", 
        {
            "request": request,
            "texts": texts,
            "hierarchical_texts": hierarchical_texts,
            "authors": catalog_service.get_all_authors(),
            "languages": catalog_service.get_all_languages(),
            "eras": catalog_service.get_all_eras(),
            "centuries": catalog_service.get_all_centuries(),
            "author_types": catalog_service.get_all_author_types(),
            "current_author": author,
            "current_language": language,
            "current_era": era,
            "current_century": century,
            "current_author_type": author_type,
            "query": query,
            "author_query": author_query,
            "show_favorites": show_favorites,
            "show_archived": show_archived,
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
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Archive a text."""
    success = catalog_service.set_archived(path, True)
    if not success:
        return {"success": False, "message": f"Text not found: {path}"}
    
    return {"success": True, "archived": True}


@router.post("/unarchive/{path:path}")
async def unset_archived(
    path: str,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Unarchive a text."""
    success = catalog_service.set_archived(path, False)
    if not success:
        return {"success": False, "message": f"Text not found: {path}"}
    
    return {"success": True, "archived": False}


@router.get("/authors", response_class=HTMLResponse)
async def author_list_htmx(
    request: Request,
    q: Optional[str] = Query(None, description="Author search query"),
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Get author list for HTMX partial template."""
    if q:
        authors = catalog_service.search_authors(q)
    else:
        authors = catalog_service.get_all_authors()
    
    return templates.TemplateResponse(
        "partials/author_list.html",
        {"request": request, "authors": authors, "query": q}
    )
