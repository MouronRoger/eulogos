"""Main FastAPI application module for Eulogos."""

import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.dependencies import get_settings
from app.middleware.api_redirect import APIRedirectMiddleware
from app.routers import admin, browse, export, reader, texts
from app.routers.v2 import browse as browse_v2
from app.routers.v2 import export as export_v2
from app.routers.v2 import reader as reader_v2
from app.routers.v2 import texts as texts_v2

# Get application settings
settings = get_settings()

# Set up the application
app = FastAPI(
    title="Eulogos",
    description="A web application for exploring ancient Greek texts",
    version="0.1.0",
)

# Add middlewares
app.add_middleware(APIRedirectMiddleware)

# Set up static files and templates
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Include original routers
app.include_router(texts.router, prefix="/api")
app.include_router(browse.router, prefix="/api")
app.include_router(reader.router)
app.include_router(export.router)
app.include_router(admin.router)

# Include v2 routers
app.include_router(export_v2.router)
app.include_router(browse_v2.router)
app.include_router(reader_v2.router)
app.include_router(texts_v2.router)

# Configure logging
logger.add("logs/eulogos.log", rotation="10 MB", level="INFO")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the browse page.

    Args:
        request: FastAPI request object

    Returns:
        HTMLResponse with rendered template
    """
    return templates.TemplateResponse("browse.html", {"request": request})


@app.get("/health")
async def health_check():
    """Return health check information."""
    return {"status": "ok", "version": "0.1.0"}
