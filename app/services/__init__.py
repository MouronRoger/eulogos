"""Services for the Eulogos application."""

from app.services.catalog_service import CatalogService, get_catalog_service
from app.services.xml_service import XMLService

__all__ = ["CatalogService", "XMLService", "get_catalog_service"] 