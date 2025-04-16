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
    return CatalogService(catalog_path="integrated_catalog.json", data_dir="data")


@lru_cache()
def get_xml_processor_service(
    catalog_service: CatalogService = None,
) -> XMLProcessorService:
    """Get an XMLProcessorService instance with catalog service for path resolution.

    Args:
        catalog_service: Optional catalog service instance

    Returns:
        XMLProcessorService instance
    """
    # If catalog_service is not provided through DI, get it
    if catalog_service is None:
        catalog_service = get_catalog_service()

    return XMLProcessorService(data_path="data", catalog_service=catalog_service)
