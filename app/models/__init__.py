"""Model classes for the Eulogos API."""

from app.models.catalog import Author, Text, UnifiedCatalog
from app.models.simple_urn import SimpleURN
from app.models.xml_document import XMLDocument

__all__ = ["Author", "Text", "UnifiedCatalog", "SimpleURN", "XMLDocument"]
