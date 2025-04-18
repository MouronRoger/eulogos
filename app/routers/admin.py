"""Router for admin functionality."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/catalog", response_class=HTMLResponse)
async def admin_catalog(request: Request):
    """Admin interface for catalog management."""
    return templates.TemplateResponse("admin/catalog.html", {"request": request})


@router.get("/rebuild-status")
async def rebuild_status():
    """Get the status of catalog building.

    This is a simplified version that just reports that catalog generation
    is a manual process using canonical_catalog_builder.py.
    """
    return {
        "status": "manual",
        "message": "Catalog generation is a manual process using canonical_catalog_builder.py",
        "in_progress": False,
        "percentage": 100,
    }
