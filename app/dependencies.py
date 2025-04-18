"""FastAPI dependencies for service instances."""

import logging
from functools import lru_cache

from app.config import EulogosSettings
from app.services.simple_catalog_service import SimpleCatalogService

logger = logging.getLogger(__name__)


@lru_cache()
def get_settings() -> EulogosSettings:
    """Get application settings, cached for performance."""
    logger.debug("Creating EulogosSettings instance")
    return EulogosSettings()


@lru_cache()
def get_simple_catalog_service() -> SimpleCatalogService:
    """Get the SimpleCatalogService dependency.

    Returns:
        SimpleCatalogService instance
    """
    settings = get_settings()
    service = SimpleCatalogService(
        catalog_path=str(settings.catalog_path),
        data_dir=str(settings.data_dir),
    )

    # Initialize the service
    service.load_catalog()

    return service
