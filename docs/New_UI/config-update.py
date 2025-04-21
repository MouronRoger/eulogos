"""Configuration settings for the Eulogos application.

This module provides application settings using Pydantic with support for
environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.
    
    These settings can be overridden by environment variables with the
    prefix EULOGOS_ (e.g., EULOGOS_DATA_DIR).
    """
    
    # Application metadata
    app_name: str = "Eulogos"
    app_version: str = "0.1.0"
    app_description: str = "Ancient Greek Text Repository"
    debug: bool = Field(False, description="Enable debug mode")
    
    # Paths
    data_dir: Path = Field(
        Path("data"), 
        description="Directory containing XML text files"
    )
    catalog_path: Path = Field(
        Path("integrated_catalog.json"), 
        description="Path to the catalog JSON file"
    )
    
    # Features
    enable_caching: bool = Field(
        True, 
        description="Enable caching of XML documents"
    )
    enable_searching: bool = Field(
        True, 
        description="Enable text search functionality"
    )
    
    # XML processing
    strip_xml_namespaces: bool = Field(
        True, 
        description="Strip namespaces from XML elements when processing"
    )
    max_xml_size: int = Field(
        10 * 1024 * 1024,  # 10 MB
        description="Maximum size of XML files to process"
    )
    
    class Config:
        """Pydantic config."""
        env_prefix = "EULOGOS_"
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get application settings.
    
    This function is cached to avoid reloading settings for every request.
    
    Returns:
        Application settings
    """
    return Settings() 