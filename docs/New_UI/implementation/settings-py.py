"""Configuration settings for the Eulogos application.

Settings are used throughout the application to ensure consistent configuration.
"""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings.
    
    These settings can be overridden by environment variables with the
    prefix EULOGOS_ (e.g., EULOGOS_CATALOG_PATH).
    """
    
    # Paths
    catalog_path: str = "integrated_catalog.json"
    data_dir: str = "data"
    
    # Features
    debug: bool = False
    
    class Config:
        """Pydantic config."""
        env_prefix = "EULOGOS_"
        env_file = ".env"
        case_sensitive = False


settings = Settings()