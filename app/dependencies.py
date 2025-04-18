"""FastAPI dependencies for service instances."""

import logging
from functools import lru_cache

from app.config import EulogosSettings
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService

logger = logging.getLogger(__name__)


@lru_cache()
def get_settings() -> EulogosSettings:
    """Get application settings, cached for performance."""
    logger.debug("Creating EulogosSettings instance")
    return EulogosSettings()


@lru_cache()
def get_catalog_service() -> EnhancedCatalogService:
    """Get an EnhancedCatalogService instance, cached for performance.

    This is the primary catalog service for the application.

    Returns:
        EnhancedCatalogService instance
    """
    logger.debug("Creating EnhancedCatalogService instance")
    settings = get_settings()
    service = EnhancedCatalogService(settings=settings)

    # Eagerly load the catalog
    service.load_catalog()

    return service


@lru_cache()
def get_xml_processor_service() -> EnhancedXMLService:
    """Get an EnhancedXMLService instance, cached for performance.

    This is the primary XML service for the application.

    Returns:
        EnhancedXMLService instance
    """
    logger.debug("Creating EnhancedXMLService instance")
    catalog_service = get_catalog_service()
    settings = get_settings()
    return EnhancedXMLService(catalog_service=catalog_service, settings=settings)


# Legacy function aliases - preserved for backward compatibility references only
# These will be removed in a future version
@lru_cache()
def get_enhanced_catalog_service() -> EnhancedCatalogService:
    """Get catalog service (legacy alias, use get_catalog_service instead)."""
    logger.warning("get_enhanced_catalog_service() is deprecated, use get_catalog_service() instead")
    return get_catalog_service()


@lru_cache()
def get_enhanced_xml_service() -> EnhancedXMLService:
    """Get XML service (legacy alias, use get_xml_processor_service instead)."""
    logger.warning("get_enhanced_xml_service() is deprecated, use get_xml_processor_service() instead")
    return get_xml_processor_service()
