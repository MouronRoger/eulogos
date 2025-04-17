"""Router for admin functionality."""

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.catalog_generator_service import CatalogGeneratorService

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

# Store the latest status for polling
_rebuild_status = {"in_progress": False, "message": "", "percentage": 0}


def get_catalog_generator_service() -> CatalogGeneratorService:
    """Get instance of catalog generator service.

    Returns:
        CatalogGeneratorService instance
    """
    return CatalogGeneratorService(data_dir="data", catalog_path="integrated_catalog.json")


@router.get("/catalog", response_class=HTMLResponse)
async def admin_catalog(request: Request):
    """Admin interface for catalog management."""
    return templates.TemplateResponse("admin/catalog.html", {"request": request})


@router.post("/rebuild-catalog")
async def rebuild_catalog(
    background_tasks: BackgroundTasks, service: CatalogGeneratorService = Depends(get_catalog_generator_service)
):
    """Rebuild the integrated catalog in the background."""
    global _rebuild_status

    # Skip if already in progress
    if _rebuild_status["in_progress"]:
        return {"status": "in_progress", "message": _rebuild_status["message"]}

    # Reset status
    _rebuild_status = {"in_progress": True, "message": "Starting catalog rebuild...", "percentage": 0}

    def progress_callback(percentage: int, message: str):
        """Update progress status."""
        global _rebuild_status
        _rebuild_status["percentage"] = percentage
        _rebuild_status["message"] = message

    async def run_catalog_generation():
        """Run the catalog generation and update status."""
        global _rebuild_status
        try:
            await service.generate_catalog_async(progress_callback=progress_callback)
            _rebuild_status = {"in_progress": False, "message": "Catalog rebuilt successfully!", "percentage": 100}
        except Exception as e:
            _rebuild_status = {"in_progress": False, "message": f"Error: {str(e)}", "percentage": 0, "error": True}

    # Add the task to be run in the background
    background_tasks.add_task(run_catalog_generation)

    return {"status": "started", "message": "Catalog rebuild started"}


@router.get("/rebuild-status")
async def rebuild_status():
    """Get the current status of the rebuild process."""
    return _rebuild_status
