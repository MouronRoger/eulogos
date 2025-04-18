"""Request validation middleware and utilities for the Eulogos API.

This module provides validation functionality including:

- Export options validation
- Request validation middleware
- Batch export validation
"""

import logging
from typing import Any, ClassVar, Dict, Optional

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

# Configure logging
logger = logging.getLogger(__name__)


class ExportOptions(BaseModel):
    """Validation model for export options."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")  # Forbid extra attributes

    reference: Optional[str] = None
    filename: Optional[str] = None
    include_metadata: bool = True
    custom_css: Optional[str] = None
    format: str = "html"
    compression: Optional[str] = Field(
        None, description="Compression format to use (gzip, bzip2, or zip)", pattern="^(gzip|bzip2|zip)?$"
    )


class ValidationMiddleware:
    """Middleware for request validation."""

    async def __call__(self, request: Request, call_next):
        """Apply validation middleware."""
        try:
            # Validate path parameters
            path_params = request.path_params
            
            # Validate query parameters for export endpoints
            if request.url.path.startswith("/api/export"):
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


class RequestValidators:
    """Collection of request validators."""

    @staticmethod
    def validate_export_options(options: Dict[str, Any]) -> ExportOptions:
        """Validate export options."""
        try:
            return ExportOptions(**options)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid export options: {str(e)}")


# Example usage in FastAPI app:
"""
from fastapi import FastAPI
from app.middleware.validation import ValidationMiddleware

app = FastAPI()

# Add middleware
app.add_middleware(ValidationMiddleware)

# Use validators in routes
@app.get("/api/export/{id}")
async def export_text(
    id: str,
    options: Dict[str, Any],
    validators: RequestValidators = Depends()
):
    validated_options = validators.validate_export_options(options)
    # Your export logic here
    return {"message": "Export successful"}
"""
