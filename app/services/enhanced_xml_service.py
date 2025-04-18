"""Enhanced service for XML processing with additional functionality."""

from loguru import logger

from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService


class EnhancedXMLService(XMLProcessorService):
    """Enhanced service for processing XML files with additional features."""

    def __init__(self, catalog_service: CatalogService = None):
        """Initialize the enhanced XML service.

        Args:
            catalog_service: Optional catalog service instance
        """
        super().__init__(catalog_service)
        logger.debug("Initializing EnhancedXMLService")
