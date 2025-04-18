"""Main FastAPI application module for Eulogos."""

import os

from fastapi import FastAPI, Query, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.dependencies import get_settings
from app.middleware.api_monitoring import APIVersionMonitoringMiddleware
from app.middleware.api_redirect import APIRedirectMiddleware
from app.middleware.performance import PerformanceMiddleware
from app.routers import admin, browse, export, reader, texts
from app.routers.v2 import browse as browse_v2
from app.routers.v2 import diagnostics as diagnostics_v2
from app.routers.v2 import export as export_v2
from app.routers.v2 import reader as reader_v2
from app.routers.v2 import texts as texts_v2

# Get application settings
settings = get_settings()

# Set up the application
app = FastAPI(
    title="Eulogos API",
    description="API for exploring and managing ancient Greek texts from the First 1000 Years Project",
    version="2.0.0",
    docs_url="/api/v2/docs",
    redoc_url="/api/v2/redoc",
    openapi_url="/api/v2/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)


def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add additional info
    openapi_schema["info"]["x-logo"] = {"url": "/static/img/logo.png", "altText": "Eulogos Logo"}

    openapi_schema["info"]["contact"] = {
        "name": "Eulogos Support",
        "email": "support@eulogos.example.com",
        "url": "https://eulogos.example.com/support",
    }

    # Add deprecation notice for v1 endpoints
    for path in openapi_schema["paths"]:
        if "/api/v2/" not in path and "/api/" in path:
            for method in openapi_schema["paths"][path]:
                if isinstance(openapi_schema["paths"][path][method], dict):
                    openapi_schema["paths"][path][method]["deprecated"] = True
                    current_desc = openapi_schema["paths"][path][method].get("description", "")
                    deprecation_notice = (
                        f"**DEPRECATED**: This endpoint is deprecated and will be removed "
                        f"on {settings.v1_sunset_date}. Please use the corresponding v2 endpoint instead."
                    )
                    openapi_schema["paths"][path][method]["description"] = f"{current_desc}\n\n{deprecation_notice}"

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Add middlewares
app.add_middleware(PerformanceMiddleware, log_threshold_ms=200)
app.add_middleware(APIVersionMonitoringMiddleware)
app.add_middleware(APIRedirectMiddleware)

# Set up static files and templates
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/static")
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app/templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Include original routers
app.include_router(texts.router, prefix="/api", tags=["Texts v1 (Deprecated)"])
app.include_router(browse.router, prefix="/api", tags=["Browse v1 (Deprecated)"])
app.include_router(reader.router, tags=["Reader v1 (Deprecated)"])
app.include_router(export.router, tags=["Export v1 (Deprecated)"])
app.include_router(admin.router, tags=["Admin"])

# Include v2 routers
app.include_router(export_v2.router, tags=["Export"])
app.include_router(browse_v2.router, tags=["Browse"])
app.include_router(reader_v2.router, tags=["Reader"])
app.include_router(texts_v2.router, tags=["Texts"])
app.include_router(diagnostics_v2.router, tags=["Diagnostics"])

# Configure logging
logger.add("logs/eulogos.log", rotation="10 MB", level="INFO")


# Simple direct URN to path function right in main.py
def direct_urn_to_path(urn: str, data_path: str = "data") -> str:
    """Transform a URN directly to a file path."""
    parts = urn.split(":")
    if len(parts) < 4:
        return f"Invalid URN format: {urn}"

    # Get the identifier (e.g., tlg0532.tlg001.perseus-grc2)
    identifier = parts[3].split("#")[0]

    # Split into components
    id_parts = identifier.split(".")
    if len(id_parts) < 3:
        return f"URN missing version information: {urn}"

    # Extract components
    textgroup = id_parts[0]
    work = id_parts[1]
    version = id_parts[2]

    # Construct the path
    path = f"{data_path}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml"

    return path


@app.get("/check-path/{urn}")
async def check_path(urn: str, data_path: str = Query("data")):
    """Check URN to path resolution with a simple direct approach.

    Args:
        urn: The URN to resolve
        data_path: Base data directory

    Returns:
        JSON response with path information
    """
    path = direct_urn_to_path(urn, data_path)

    # Check if file exists
    exists = os.path.exists(path)
    is_file = os.path.isfile(path) if exists else False

    # Parse URN components for reference
    parts = urn.split(":")
    namespace = parts[2] if len(parts) >= 3 else None

    identifier = parts[3].split("#")[0] if len(parts) >= 4 else None
    id_parts = identifier.split(".") if identifier else []

    textgroup = id_parts[0] if len(id_parts) >= 1 else None
    work = id_parts[1] if len(id_parts) >= 2 else None
    version = id_parts[2] if len(id_parts) >= 3 else None

    result = {
        "urn": urn,
        "components": {"namespace": namespace, "textgroup": textgroup, "work": work, "version": version},
        "path": path,
        "exists": exists,
        "is_file": is_file,
    }

    # Try alternate paths
    alternates = []

    if textgroup and work and version:
        # Try without namespace directory
        alt1 = f"{data_path}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml"
        alternates.append({"path": alt1, "exists": os.path.exists(alt1), "is_file": os.path.isfile(alt1)})

        # Try with namespace directory
        alt2 = f"{data_path}/{namespace}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml"
        alternates.append({"path": alt2, "exists": os.path.exists(alt2), "is_file": os.path.isfile(alt2)})

    result["alternates"] = alternates

    return JSONResponse(content=result)


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
    return {"status": "ok", "version": "2.0.0"}
