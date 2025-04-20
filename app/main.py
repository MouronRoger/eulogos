"""Main FastAPI application module for Eulogos.

This module initializes the FastAPI application and sets up the
dependencies, routes, and services needed by the application.
"""

import datetime
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.config import get_settings
from app.routers import browse_router, read_router
from app.services.catalog_service import get_catalog_service

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

# Setup static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(browse_router)
app.include_router(read_router)

# Add some utility context processors for templates
@app.middleware("http")
async def add_template_context(request: Request, call_next):
    """Add common template context variables."""
    response = await call_next(request)
    
    # Only process HTML responses going to templates
    if isinstance(response, HTMLResponse) and hasattr(response, "context"):
        # Add current year for copyright
        response.context["current_year"] = datetime.datetime.now().year
        
    return response


@app.get("/api/catalog")
async def get_catalog(catalog_service=Depends(get_catalog_service)):
    """API endpoint to get the full catalog."""
    return catalog_service._catalog


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": settings.app_version,
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