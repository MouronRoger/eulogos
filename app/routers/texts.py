"""Router for text management operations."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.catalog_service import CatalogService

# Dependency to get catalog service
def get_catalog_service():
    """Get instance of catalog service.
    
    Returns:
        CatalogService instance
    """
    service = CatalogService(
        catalog_path="integrated_catalog.json",
        data_dir="data"
    )
    service.create_unified_catalog()
    return service

router = APIRouter(tags=["texts"])

@router.post("/texts/{urn}/archive")
async def archive_text(
    urn: str,
    archive: bool = True,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Archive or unarchive a text.
    
    Args:
        urn: The URN of the text to archive/unarchive
        archive: True to archive, False to unarchive
        catalog_service: CatalogService instance
        
    Returns:
        JSON response with status and archived state
        
    Raises:
        HTTPException: If text is not found
    """
    success = catalog_service.archive_text(urn, archive)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"status": "success", "archived": archive}

@router.post("/texts/{urn}/favorite")
async def favorite_text(
    urn: str,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Toggle favorite status for a text.
    
    Args:
        urn: The URN of the text to favorite/unfavorite
        catalog_service: CatalogService instance
        
    Returns:
        JSON response with status
        
    Raises:
        HTTPException: If text is not found
    """
    success = catalog_service.toggle_text_favorite(urn)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"status": "success"}

@router.delete("/texts/{urn}")
async def delete_text(
    urn: str,
    confirmation: bool = Query(False, description="Confirm deletion"),
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Delete a text.
    
    Args:
        urn: The URN of the text to delete
        confirmation: Confirmation flag
        catalog_service: CatalogService instance
        
    Returns:
        JSON response with status
        
    Raises:
        HTTPException: If text is not found or confirmation not provided
    """
    if not confirmation:
        raise HTTPException(status_code=400, detail="Confirmation required")
    
    success = catalog_service.delete_text(urn)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"status": "success"} 