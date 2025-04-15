"""FastAPI dependencies for service instances."""

from functools import lru_cache

from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService


@lru_cache()
def get_catalog_service() -> CatalogService:
    """Get a CatalogService instance.

    Returns:
        CatalogService instance
    """
    return CatalogService()


@lru_cache()
def get_xml_processor_service() -> XMLProcessorService:
    """Get an XMLProcessorService instance.

    Returns:
        XMLProcessorService instance
    """
    return XMLProcessorService()
