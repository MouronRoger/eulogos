"""Enhanced service for catalog operations with additional functionality."""

from typing import Optional

from loguru import logger

from app.config import EulogosSettings
from app.services.catalog_service import CatalogService


class EnhancedCatalogService(CatalogService):
    """Enhanced service for accessing the unified catalog with additional features."""

    def __init__(
        self,
        catalog_path: str = None,
        author_path: str = None,
        data_dir: str = None,
        settings: Optional[EulogosSettings] = None,
    ):
        """Initialize the enhanced catalog service.

        Args:
            catalog_path: Path to the catalog_index.json file
            author_path: Path to the author_index.json file
            data_dir: Path to the data directory
            settings: Application settings
        """
        # If settings are provided, extract paths from it
        if settings:
            catalog_path = catalog_path or str(settings.catalog_path)
            data_dir = data_dir or str(settings.data_dir)

        super().__init__(catalog_path, author_path, data_dir)
        logger.debug("Initializing EnhancedCatalogService with catalog_path={}, data_dir={}", catalog_path, data_dir)
