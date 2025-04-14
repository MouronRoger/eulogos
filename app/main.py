"""Main FastAPI application module for Eulogos."""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

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