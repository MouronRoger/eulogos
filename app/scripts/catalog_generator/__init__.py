"""Catalog generator module for Eulogos.

This module contains functionality for generating the integrated catalog
from XML files in the data directory. It is a modular implementation of
the enhanced-scan-xml-urns.py script.
"""

from app.scripts.catalog_generator.config import CatalogGeneratorConfig
from app.scripts.catalog_generator.catalog_builder import generate_catalog

__all__ = ["CatalogGeneratorConfig", "generate_catalog"]
