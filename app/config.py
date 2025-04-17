"""Configuration settings for the Eulogos application.

This module provides centralized configuration management using Pydantic settings,
with support for environment variables and .env files.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class EulogosSettings(BaseSettings):
    """Configuration settings for Eulogos application."""

    # Catalog paths
    catalog_path: Path = Field(
        default=Path("integrated_catalog.json"), description="Path to the integrated catalog JSON file"
    )

    # Data directories
    data_dir: Path = Field(default=Path("data"), description="Base directory for text data files")

    # Cache settings
    xml_cache_size: int = Field(default=100, description="Maximum number of XML documents to cache")
    xml_cache_ttl: int = Field(default=3600, description="Time to live for cached XML documents in seconds")

    # Performance settings
    enable_caching: bool = Field(default=True, description="Enable caching for XML documents")

    # Compatibility settings
    compatibility_mode: bool = Field(default=True, description="Enable compatibility with existing code")

    # Logging settings
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    log_file: Optional[Path] = Field(default=Path("logs/eulogos.log"), description="Log file path")

    @validator("catalog_path", "data_dir", pre=True)
    def validate_paths(cls, v):
        """Validate paths and convert to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    def as_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {k: str(v) if isinstance(v, Path) else v for k, v in self.dict().items()}

    class Config:
        """Configure settings behavior."""

        env_prefix = "EULOGOS_"
        env_file = ".env"
