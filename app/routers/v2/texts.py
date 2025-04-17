"""Router for text management operations (v2 API).

This module provides enhanced endpoints for text management functionality including:
- Archive/unarchive functionality for texts
- Favorite/unfavorite functionality for texts
- Delete functionality with proper safeguards
- Batch operations for multiple texts
- Detailed operation status reporting
"""

from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.dependencies import get_enhanced_catalog_service
from app.services.enhanced_catalog_service import EnhancedCatalogService

# Create router
router = APIRouter(
    prefix="/api/v2",
    tags=["texts"],
    responses={404: {"description": "Not found"}},
)


@router.post("/texts/{urn}/archive", response_model=None)
async def archive_text(
    urn: str, archive: bool = True, catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service)
):
    """Archive or unarchive a text.

    Args:
        urn: The URN of the text to archive/unarchive
        archive: True to archive, False to unarchive
        catalog_service: EnhancedCatalogService instance

    Returns:
        JSON response with status and archived state

    Raises:
        HTTPException: If text is not found
    """
    try:
        catalog_service.archive_text(urn, archive)
        return {"status": "success", "archived": archive, "urn": urn}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Text not found: {str(e)}")


@router.post("/texts/{urn}/favorite", response_model=None)
async def favorite_text(urn: str, catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service)):
    """Toggle favorite status for a text.

    Args:
        urn: The URN of the text to favorite/unfavorite
        catalog_service: EnhancedCatalogService instance

    Returns:
        JSON response with status

    Raises:
        HTTPException: If text is not found
    """
    try:
        result = catalog_service.toggle_text_favorite(urn)
        return {"status": "success", "urn": urn, "favorite": result}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Text not found: {str(e)}")


@router.delete("/texts/{urn}", response_model=None)
async def delete_text(
    urn: str,
    confirmation: bool = Query(False, description="Confirm deletion"),
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
):
    """Delete a text.

    Args:
        urn: The URN of the text to delete
        confirmation: Confirmation flag
        catalog_service: EnhancedCatalogService instance

    Returns:
        JSON response with status

    Raises:
        HTTPException: If text is not found or confirmation not provided
    """
    if not confirmation:
        raise HTTPException(status_code=400, detail="Confirmation required")

    try:
        catalog_service.delete_text(urn)
        return {"status": "success", "urn": urn}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Text not found: {str(e)}")


@router.post("/texts/batch", response_model=None)
async def batch_operations(
    urns: List[str] = Body(..., description="List of URNs to operate on"),
    operation: str = Body(..., description="Operation to perform: archive, unarchive, favorite, unfavorite, delete"),
    confirmation: bool = Body(False, description="Confirmation for destructive operations"),
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
):
    """Perform batch operations on multiple texts.

    Args:
        urns: List of URNs to operate on
        operation: Operation to perform (archive, unarchive, favorite, unfavorite, delete)
        confirmation: Confirmation for destructive operations
        catalog_service: EnhancedCatalogService instance

    Returns:
        JSON response with operation results

    Raises:
        HTTPException: If operation is invalid or confirmation not provided for delete
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

    for urn in urns:
        try:
            if operation == "archive":
                catalog_service.archive_text(urn, True)
            elif operation == "unarchive":
                catalog_service.archive_text(urn, False)
            elif operation == "favorite" or operation == "unfavorite":
                catalog_service.toggle_text_favorite(urn)
            elif operation == "delete":
                catalog_service.delete_text(urn)

            results["successful"].append(urn)
        except Exception as e:
            results["failed"].append({"urn": urn, "error": str(e)})

    return {
        "status": "success",
        "operation": operation,
        "total": len(urns),
        "succeeded": len(results["successful"]),
        "failed": len(results["failed"]),
        "results": results,
    }
