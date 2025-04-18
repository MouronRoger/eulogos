"""Configuration settings for the Eulogos application.

This module provides centralized configuration management using Pydantic settings,
with support for environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class EulogosSettings(BaseSettings):
    """Configuration settings for Eulogos application."""

    model_config: ClassVar[ConfigDict] = ConfigDict(env_prefix="EULOGOS_", env_file=".env")

    # Catalog paths
    catalog_path: Path = Field(
        default=Path("integrated_catalog.json"), description="Path to the integrated catalog JSON file"
    )

    # Data directories
    data_dir: Path = Field(default=Path("data"), description="Base directory for text data files")

    # Cache settings
    xml_cache_size: int = Field(default=100, description="Maximum number of XML documents to cache")
    xml_cache_ttl: int = Field(default=3600, description="Time to live for cached XML documents in seconds")
    cache_max_size_bytes: int = Field(
        default=50 * 1024 * 1024, description="Maximum cache size in bytes (default: 50MB)"
    )

    # Performance settings
    enable_caching: bool = Field(default=True, description="Enable caching for XML documents")

    # Compatibility settings
    compatibility_mode: bool = Field(default=False, description="Enable compatibility with existing code")

    # API version settings
    api_version: int = Field(default=2, description="Default API version (1 or 2)")
    enable_api_redirects: bool = Field(default=True, description="Enable automatic redirects from v1 to v2 API")
    deprecate_v1_api: bool = Field(default=True, description="Add deprecation headers to v1 API responses")
    v1_sunset_date: Optional[str] = Field(
        default="2025-12-31", description="Sunset date for v1 API (ISO format, e.g., '2025-12-31')"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    log_file: Optional[Path] = Field(default=Path("logs/eulogos.log"), description="Log file path")

    @field_validator("catalog_path", "data_dir", mode="before")
    @classmethod
    def validate_paths(cls, v):
        """Validate paths and convert to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("api_version")
    @classmethod
    def validate_api_version(cls, v):
        """Validate API version."""
        if v not in (1, 2):
            raise ValueError("API version must be either 1 or 2")
        return v

    def model_dump(self) -> Dict[str, Any]:
        """Convert settings to dictionary.

        Replaces the deprecated dict() method.
        """
        return {k: str(v) if isinstance(v, Path) else v for k, v in super().model_dump().items()}


@lru_cache()
def get_settings() -> EulogosSettings:
    """Get a cached instance of the settings.
    
    Returns:
        EulogosSettings: The application settings
    """
    return EulogosSettings()
