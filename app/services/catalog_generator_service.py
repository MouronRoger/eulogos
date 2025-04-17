"""Service for generating the integrated catalog."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from app.scripts.catalog_generator.catalog_builder import generate_catalog
from app.scripts.catalog_generator.config import CatalogGeneratorConfig

logger = logging.getLogger(__name__)


class CatalogGeneratorService:
    """Service for generating the integrated catalog."""

    def __init__(self, data_dir: str, catalog_path: str):
        """Initialize the service.

        Args:
            data_dir: Path to the data directory
            catalog_path: Path to the catalog file
        """
        self.data_dir = Path(data_dir)
        self.catalog_path = Path(catalog_path)

    async def generate_catalog_async(
        self,
        include_content_sample: bool = False,
        stats_only: bool = False,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """Generate the catalog asynchronously.

        Args:
            include_content_sample: Whether to include content samples
            stats_only: Whether to generate only statistics
            progress_callback: Callback for reporting progress

        Returns:
            Generated catalog
        """
        # Create configuration
        config = CatalogGeneratorConfig(
            data_dir=self.data_dir,
            output_file=self.catalog_path,
            include_content_sample=include_content_sample,
            stats_only=stats_only,
        )

        # Run the catalog generation in a thread pool
        loop = asyncio.get_event_loop()
        catalog = await loop.run_in_executor(None, lambda: generate_catalog(config, progress_callback))

        return catalog

    def generate_catalog(
        self,
        include_content_sample: bool = False,
        stats_only: bool = False,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """Generate the catalog synchronously.

        Args:
            include_content_sample: Whether to include content samples
            stats_only: Whether to generate only statistics
            progress_callback: Callback for reporting progress

        Returns:
            Generated catalog
        """
        # Create configuration
        config = CatalogGeneratorConfig(
            data_dir=self.data_dir,
            output_file=self.catalog_path,
            include_content_sample=include_content_sample,
            stats_only=stats_only,
        )

        # Generate catalog
        return generate_catalog(config, progress_callback)
