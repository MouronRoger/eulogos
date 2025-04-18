"""Main FastAPI application module for Eulogos."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

# Set up the application
app = FastAPI(
    title="Eulogos API",
    description="API for exploring and managing ancient Greek texts from the First 1000 Years Project",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Set up static files and templates
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Configure logging
logger.add("logs/eulogos.log", rotation="10 MB", level="INFO")

# Path to catalog file - using absolute path
CATALOG_PATH = Path("/Users/james/Documents/GitHub/eulogos/integrated_catalog.json")
DATA_DIR = Path("/Users/james/Documents/GitHub/eulogos/data")


def load_catalog():
    """Load the catalog data from the integrated_catalog.json file."""
    if not CATALOG_PATH.exists():
        logger.error(f"Catalog file not found: {CATALOG_PATH}")
        return {}

    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)
            logger.info(f"Loaded catalog from {CATALOG_PATH}")
            return catalog_data
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        return {}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the browse page."""
    # Pre-load catalog data
    catalog = load_catalog()

    # Process catalog to get a list of authors with works
    authors = []
    for author_id, author_data in catalog.items():
        works_data = author_data.get("works", {})
        works = []

        for work_id, work_data in works_data.items():
            work = {"id": work_id, "title": work_data.get("title", ""), "editions": [], "translations": []}

            for edition_id, edition_data in work_data.get("editions", {}).items():
                work["editions"].append(
                    {
                        "id": edition_id,
                        "label": edition_data.get("label", ""),
                        "language": edition_data.get("language", ""),
                        "path": edition_data.get("path", ""),
                    }
                )

            for translation_id, translation_data in work_data.get("translations", {}).items():
                work["translations"].append(
                    {
                        "id": translation_id,
                        "label": translation_data.get("label", ""),
                        "language": translation_data.get("language", ""),
                        "path": translation_data.get("path", ""),
                    }
                )

            if work["editions"] or work["translations"]:
                works.append(work)

        if works:
            authors.append(
                {
                    "id": author_id,
                    "name": author_data.get("name", ""),
                    "century": author_data.get("century", ""),
                    "type": author_data.get("type", ""),
                    "works": works,
                }
            )

    # Sort authors by name
    authors.sort(key=lambda x: x["name"])

    return templates.TemplateResponse(
        "browse.html", {"request": request, "authors": authors, "author_count": len(authors)}
    )


@app.get("/health")
async def health_check():
    """Return health check information."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/catalog")
async def get_catalog():
    """Get the full catalog data."""
    catalog = load_catalog()
    return JSONResponse(content=catalog)


@app.get("/api/authors")
async def get_authors():
    """Get all authors."""
    catalog = load_catalog()
    authors = []

    for author_id, author_data in catalog.items():
        authors.append(
            {
                "id": author_id,
                "name": author_data.get("name"),
                "century": author_data.get("century"),
                "type": author_data.get("type"),
            }
        )

    return JSONResponse(content={"authors": authors})


@app.get("/api/authors/{author_id}")
async def get_author(author_id: str):
    """Get a specific author by ID."""
    catalog = load_catalog()

    if author_id not in catalog:
        return JSONResponse(content={"error": "Author not found"}, status_code=404)

    return JSONResponse(content=catalog[author_id])


@app.get("/api/works/{author_id}/{work_id}")
async def get_work(author_id: str, work_id: str):
    """Get a specific work by author ID and work ID."""
    catalog = load_catalog()

    if author_id not in catalog:
        return JSONResponse(content={"error": "Author not found"}, status_code=404)

    works = catalog[author_id].get("works", {})
    if work_id not in works:
        return JSONResponse(content={"error": "Work not found"}, status_code=404)

    return JSONResponse(content=works[work_id])


@app.get("/data/{path:path}")
async def get_file_by_path(path: str):
    """Get a file directly using its path from the catalog.

    This is the canonical method for accessing XML files,
    using paths exactly as they appear in the integrated_catalog.json.
    The integrated_catalog.json is the single source of truth for all paths.
    """
    # Build the full path by joining the data directory with the path
    full_path = DATA_DIR / path

    # Check if the file exists
    if not full_path.exists():
        logger.error(f"File not found: {full_path}")
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    # Determine the media type based on file extension
    if path.endswith(".xml"):
        media_type = "application/xml"
    elif path.endswith(".json"):
        media_type = "application/json"
    elif path.endswith(".txt"):
        media_type = "text/plain"
    else:
        media_type = "application/octet-stream"

    # Return the file content
    return FileResponse(full_path, media_type=media_type)


@app.get("/api/paths")
async def get_all_paths():
    """Get all file paths from the catalog."""
    catalog = load_catalog()
    paths = []

    for author_id, author_data in catalog.items():
        works = author_data.get("works", {})

        for work_id, work_data in works.items():
            editions = work_data.get("editions", {})

            for edition_id, edition_data in editions.items():
                path = edition_data.get("path")
                if path:
                    paths.append(
                        {
                            "author_id": author_id,
                            "work_id": work_id,
                            "edition_id": edition_id,
                            "path": path,
                            "full_path": str(DATA_DIR / path),
                        }
                    )

            translations = work_data.get("translations", {})
            for translation_id, translation_data in translations.items():
                path = translation_data.get("path")
                if path:
                    paths.append(
                        {
                            "author_id": author_id,
                            "work_id": work_id,
                            "translation_id": translation_id,
                            "path": path,
                            "full_path": str(DATA_DIR / path),
                        }
                    )

    return JSONResponse(content={"paths": paths, "count": len(paths)})


@app.get("/api/debug/file/{path:path}")
async def debug_file(path: str):
    """Debug endpoint to check a specific file path.

    This uses the same path format as the canonical file access method.
    """
    # Build the full path by joining the data directory with the path
    full_path = DATA_DIR / path

    return JSONResponse(
        content={
            "path": path,
            "full_path": str(full_path),
            "exists": full_path.exists(),
            "is_file": full_path.is_file() if full_path.exists() else None,
            "size": full_path.stat().st_size if full_path.exists() else None,
        }
    )
