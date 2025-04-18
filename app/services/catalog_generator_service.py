"""Service for generating the integrated catalog."""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CatalogGeneratorService:
    """Service for generating the integrated catalog using the canonical catalog builder."""

    def __init__(self, data_dir: str, catalog_path: str):
        """Initialize the service.

        Args:
            data_dir: Path to the data directory
            catalog_path: Path to the catalog file
        """
        self.data_dir = Path(data_dir)
        self.catalog_path = Path(catalog_path)
        self.author_index_path = Path("author_index.json")

    async def generate_catalog_async(
        self,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """Generate the catalog asynchronously.

        Args:
            progress_callback: Callback for reporting progress

        Returns:
            Generated catalog
        """
        # Report initial status
        if progress_callback:
            progress_callback(0, "Starting catalog generation...")

        # Run the catalog generation in a subprocess
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.generate_catalog(progress_callback))

    def generate_catalog(
        self,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """Generate the catalog synchronously.

        Args:
            progress_callback: Callback for reporting progress

        Returns:
            Generated catalog
        """
        # Report starting
        if progress_callback:
            progress_callback(10, "Running canonical catalog builder...")

        logger.info("Starting canonical catalog generation")

        # Prepare command arguments
        cmd = [
            "python3",
            "app/scripts/canonical_catalog_builder.py",
            f"--data-dir={self.data_dir}",
            f"--output={self.catalog_path}",
            f"--author-index={self.author_index_path}",
            "--verbose",
        ]

        try:
            # Run the command
            logger.info(f"Executing command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Progress updates
            if progress_callback:
                progress_callback(30, "Processing authors and works...")

            # Wait for completion
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logger.error(f"Catalog generation failed: {stderr}")
                raise RuntimeError(f"Catalog generation failed: {stderr}")

            logger.info("Catalog generation completed successfully")

            # Report progress
            if progress_callback:
                progress_callback(90, "Catalog generated, loading results...")

            # Load and return the generated catalog
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)

            if progress_callback:
                progress_callback(100, "Catalog generation complete")

            return catalog

        except Exception as e:
            logger.error(f"Error during catalog generation: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            raise
