"""Tests for the Enhanced Catalog Service.

This module contains unit tests for catalog management functionality.
"""

import os
from pathlib import Path

import pytest

from app.models.enhanced_urn import EnhancedURN
from app.services.enhanced_catalog_service import EnhancedCatalogService


def test_load_catalog(test_settings, sample_catalog_file):
    """Test loading the catalog."""
    service = EnhancedCatalogService(settings=test_settings)
    catalog = service.load_catalog()

    # Check that catalog loaded successfully
    assert catalog is not None
    assert len(catalog.authors) == 1
    assert "tlg0012" in catalog.authors

    # Check author data
    homer = catalog.authors["tlg0012"]
    assert homer.name == "Homer"
    assert homer.century == -8

    # Check works
    assert "tlg001" in homer.works
    iliad = homer.works["tlg001"]
    assert iliad.title == "Iliad"

    # Check editions
    assert "perseus-grc1" in iliad.editions
    edition = iliad.editions["perseus-grc1"]
    assert edition.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
    assert edition.path == "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml"


def test_load_catalog_nonexistent_file(test_settings):
    """Test loading a nonexistent catalog file."""
    test_settings.catalog_path = Path("nonexistent.json")
    service = EnhancedCatalogService(settings=test_settings)

    with pytest.raises(FileNotFoundError):
        service.load_catalog()


def test_get_path_by_urn(test_settings):
    """Test getting path by URN."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    # Test with string URN
    path = service.get_path_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert path == "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml"

    # Test with EnhancedURN object
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    path = service.get_path_by_urn(urn)
    assert path == "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml"

    # Test non-existent URN
    path = service.get_path_by_urn("urn:cts:greekLit:tlg0012.tlg002.perseus-grc1")
    assert path is None


def test_resolve_file_path(test_settings, sample_xml_file):
    """Test resolving URN to file path."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    # Test with string URN
    path = service.resolve_file_path("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert path is not None
    assert path.name == "tlg0012.tlg001.perseus-grc1.xml"

    # Test with EnhancedURN object
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    path = service.resolve_file_path(urn)
    assert path is not None
    assert path.name == "tlg0012.tlg001.perseus-grc1.xml"

    # Test fallback for non-existent URN in compatibility mode
    path = service.resolve_file_path("urn:cts:greekLit:tlg0013.tlg001.perseus-grc1")
    assert path is not None  # Should use fallback path
    assert path.name == "tlg0013.tlg001.perseus-grc1.xml"

    # Test fallback disabled
    service.settings.compatibility_mode = False
    path = service.resolve_file_path("urn:cts:greekLit:tlg0013.tlg001.perseus-grc1")
    assert path is None  # Should not use fallback path


def test_get_text_by_urn(test_settings):
    """Test getting text by URN."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    # Test with string URN
    text = service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert text is not None
    assert text.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test non-existent URN
    text = service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg002.perseus-grc1")
    assert text is None

    # Test compatibility mode with original model
    class MockTextClass:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    service._original_text_class = MockTextClass
    text = service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert text is not None
    assert isinstance(text, MockTextClass)
    assert text.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
    assert text.group_name == "Homer"
    assert text.work_name == "Iliad"


def test_get_authors(test_settings):
    """Test getting authors."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    # Get all authors
    authors = service.get_authors()
    assert len(authors) == 1
    assert authors[0].name == "Homer"

    # Test with archived author
    authors[0].archived = True
    authors = service.get_authors()
    assert len(authors) == 0  # Should be filtered out

    # Test including archived authors
    authors = service.get_authors(include_archived=True)
    assert len(authors) == 1
    assert authors[0].name == "Homer"


def test_get_texts_by_author(test_settings):
    """Test getting texts by author."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    # Get texts for author
    texts = service.get_texts_by_author("tlg0012")
    assert len(texts) == 1
    assert texts[0].urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test with archived text
    texts[0].archived = True
    texts = service.get_texts_by_author("tlg0012")
    assert len(texts) == 0  # Should be filtered out

    # Test including archived texts
    texts = service.get_texts_by_author("tlg0012", include_archived=True)
    assert len(texts) == 1

    # Test non-existent author
    texts = service.get_texts_by_author("nonexistent")
    assert len(texts) == 0


def test_validate_path_consistency(test_settings, sample_xml_file):
    """Test path consistency validation."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    results = service.validate_path_consistency()

    assert results["total_urns"] == 1
    assert results["urns_with_path"] == 1
    assert results["existing_files"] == 1
    assert results["missing_files"] == 0

    # Test with missing file
    os.remove(sample_xml_file)
    results = service.validate_path_consistency()
    assert results["missing_files"] == 1
    assert len(results["missing_files_list"]) == 1


def test_archive_text(test_settings):
    """Test archiving and unarchiving a text."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Archive text
    success = service.archive_text(urn, archive=True)
    assert success is True

    # Check that text is archived
    text = service.get_text_by_urn(urn)
    assert text.archived is True

    # Unarchive text
    success = service.archive_text(urn, archive=False)
    assert success is True

    # Check that text is unarchived
    text = service.get_text_by_urn(urn)
    assert text.archived is False

    # Test with non-existent URN
    success = service.archive_text("nonexistent-urn")
    assert success is False


def test_toggle_favorite(test_settings):
    """Test toggling favorite status."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Initial state should be false
    text = service.get_text_by_urn(urn)
    assert text.favorite is False

    # Toggle favorite on
    success = service.toggle_favorite(urn)
    assert success is True

    # Check that favorite is toggled on
    text = service.get_text_by_urn(urn)
    assert text.favorite is True

    # Toggle favorite off
    success = service.toggle_favorite(urn)
    assert success is True

    # Check that favorite is toggled off
    text = service.get_text_by_urn(urn)
    assert text.favorite is False

    # Test with non-existent URN
    success = service.toggle_favorite("nonexistent-urn")
    assert success is False


def test_build_indexes(test_settings):
    """Test index building."""
    service = EnhancedCatalogService(settings=test_settings)
    catalog = service.load_catalog()  # noqa: F841 - Used indirectly to populate service indexes

    # Check text_path_by_urn index
    assert "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1" in service._text_path_by_urn
    path = service._text_path_by_urn["urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"]
    assert path == "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml"

    # Check urn_by_path index
    assert path in service._urn_by_path
    urn = service._urn_by_path[path]
    assert urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Check texts_by_author index
    assert "tlg0012" in service._texts_by_author
    urns = service._texts_by_author["tlg0012"]
    assert "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1" in urns

    # Check texts_by_language index
    assert "grc" in service._texts_by_language
    urns = service._texts_by_language["grc"]
    assert "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1" in urns
