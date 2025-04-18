"""FastAPI dependencies for service instances."""

import logging
from functools import lru_cache
from typing import Optional

from fastapi import Depends
from loguru import logger

from app.config import EulogosSettings, get_settings
from app.services.catalog_service import CatalogService
from app.services.export_service import ExportService
from app.services.xml_processor_service import XMLProcessorService


@lru_cache(maxsize=1)
def get_catalog_service() -> CatalogService:
    """Get a CatalogService instance, cached for performance.
    
    This function caches the service to avoid repeated initialization
    when used with FastAPI's dependency injection system.
    The lru_cache ensures we only create one instance of the service
    during the application's lifetime.
    
    Returns:
        CatalogService instance
    """
    logger.debug("Creating CatalogService instance")
    settings = get_settings()
    service = CatalogService(settings=settings)
    service.create_unified_catalog()
    return service


@lru_cache(maxsize=1)
def get_xml_service(
    catalog_service: CatalogService = Depends(get_catalog_service),
    settings: EulogosSettings = Depends(get_settings),
) -> XMLProcessorService:
    """Get a XMLProcessorService instance, cached for performance.
    
    Args:
        catalog_service: Catalog service instance
        settings: Application settings
        
    Returns:
        XMLProcessorService instance
    """
    logger.debug("Creating XMLProcessorService instance")
    return XMLProcessorService(catalog_service=catalog_service, settings=settings)


@lru_cache(maxsize=1)
def get_export_service(
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLProcessorService = Depends(get_xml_service),
    settings: Optional[EulogosSettings] = Depends(get_settings),
) -> ExportService:
    """Get an ExportService instance, cached for performance.
    
    Args:
        catalog_service: Catalog service instance
        xml_service: XML service instance
        settings: Application settings
        
    Returns:
        ExportService instance
    """
    logger.debug("Creating ExportService instance")
    return ExportService(
        catalog_service=catalog_service,
        xml_service=xml_service,
        settings=settings,
    )
