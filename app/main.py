"""Main FastAPI application module for Eulogos."""

import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from loguru import logger

from app.routers import texts, browse, reader

# Set up the application
app = FastAPI(
    title="Eulogos",
    description="A web application for exploring ancient Greek texts",
    version="0.1.0",
)

# Set up static files and templates
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Include routers
app.include_router(texts.router, prefix="/api")
app.include_router(browse.router, prefix="/api")
app.include_router(reader.router)

# Configure logging
logger.add("logs/eulogos.log", rotation="10 MB", level="INFO")

@app.get("/")
async def root():
    """Return the root endpoint response."""
    return {"message": "Welcome to Eulogos - Ancient Greek Texts Explorer"}

@app.get("/health")
async def health_check():
    """Return health check information."""
    return {"status": "ok", "version": "0.1.0"}

@app.get("/browse", response_class=HTMLResponse)
async def browse_page(request: Request):
    """Render the browse page.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse with rendered template
    """
    return templates.TemplateResponse("browse.html", {"request": request}) 