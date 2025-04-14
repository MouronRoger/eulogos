"""Admin router for the Eulogos admin interface."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Form, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

from app.services.catalog_generation_service import CatalogGenerationService
from app.services.task_service import TaskService

# Create instances of services
catalog_generation_service = CatalogGenerationService()
task_service = TaskService()

# Configure templates
templates = Jinja2Templates(directory="app/templates")

# Create router
router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard page.
    
    Args:
        request: The request object
        
    Returns:
        HTML response with the admin dashboard
    """
    # Get catalog statistics
    catalog_stats = await catalog_generation_service.get_catalog_statistics()
    stats = catalog_stats.get("statistics", {})
    
    return templates.TemplateResponse(
        "admin/dashboard.html", 
        {"request": request, "stats": stats}
    )


@router.post("/catalog/generate", response_model=Dict[str, Any])
async def generate_catalog(
    background_tasks: BackgroundTasks,
    data_dir: str = Form("data"),
    author_index: str = Form("author_index.json"),
    output_file: str = Form("integrated_catalog.json"),
    include_content_sample: bool = Form(False),
    stats_only: bool = Form(False)
):
    """Generate the integrated catalog in the background.
    
    Args:
        background_tasks: FastAPI background tasks
        data_dir: Path to the data directory
        author_index: Path to the author index
        output_file: Path for the output file
        include_content_sample: Whether to include content samples
        stats_only: Whether to generate only statistics
        
    Returns:
        Task information
    """
    # Create service with provided paths
    service = CatalogGenerationService(
        data_dir=data_dir,
        author_path=author_index,
        output_path=output_file,
        task_service=task_service
    )
    
    # Create task
    task_id = await service.create_catalog_generation_task(
        include_content_sample=include_content_sample,
        stats_only=stats_only
    )
    
    return {
        "message": "Catalog generation started",
        "task_id": task_id
    }


@router.get("/catalog/statistics", response_model=Dict[str, Any])
async def get_catalog_statistics(
    catalog_file: str = Query("integrated_catalog.json", description="Path to the catalog file")
):
    """Get statistics about the current catalog.
    
    Args:
        catalog_file: Path to the catalog file
        
    Returns:
        Catalog statistics
    """
    service = CatalogGenerationService(output_path=catalog_file)
    return await service.get_catalog_statistics()


@router.get("/catalog/download")
async def download_catalog(
    catalog_file: str = Query("integrated_catalog.json", description="Path to the catalog file")
):
    """Download the catalog file.
    
    Args:
        catalog_file: Path to the catalog file
        
    Returns:
        The catalog file for download
    """
    return FileResponse(
        path=catalog_file,
        filename="integrated_catalog.json",
        media_type="application/json"
    )


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(task_id: str):
    """Get information about a specific task.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Task information
    """
    task_data = await task_service.get_task(task_id)
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_data


@router.get("/tasks", response_model=List[Dict[str, Any]])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of tasks to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """List tasks with optional filtering.
    
    Args:
        status: Optional status filter
        limit: Maximum number of tasks to return
        offset: Offset for pagination
        
    Returns:
        List of task information
    """
    tasks = await task_service.list_tasks(status, limit, offset)
    return tasks


@router.delete("/tasks/{task_id}", response_model=Dict[str, Any])
async def delete_task(task_id: str):
    """Delete a task.
    
    Args:
        task_id: ID of the task to delete
        
    Returns:
        Success message
    """
    success = await task_service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted", "task_id": task_id} 