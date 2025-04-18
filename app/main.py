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


@app.get("/api/xml/{author_id}/{work_id}/{edition_id}")
async def get_xml_file(author_id: str, work_id: str, edition_id: str):
    """Get the XML file for a specific edition."""
    catalog = load_catalog()

    if author_id not in catalog:
        raise HTTPException(status_code=404, detail=f"Author {author_id} not found")

    works = catalog[author_id].get("works", {})
    if work_id not in works:
        raise HTTPException(status_code=404, detail=f"Work {work_id} not found")

    editions = works[work_id].get("editions", {})
    if edition_id not in editions:
        raise HTTPException(status_code=404, detail=f"Edition {edition_id} not found")

    edition = editions[edition_id]
    file_path = edition.get("path")

    if not file_path:
        raise HTTPException(status_code=404, detail="Path not found in catalog")

    full_path = DATA_DIR / file_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {full_path}")

    return FileResponse(full_path, media_type="application/xml")


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

    return JSONResponse(content={"paths": paths, "count": len(paths)})


@app.get("/api/debug/paths")
async def debug_paths():
    """Debug endpoint to check all paths in the catalog."""
    catalog = load_catalog()
    paths = []

    for author_id, author_data in catalog.items():
        works = author_data.get("works", {})

        for work_id, work_data in works.items():
            editions = work_data.get("editions", {})

            for edition_id, edition_data in editions.items():
                path = edition_data.get("path")
                if path:
                    full_path = DATA_DIR / path
                    exists = full_path.exists()
                    paths.append(
                        {
                            "author_id": author_id,
                            "work_id": work_id,
                            "edition_id": edition_id,
                            "path": path,
                            "full_path": str(full_path),
                            "exists": exists,
                        }
                    )

    return JSONResponse(
        content={"paths": paths, "count": len(paths), "missing": len([p for p in paths if not p["exists"]])}
    )


@app.get("/api/debug/file/{author_id}/{work_id}/{edition_id}")
async def debug_file(author_id: str, work_id: str, edition_id: str):
    """Debug endpoint to check a specific file."""
    catalog = load_catalog()

    if author_id not in catalog:
        return JSONResponse(content={"error": f"Author {author_id} not found"}, status_code=404)

    works = catalog[author_id].get("works", {})
    if work_id not in works:
        return JSONResponse(content={"error": f"Work {work_id} not found"}, status_code=404)

    editions = works[work_id].get("editions", {})
    if edition_id not in editions:
        return JSONResponse(content={"error": f"Edition {edition_id} not found"}, status_code=404)

    edition = editions[edition_id]
    file_path = edition.get("path")

    if not file_path:
        return JSONResponse(content={"error": "Path not found in catalog"}, status_code=404)

    full_path = DATA_DIR / file_path

    return JSONResponse(
        content={
            "path": file_path,
            "full_path": str(full_path),
            "exists": full_path.exists(),
            "is_file": full_path.is_file() if full_path.exists() else None,
            "size": full_path.stat().st_size if full_path.exists() else None,
        }
    )
