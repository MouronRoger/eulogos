"""FastAPI dependencies for service instances."""

import logging
from functools import lru_cache

from app.config import EulogosSettings
from app.services.catalog_service_adapter import CatalogServiceAdapter
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService
from app.services.xml_processor_adapter import XMLProcessorServiceAdapter

logger = logging.getLogger(__name__)


@lru_cache()
def get_settings() -> EulogosSettings:
    """Get application settings, cached for performance."""
    logger.debug("Creating EulogosSettings instance")
    return EulogosSettings()


@lru_cache()
def get_enhanced_catalog_service() -> EnhancedCatalogService:
    """Get an EnhancedCatalogService instance, cached for performance."""
    logger.debug("Creating EnhancedCatalogService instance")
    settings = get_settings()
    service = EnhancedCatalogService(settings=settings)

    # Eagerly load the catalog
    service.load_catalog()

    return service


@lru_cache()
def get_enhanced_xml_service() -> EnhancedXMLService:
    """Get an EnhancedXMLService instance, cached for performance."""
    logger.debug("Creating EnhancedXMLService instance")
    catalog_service = get_enhanced_catalog_service()
    settings = get_settings()
    return EnhancedXMLService(catalog_service=catalog_service, settings=settings)


@lru_cache()
def get_catalog_service() -> CatalogServiceAdapter:
    """Get a CatalogServiceAdapter instance for backward compatibility.

    Returns:
        CatalogServiceAdapter instance that wraps EnhancedCatalogService
    """
    logger.debug("Creating CatalogServiceAdapter instance")
    enhanced_service = get_enhanced_catalog_service()
    return CatalogServiceAdapter(enhanced_service=enhanced_service)


@lru_cache()
def get_xml_processor_service() -> XMLProcessorServiceAdapter:
    """Get a XMLProcessorServiceAdapter instance for backward compatibility.

    Returns:
        XMLProcessorServiceAdapter instance
    """
    logger.debug("Creating XMLProcessorServiceAdapter instance")
    catalog_service = get_enhanced_catalog_service()
    xml_service = get_enhanced_xml_service()
    return XMLProcessorServiceAdapter(enhanced_service=xml_service, catalog_service=catalog_service)
