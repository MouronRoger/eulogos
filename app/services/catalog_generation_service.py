"""Service for catalog generation operations."""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Union

from loguru import logger

from app.scripts.catalog_generator.config import CatalogGeneratorConfig
from app.scripts.catalog_generator.catalog_builder import generate_catalog
from app.services.task_service import TaskService


class CatalogGenerationService:
    """Service for generating the integrated catalog.
    
    This service encapsulates the functionality of the catalog generator script
    and provides a programmatic interface for generating the catalog, with
    support for background processing and progress tracking.
    """
    
    def __init__(
        self, 
        data_dir: Union[str, Path] = "data", 
        author_path: Union[str, Path] = "author_index.json",
        output_path: Union[str, Path] = "integrated_catalog.json",
        task_service: Optional[TaskService] = None
    ):
        """Initialize the catalog generation service.
        
        Args:
            data_dir: Path to the data directory
            author_path: Path to the author_index.json file
            output_path: Path for the output catalog file
            task_service: Optional TaskService for tracking progress
        """
        self.data_dir = Path(data_dir)
        self.author_path = Path(author_path)
        self.output_path = Path(output_path)
        self.task_service = task_service or TaskService()
        
    async def generate_catalog_async(
        self, 
        task_id: Optional[str] = None,
        include_content_sample: bool = False,
        stats_only: bool = False
    ) -> Dict[str, Any]:
        """Generate the integrated catalog asynchronously.
        
        Args:
            task_id: Optional task ID for tracking progress
            include_content_sample: Whether to include content samples
            stats_only: Whether to generate only statistics
            
        Returns:
            The generated catalog
        """
        # Create config
        config = CatalogGeneratorConfig(
            data_dir=self.data_dir,
            author_index=self.author_path,
            output_file=self.output_path,
            include_content_sample=include_content_sample,
            stats_only=stats_only
        )
        
        # Define progress callback
        async def progress_callback(progress: int, message: str):
            if task_id:
                await self.task_service.update_task_progress(task_id, progress, message)
        
        # Run the catalog generation in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        catalog = await loop.run_in_executor(
            None,
            lambda: self._generate_catalog_sync(config, progress_callback)
        )
        
        # Update task result
        if task_id:
            await self.task_service.set_task_result(task_id, {
                "file_path": str(self.output_path),
                "statistics": catalog["statistics"]
            })
        
        return catalog
    
    def _generate_catalog_sync(
        self, 
        config: CatalogGeneratorConfig,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """Generate the catalog synchronously.
        
        Args:
            config: Configuration for catalog generation
            progress_callback: Callback for progress updates
            
        Returns:
            The generated catalog
        """
        # Adapter for progress callback to handle async callback
        def sync_progress_callback(progress: int, message: str):
            if progress_callback:
                asyncio.run(progress_callback(progress, message))
        
        # Generate the catalog
        try:
            return generate_catalog(config, sync_progress_callback)
        except Exception as e:
            logger.error(f"Error generating catalog: {e}")
            if progress_callback:
                asyncio.run(progress_callback(-1, f"Error: {str(e)}"))
            raise
    
    async def create_catalog_generation_task(
        self,
        include_content_sample: bool = False,
        stats_only: bool = False,
        user_id: Optional[str] = None
    ) -> str:
        """Create a new task for catalog generation.
        
        Args:
            include_content_sample: Whether to include content samples
            stats_only: Whether to generate only statistics
            user_id: Optional ID of the user initiating the task
            
        Returns:
            Task ID
        """
        parameters = {
            "data_dir": str(self.data_dir),
            "author_index": str(self.author_path),
            "output_file": str(self.output_path),
            "include_content_sample": include_content_sample,
            "stats_only": stats_only
        }
        
        if user_id:
            parameters["initiated_by"] = user_id
            
        # Create a task
        task_id = await self.task_service.create_task("catalog_generation", parameters)
        
        # Start processing in the background
        asyncio.create_task(self.generate_catalog_async(
            task_id=task_id,
            include_content_sample=include_content_sample,
            stats_only=stats_only
        ))
        
        return task_id
        
    async def get_catalog_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current catalog.
        
        Returns:
            Dictionary with catalog statistics
        """
        if not self.output_path.exists():
            return {
                "exists": False,
                "error": "Catalog file not found"
            }
            
        try:
            with open(self.output_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
                
            stats = catalog.get("statistics", {})
            return {
                "exists": True,
                "last_modified": self.output_path.stat().st_mtime,
                "file_size": self.output_path.stat().st_size,
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"Error loading catalog statistics: {e}")
            return {
                "exists": True,
                "error": str(e)
            } 