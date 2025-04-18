"""Texts router for the Eulogos web application.

Provides endpoints for text management, including archive, favorite, and delete operations.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from fastapi.responses import JSONResponse
from loguru import logger

from app.dependencies import get_catalog_service
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/texts", tags=["texts"])


@router.post("/{text_id}/archive")
async def archive_text(
    text_id: str,
    archive: bool = Query(True, description="True to archive, False to unarchive"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Archive or unarchive a text.

    Args:
        text_id: Text ID
        archive: True to archive, False to unarchive
        catalog_service: CatalogService instance

    Returns:
        JSON response with success status and archive state
    """
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    success = catalog_service.archive_text_by_id(text_id, archive)
    return {"success": success, "archived": archive}


@router.post("/{text_id}/favorite")
async def favorite_text(
    text_id: str,
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Toggle favorite status for a text.

    Args:
        text_id: Text ID
        catalog_service: CatalogService instance

    Returns:
        JSON response with success status and favorite state
    """
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    success = catalog_service.toggle_text_favorite_by_id(text_id)
    
    # Get updated text to check the current favorite status
    text = catalog_service.get_text_by_id(text_id)
    
    return {"success": success, "favorite": text.favorite if text else False}


@router.delete("/{text_id}")
async def delete_text(
    text_id: str,
    confirmation: bool = Query(False, description="Confirm deletion"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Delete a text from the catalog.

    Args:
        text_id: Text ID
        confirmation: Confirmation flag for safety
        catalog_service: CatalogService instance

    Returns:
        JSON response with success status
    """
    if not confirmation:
        raise HTTPException(status_code=400, detail="Confirmation required")

    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")

    success = catalog_service.delete_text_by_id(text_id)
    return {"success": success}


@router.post("/batch")
async def batch_operations(
    text_ids: List[str] = Body(..., description="List of text IDs to operate on"),
    operation: str = Body(..., description="Operation to perform: archive, unarchive, favorite, unfavorite, delete"),
    confirmation: bool = Body(False, description="Confirmation for destructive operations"),
    catalog_service: CatalogService = Depends(get_catalog_service),
):
    """Perform batch operations on multiple texts.

    Args:
        text_ids: List of text IDs to operate on
        operation: Operation to perform (archive, unarchive, favorite, unfavorite, delete)
        confirmation: Confirmation for destructive operations
        catalog_service: CatalogService instance

    Returns:
        JSON response with operation results
    """
    # Validate operation
    valid_operations = ["archive", "unarchive", "favorite", "unfavorite", "delete"]
    if operation not in valid_operations:
        raise HTTPException(
            status_code=400, detail=f"Invalid operation: {operation}. Must be one of {valid_operations}"
        )

    # Check confirmation for delete
    if operation == "delete" and not confirmation:
        raise HTTPException(status_code=400, detail="Confirmation required for delete operation")

    # Process the batch operation
    results = {"successful": [], "failed": []}

    for text_id in text_ids:
        try:
            if operation == "archive":
                catalog_service.archive_text_by_id(text_id, True)
            elif operation == "unarchive":
                catalog_service.archive_text_by_id(text_id, False)
            elif operation == "favorite" or operation == "unfavorite":
                catalog_service.toggle_text_favorite_by_id(text_id)
            elif operation == "delete":
                catalog_service.delete_text_by_id(text_id)

            results["successful"].append(text_id)
        except Exception as e:
            results["failed"].append({"text_id": text_id, "error": str(e)})

    return {
        "status": "success",
        "operation": operation,
        "total": len(text_ids),
        "succeeded": len(results["successful"]),
        "failed": len(results["failed"]),
        "results": results,
    } 