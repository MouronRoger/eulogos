"""Enhanced service for XML processing with additional functionality."""

from loguru import logger

from app.config import EulogosSettings
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService


class EnhancedXMLService(XMLProcessorService):
    """Enhanced service for processing XML files with additional features."""

    def __init__(self, catalog_service: CatalogService, settings: EulogosSettings = None):
        """Initialize the enhanced XML service.

        Args:
            catalog_service: Catalog service instance for path resolution. Required
                as the catalog is the single source of truth for path resolution.
            settings: Application settings

        Raises:
            ValueError: If no catalog service is provided
        """
        data_dir = str(settings.data_dir) if settings else "data"

        if not catalog_service:
            raise ValueError(
                "EnhancedXMLService requires a catalog_service. "
                "The catalog is the single source of truth for path resolution."
            )

        super().__init__(data_path=data_dir, catalog_service=catalog_service)
        logger.debug("Initialized EnhancedXMLService with catalog_service and data_dir={}", data_dir)
