"""Router for browsing texts with filtering options."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.catalog_service import CatalogService


# Dependency to get catalog service
def get_catalog_service():
    """Get instance of catalog service.

    Returns:
        CatalogService instance
    """
    service = CatalogService(catalog_path="integrated_catalog.json", data_dir="data")
    service.create_unified_catalog()
    return service


# Templates
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["browse"])


@router.get("/browse", response_class=HTMLResponse, response_model=None)
async def browse_texts(
    request: Request,
    show: str = Query("all", description="Filter by status: all, favorites, archived"),
    era: Optional[str] = Query(None, description="Filter by era: pre-socratic, hellenistic, imperial, late-antiquity"),
    search: Optional[str] = Query(None, description="Search term"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Browse texts with filtering options.

    Args:
        request: FastAPI request object
        show: Filter by status (all, favorites, archived)
        era: Filter by era
        search: Search term
        catalog_service: CatalogService instance

    Returns:
        HTMLResponse with rendered template
    """
    # Get all authors
    authors = catalog_service.get_all_authors(include_archived=(show == "archived"))

    # Apply era filter
    if era:
        # Map era to century ranges
        era_ranges = {
            "pre-socratic": (-7, -5),  # 7th to 5th century BCE
            "hellenistic": (-4, -1),  # 4th to 1st century BCE
            "imperial": (1, 3),  # 1st to 3rd century CE
            "late-antiquity": (4, 6),  # 4th to 6th century CE
        }

        if era in era_ranges:
            start_century, end_century = era_ranges[era]
            authors = [author for author in authors if start_century <= author.century <= end_century]

    # Process authors to include their works
    result_authors = []
    for author in authors:
        # Get works for this author
        works = catalog_service.get_texts_by_author(author.id, include_archived=(show == "archived"))

        # Filter by favorites if requested
        if show == "favorites":
            works = [work for work in works if work.favorite]
            # Skip author if no favorite works
            if not works:
                continue

        # Apply search filter if provided
        if search:
            works = [
                work
                for work in works
                if search.lower() in work.work_name.lower() or search.lower() in author.name.lower()
            ]
            # Skip author if no matching works
            if not works:
                continue

        # Add author with filtered works to results
        author_data = author.dict()
        author_data["works"] = [work.dict() for work in works]
        result_authors.append(author_data)

    # Sort authors by name
    result_authors.sort(key=lambda a: a["name"])

    # Render the template
    return templates.TemplateResponse(
        "partials/author_works_tree.html",
        {"request": request, "authors": result_authors, "show": show, "era": era, "search": search},
    )
