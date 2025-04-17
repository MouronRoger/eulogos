"""Tests for the CatalogServiceAdapter.

This module provides tests for the CatalogServiceAdapter which provides
a compatibility layer for existing code.
"""

import warnings
from unittest.mock import MagicMock, patch

from app.services.catalog_service_adapter import CatalogServiceAdapter
from app.services.enhanced_catalog_service import EnhancedCatalogService


def test_init_with_warning():
    """Test that initialization issues a deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        # Cause all warnings to always be triggered
        warnings.simplefilter("always")

        # Create adapter
        adapter = CatalogServiceAdapter()  # noqa: F841 - Used for test setup

        # Check warning was raised
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message)


def test_init_with_enhanced_service():
    """Test initialization with a provided EnhancedCatalogService."""
    enhanced_service = MagicMock(spec=EnhancedCatalogService)

    with warnings.catch_warnings():
        # Ignore deprecation warning
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(enhanced_service=enhanced_service)  # noqa: F841 - Used for test setup

    assert adapter.enhanced_service is enhanced_service


def test_init_with_settings():
    """Test initialization with settings creates enhanced service."""
    settings = MagicMock()

    with warnings.catch_warnings(), patch(
        "app.services.catalog_service_adapter.EnhancedCatalogService"
    ) as mock_service:
        # Ignore deprecation warning
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(settings=settings)

        # Check EnhancedCatalogService was created with settings
        mock_service.assert_called_once_with(settings=settings)
        assert isinstance(adapter, CatalogServiceAdapter)


def test_load_catalog():
    """Test load_catalog method delegates to enhanced service."""
    enhanced_service = MagicMock(spec=EnhancedCatalogService)
    mock_catalog = MagicMock()
    enhanced_service.load_catalog.return_value = mock_catalog

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(enhanced_service=enhanced_service)

    # Call adapter method
    result = adapter.load_catalog()

    # Check delegation
    enhanced_service.load_catalog.assert_called_once()
    assert result is mock_catalog


def test_get_text_by_urn():
    """Test get_text_by_urn method delegates to enhanced service."""
    enhanced_service = MagicMock(spec=EnhancedCatalogService)
    mock_text = MagicMock()
    enhanced_service.get_text_by_urn.return_value = mock_text

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(enhanced_service=enhanced_service)

    # Call adapter method
    result = adapter.get_text_by_urn("test:urn")

    # Check delegation
    enhanced_service.get_text_by_urn.assert_called_once_with("test:urn")
    assert result is mock_text


def test_get_path_by_urn():
    """Test get_path_by_urn method delegates to enhanced service."""
    enhanced_service = MagicMock(spec=EnhancedCatalogService)
    enhanced_service.get_path_by_urn.return_value = "path/to/file.xml"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(enhanced_service=enhanced_service)

    # Call adapter method
    result = adapter.get_path_by_urn("test:urn")

    # Check delegation
    enhanced_service.get_path_by_urn.assert_called_once_with("test:urn")
    assert result == "path/to/file.xml"


def test_resolve_file_path():
    """Test resolve_file_path method delegates to enhanced service."""
    enhanced_service = MagicMock(spec=EnhancedCatalogService)
    mock_path = MagicMock()
    enhanced_service.resolve_file_path.return_value = mock_path

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(enhanced_service=enhanced_service)

    # Call adapter method
    result = adapter.resolve_file_path("test:urn")

    # Check delegation
    enhanced_service.resolve_file_path.assert_called_once_with("test:urn")
    assert result is mock_path


def test_get_authors():
    """Test get_authors method delegates to enhanced service."""
    enhanced_service = MagicMock(spec=EnhancedCatalogService)
    mock_authors = [MagicMock(), MagicMock()]
    enhanced_service.get_authors.return_value = mock_authors

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(enhanced_service=enhanced_service)

    # Call adapter method
    result = adapter.get_authors(include_archived=True)

    # Check delegation
    enhanced_service.get_authors.assert_called_once_with(include_archived=True)
    assert result is mock_authors


def test_get_texts_by_author():
    """Test get_texts_by_author method delegates to enhanced service."""
    enhanced_service = MagicMock(spec=EnhancedCatalogService)
    mock_texts = [MagicMock(), MagicMock()]
    enhanced_service.get_texts_by_author.return_value = mock_texts

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(enhanced_service=enhanced_service)

    # Call adapter method
    result = adapter.get_texts_by_author("author1", include_archived=True)

    # Check delegation
    enhanced_service.get_texts_by_author.assert_called_once_with("author1", include_archived=True)
    assert result is mock_texts


def test_archive_text():
    """Test archive_text method delegates to enhanced service."""
    enhanced_service = MagicMock(spec=EnhancedCatalogService)
    enhanced_service.archive_text.return_value = True

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(enhanced_service=enhanced_service)

    # Call adapter method
    result = adapter.archive_text("test:urn", archive=True)

    # Check delegation
    enhanced_service.archive_text.assert_called_once_with("test:urn", archive=True)
    assert result is True


def test_toggle_text_favorite():
    """Test toggle_text_favorite method delegates to enhanced service."""
    enhanced_service = MagicMock(spec=EnhancedCatalogService)
    enhanced_service.toggle_favorite.return_value = True

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        adapter = CatalogServiceAdapter(enhanced_service=enhanced_service)

    # Call adapter method
    result = adapter.toggle_text_favorite("test:urn")

    # Check delegation
    enhanced_service.toggle_favorite.assert_called_once_with("test:urn")
    assert result is True
