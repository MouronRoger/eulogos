"""Main FastAPI application module for Eulogos."""

import os

from fastapi import Depends, FastAPI, Query, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.dependencies import get_settings, get_simple_catalog_service
from app.middleware.api_monitoring import APIVersionMonitoringMiddleware
from app.middleware.api_redirect import APIRedirectMiddleware
from app.middleware.performance import PerformanceMiddleware
from app.routers import admin, browse, export, reader, texts
from app.routers.v2 import browse as browse_v2
from app.routers.v2 import catalog as catalog_v2
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
app.include_router(catalog_v2.router, tags=["Catalog"])
app.include_router(diagnostics_v2.router, tags=["Diagnostics"])

# Configure logging
logger.add("logs/eulogos.log", rotation="10 MB", level="INFO")


@app.get("/check-path/{urn}")
async def check_path(urn: str, data_path: str = Query("data"), catalog_service=Depends(get_simple_catalog_service)):
    """Check URN to path resolution with the simplified catalog service.

    Args:
        urn: The URN to resolve
        data_path: Base data directory
        catalog_service: SimpleCatalogService instance

    Returns:
        JSON response with path information
    """
    try:
        # Get path using the SimpleCatalogService
        path = catalog_service.resolve_urn_to_path(urn)

        # Check if file exists
        exists = path.exists()
        is_file = path.is_file() if exists else False

        # Get URN components
        urn_obj = catalog_service._texts_by_urn.get(urn)
        if urn_obj:
            components = {
                "namespace": urn_obj.namespace,
                "textgroup": urn_obj.textgroup,
                "work": urn_obj.work_id,
                "version": urn_obj.version,
            }
        else:
            # Parse URN components manually if not in catalog
            from app.models.simple_urn import SimpleURN

            simple_urn = SimpleURN(value=urn)
            components = simple_urn.get_components()

        result = {"urn": urn, "components": components, "path": str(path), "exists": exists, "is_file": is_file}

        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": f"Error resolving URN: {str(e)}"}, status_code=400)


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
