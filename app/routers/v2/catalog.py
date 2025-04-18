"""API routes for catalog operations using the simplified catalog service."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.dependencies import get_simple_catalog_service
from app.models.catalog import Author, Text
from app.services.simple_catalog_service import SimpleCatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/texts", response_model=List[Text])
async def get_all_texts(
    include_archived: bool = False,
    language: Optional[str] = None,
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get all texts in the catalog.

    Args:
        include_archived: Whether to include archived texts
        language: Filter by language code (e.g., 'grc', 'lat', 'eng')
        catalog_service: SimpleCatalogService dependency

    Returns:
        List of text metadata
    """
    # Filter by language if specified
    if language:
        texts = catalog_service.get_texts_by_language(language, include_archived)
    else:
        texts = catalog_service.get_all_texts(include_archived)

    return texts


@router.get("/texts/{urn}", response_model=Text)
async def get_text_by_urn(
    urn: str = Path(..., title="The URN of the text"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get text metadata by URN.

    Args:
        urn: The URN of the text
        catalog_service: SimpleCatalogService dependency

    Returns:
        Text metadata

    Raises:
        HTTPException: If text not found
    """
    text = catalog_service.get_text_by_urn(urn)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text with URN {urn} not found")

    return text


@router.get("/authors", response_model=List[Author])
async def get_all_authors(
    include_archived: bool = False,
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get all authors in the catalog.

    Args:
        include_archived: Whether to include authors with only archived texts
        catalog_service: SimpleCatalogService dependency

    Returns:
        List of author metadata
    """
    authors = catalog_service.get_authors(include_archived)
    return authors


@router.get("/authors/{author_id}", response_model=Author)
async def get_author_by_id(
    author_id: str = Path(..., title="Author ID"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get author metadata by ID.

    Args:
        author_id: Author ID
        catalog_service: SimpleCatalogService dependency

    Returns:
        Author metadata

    Raises:
        HTTPException: If author not found
    """
    author = catalog_service.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail=f"Author with ID {author_id} not found")

    return author


@router.get("/authors/{author_id}/texts", response_model=List[Text])
async def get_texts_by_author(
    author_id: str = Path(..., title="Author ID"),
    include_archived: bool = False,
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get texts by an author.

    Args:
        author_id: Author ID
        include_archived: Whether to include archived texts
        catalog_service: SimpleCatalogService dependency

    Returns:
        List of text metadata

    Raises:
        HTTPException: If author not found
    """
    # Verify author exists
    author = catalog_service.get_author_by_id(author_id)
    if not author:
        raise HTTPException(status_code=404, detail=f"Author with ID {author_id} not found")

    texts = catalog_service.get_texts_by_author(author_id, include_archived)
    return texts


@router.post("/texts/{urn}/archive", response_model=Dict[str, bool])
async def archive_text(
    urn: str = Path(..., title="The URN of the text"),
    archive: bool = Query(True, title="Whether to archive or unarchive"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Archive or unarchive a text.

    Args:
        urn: The URN of the text
        archive: True to archive, False to unarchive
        catalog_service: SimpleCatalogService dependency

    Returns:
        Success status

    Raises:
        HTTPException: If text not found
    """
    result = catalog_service.archive_text(urn, archive)
    if not result:
        raise HTTPException(status_code=404, detail=f"Text with URN {urn} not found")

    return {"success": True, "archived": archive}


@router.post("/texts/{urn}/favorite", response_model=Dict[str, bool])
async def favorite_text(
    urn: str = Path(..., title="The URN of the text"),
    favorite: bool = Query(True, title="Whether to mark as favorite or not"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Mark a text as favorite or not.

    Args:
        urn: The URN of the text
        favorite: True to mark as favorite, False to unmark
        catalog_service: SimpleCatalogService dependency

    Returns:
        Success status

    Raises:
        HTTPException: If text not found
    """
    result = catalog_service.favorite_text(urn, favorite)
    if not result:
        raise HTTPException(status_code=404, detail=f"Text with URN {urn} not found")

    return {"success": True, "favorite": favorite}


@router.post("/texts/{urn}/toggle-favorite", response_model=Dict[str, bool])
async def toggle_favorite(
    urn: str = Path(..., title="The URN of the text"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Toggle the favorite status of a text.

    Args:
        urn: The URN of the text
        catalog_service: SimpleCatalogService dependency

    Returns:
        New favorite status

    Raises:
        HTTPException: If text not found
    """
    result = catalog_service.toggle_favorite(urn)
    if result is False:
        raise HTTPException(status_code=404, detail=f"Text with URN {urn} not found")

    return {"success": True, "favorite": result}


@router.get("/resolve/{urn}", response_model=Dict[str, str])
async def resolve_urn_to_path(
    urn: str = Path(..., title="The URN to resolve"),
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Resolve a URN to a file path.

    Args:
        urn: The URN to resolve
        catalog_service: SimpleCatalogService dependency

    Returns:
        Dictionary with resolved path

    Raises:
        HTTPException: If URN format is invalid
    """
    try:
        path = catalog_service.resolve_urn_to_path(urn)
        return {"urn": urn, "path": str(path)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics", response_model=Dict[str, int])
async def get_catalog_statistics(
    catalog_service: SimpleCatalogService = Depends(get_simple_catalog_service),
):
    """Get catalog statistics.

    Args:
        catalog_service: SimpleCatalogService dependency

    Returns:
        Dictionary with catalog statistics
    """
    return catalog_service.get_catalog_statistics()
