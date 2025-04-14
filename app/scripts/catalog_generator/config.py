"""Configuration for the catalog generator."""

from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class CatalogGeneratorConfig(BaseSettings):
    """Configuration for the catalog generator.
    
    This class defines the configuration options for the catalog generator,
    using Pydantic's BaseSettings for environment variable support.
    """
    
    data_dir: Path = Field(
        default=Path("data"), 
        description="Path to data directory"
    )
    author_index: Path = Field(
        default=Path("author_index.json"), 
        description="Path to author index"
    )
    output_file: Path = Field(
        default=Path("integrated_catalog.json"), 
        description="Output file path"
    )
    log_level: str = Field(
        default="info", 
        description="Logging level"
    )
    include_content_sample: bool = Field(
        default=False, 
        description="Include text content samples"
    )
    stats_only: bool = Field(
        default=False, 
        description="Generate only statistics"
    )
    
    class Config:
        """Pydantic config."""
        
        env_prefix = "CATALOG_"
        env_file = ".env" 