"""Request validation middleware and utilities for the Eulogos API.

This module provides validation functionality including:
- URN format validation
- Export options validation
- API version handling
- Request validation middleware
- Batch export validation
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

from app.models.enhanced_urn import EnhancedURN

# Configure logging
logger = logging.getLogger(__name__)


class ExportOptions(BaseModel):
    """Validation model for export options."""

    reference: Optional[str] = None
    filename: Optional[str] = None
    include_metadata: bool = True
    custom_css: Optional[str] = None
    format: str = "html"
    compression: Optional[str] = Field(
        None, description="Compression format to use (gzip, bzip2, or zip)", regex="^(gzip|bzip2|zip)?$"
    )

    class Config:
        """Pydantic config."""

        extra = "forbid"  # Forbid extra attributes


class ValidationMiddleware:
    """Middleware for request validation."""

    async def __call__(self, request: Request, call_next):
        """Apply validation middleware."""
        try:
            # Validate path parameters
            path_params = request.path_params
            if "urn" in path_params:
                try:
                    EnhancedURN(value=path_params["urn"])
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=f"Invalid URN format: {str(e)}")

            # Validate query parameters for export endpoints
            if request.url.path.startswith("/api/v2/export"):
                query_params = dict(request.query_params)
                try:
                    ExportOptions(**query_params)
                except ValidationError as e:
                    raise HTTPException(status_code=400, detail=f"Invalid export options: {str(e)}")

            # Process request
            response = await call_next(request)
            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")


class APIVersionMiddleware:
    """Middleware for API versioning."""

    def __init__(self, default_version: str = "1"):
        """Initialize version middleware.

        Args:
            default_version: Default API version
        """
        self.default_version = default_version

    async def __call__(self, request: Request, call_next):
        """Apply versioning middleware."""
        # Check version from header or URL
        version = (
            request.headers.get("X-API-Version") or self.get_version_from_path(request.url.path) or self.default_version
        )

        # Add version to request state
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version to response headers
        response.headers["X-API-Version"] = version
        return response

    def get_version_from_path(self, path: str) -> Optional[str]:
        """Extract version from path."""
        if "/api/v" in path:
            parts = path.split("/")
            for part in parts:
                if part.startswith("v") and part[1:].isdigit():
                    return part[1:]
        return None


class RequestValidators:
    """Collection of request validators."""

    @staticmethod
    def validate_urn(urn: str) -> EnhancedURN:
        """Validate URN format."""
        try:
            return EnhancedURN(value=urn)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid URN format: {str(e)}")

    @staticmethod
    def validate_export_options(options: Dict[str, Any]) -> ExportOptions:
        """Validate export options."""
        try:
            return ExportOptions(**options)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid export options: {str(e)}")

    @staticmethod
    def validate_batch_export(urns: List[str], options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate batch export request."""
        validated_urns = []
        for urn in urns:
            try:
                validated_urns.append(EnhancedURN(value=urn))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid URN format for {urn}: {str(e)}")

        try:
            validated_options = ExportOptions(**options)
            return {"urns": validated_urns, "options": validated_options}
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid export options: {str(e)}")


# Example usage in FastAPI app:
"""
from fastapi import FastAPI
from app.middleware.validation import ValidationMiddleware, APIVersionMiddleware

app = FastAPI()

# Add middleware
app.add_middleware(ValidationMiddleware)
app.add_middleware(APIVersionMiddleware)

# Use validators in routes
@app.get("/api/v2/export/{urn}")
async def export_text(
    urn: str,
    options: Dict[str, Any],
    validators: RequestValidators = Depends()
):
    validated_urn = validators.validate_urn(urn)
    validated_options = validators.validate_export_options(options)
    # Your export logic here
    return {"message": "Export successful"}
"""
