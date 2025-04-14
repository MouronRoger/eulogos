"""Main application module for Eulogos."""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.routers.admin import router as admin_router

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.add("logs/eulogos.log", level=log_level, rotation="10 MB")

# Create app
app = FastAPI(
    title="Eulogos",
    description="Web application for accessing ancient Greek texts",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(admin_router)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Home page route.

    Args:
        request: The request object
        
    Returns:
        HTML response
    """
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Eulogos"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Status message
    """
    return {"status": "ok"} 