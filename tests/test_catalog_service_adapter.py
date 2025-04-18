"""Tests for the CatalogServiceAdapter.

This module provides tests for the CatalogServiceAdapter which provides
a compatibility layer for existing code.
"""

import warnings
from unittest.mock import MagicMock, patch

from app.services.catalog_service_adapter import CatalogServiceAdapter
from app.services.enhanced_catalog_service import EnhancedCatalogService


