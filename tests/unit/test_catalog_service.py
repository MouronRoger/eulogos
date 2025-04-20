"""Unit tests for the catalog service.

These tests verify that the catalog service correctly loads and processes
catalog data with paths as the canonical identifiers for texts.
"""

import json
import os
import pytest
from pathlib import Path
from typing import Dict, List, Any

from app.models.catalog import Catalog, Text
from app.services.catalog_service import CatalogService


def test_load_catalog(sample_catalog_file: Path) -> None:
    """Test loading the catalog from a valid JSON file."""
    service = CatalogService(catalog_path=str(sample_catalog_file))
    
    # Verify catalog was loaded
    assert service._catalog is not None
    assert len(service._catalog.texts) == 4
    
    # Verify indexes were built
    assert len(service._texts_by_path) == 4
    assert len(service._authors) == 2
    assert len(service._languages) == 2
    
    # Check that authors were extracted correctly
    assert "Diogenes Laertius" in service._authors
    assert "Herodotus" in service._authors
    
    # Check that languages were extracted correctly
    assert "Greek" in service._languages
    assert "English" in service._languages


def test_transform_hierarchical_to_flat(sample_catalog_data: Dict[str, Any], expected_texts: List[Text]) -> None:
    """Test transforming hierarchical catalog to flat list of Text objects."""
    service = CatalogService()
    
    # Transform the hierarchical data
    texts = service._transform_hierarchical_to_flat(sample_catalog_data)
    
    # Verify the correct number of texts were created
    assert len(texts) == 4
    
    # Compare each transformed text with the expected result
    for transformed, expected in zip(sorted(texts, key=lambda t: t.path), sorted(expected_texts, key=lambda t: t.path)):
        assert transformed.path == expected.path
        assert transformed.title == expected.title
        assert transformed.author == expected.author
        assert transformed.language == expected.language
        
        # Check that metadata contains expected fields
        for key, value in expected.metadata.items():
            assert key in transformed.metadata
            assert transformed.metadata[key] == value


def test_get_text_by_path(mock_catalog_service: CatalogService) -> None:
    """Test getting a text by its path."""
    # Test getting an existing text
    text = mock_catalog_service.get_text_by_path("tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml")
    assert text is not None
    assert text.path == "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    assert text.author == "Diogenes Laertius"
    assert text.title == "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων"
    
    # Test getting a non-existent text
    text = mock_catalog_service.get_text_by_path("nonexistent/path.xml")
    assert text is None


def test_get_texts_by_author(mock_catalog_service: CatalogService) -> None:
    """Test getting texts by author."""
    # Test getting texts for an existing author
    texts = mock_catalog_service.get_texts_by_author("Diogenes Laertius")
    assert len(texts) == 2
    
    # Verify that all returned texts have the correct author
    for text in texts:
        assert text.author == "Diogenes Laertius"
    
    # Test getting texts for a non-existent author
    texts = mock_catalog_service.get_texts_by_author("Nonexistent Author")
    assert len(texts) == 0


def test_get_texts_by_language(mock_catalog_service: CatalogService) -> None:
    """Test getting texts by language."""
    # Test getting texts for an existing language
    texts = mock_catalog_service.get_texts_by_language("Greek")
    assert len(texts) == 2
    
    # Verify that all returned texts have the correct language
    for text in texts:
        assert text.language == "Greek"
    
    # Test getting texts for a non-existent language
    texts = mock_catalog_service.get_texts_by_language("Nonexistent Language")
    assert len(texts) == 0


def test_toggle_favorite(mock_catalog_service: CatalogService, tmp_path: Path) -> None:
    """Test toggling the favorite status of a text."""
    path = "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    
    # Verify initial state
    text = mock_catalog_service.get_text_by_path(path)
    assert text is not None
    assert text.favorite is False
    
    # Toggle favorite status
    success = mock_catalog_service.toggle_favorite(path)
    assert success is True
    
    # Verify updated state
    text = mock_catalog_service.get_text_by_path(path)
    assert text.favorite is True
    
    # Toggle again
    success = mock_catalog_service.toggle_favorite(path)
    assert success is True
    
    # Verify updated state
    text = mock_catalog_service.get_text_by_path(path)
    assert text.favorite is False
    
    # Test toggling a non-existent text
    success = mock_catalog_service.toggle_favorite("nonexistent/path.xml")
    assert success is False


def test_set_archived(mock_catalog_service: CatalogService) -> None:
    """Test setting the archived status of a text."""
    path = "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    
    # Verify initial state
    text = mock_catalog_service.get_text_by_path(path)
    assert text is not None
    assert text.archived is False
    
    # Set archived status
    success = mock_catalog_service.set_archived(path, True)
    assert success is True
    
    # Verify updated state
    text = mock_catalog_service.get_text_by_path(path)
    assert text.archived is True
    
    # Test that archived texts are excluded by default
    all_texts = mock_catalog_service.get_all_texts()
    assert len(all_texts) == 3
    
    # Test including archived texts
    all_texts = mock_catalog_service.get_all_texts(include_archived=True)
    assert len(all_texts) == 4
    
    # Test setting archived for a non-existent text
    success = mock_catalog_service.set_archived("nonexistent/path.xml", True)
    assert success is False


def test_search_texts(mock_catalog_service: CatalogService) -> None:
    """Test searching for texts by title or author."""
    # Search by author
    results = mock_catalog_service.search_texts("Diogenes")
    assert len(results) == 2
    
    # Search by title
    results = mock_catalog_service.search_texts("Histories")
    assert len(results) == 1
    assert results[0].title == "Histories"
    
    # Search with no results
    results = mock_catalog_service.search_texts("Nonexistent")
    assert len(results) == 0
    
    # Search with empty query
    results = mock_catalog_service.search_texts("")
    assert len(results) == 0


def test_catalog_with_missing_file(tmp_path: Path) -> None:
    """Test error handling when catalog file is missing."""
    nonexistent_file = tmp_path / "nonexistent.json"
    
    # Verify that attempting to load a nonexistent catalog raises an error
    with pytest.raises(FileNotFoundError):
        CatalogService(catalog_path=str(nonexistent_file))


def test_catalog_with_invalid_json(tmp_path: Path) -> None:
    """Test error handling when catalog file contains invalid JSON."""
    invalid_file = tmp_path / "invalid.json"
    
    # Create a file with invalid JSON
    with open(invalid_file, "w") as f:
        f.write("This is not valid JSON")
    
    # Verify that attempting to load invalid JSON raises an error
    with pytest.raises(ValueError):
        CatalogService(catalog_path=str(invalid_file))


def test_save_catalog(mock_catalog_service: CatalogService, tmp_path: Path) -> None:
    """Test saving the catalog to a file."""
    output_file = tmp_path / "output_catalog.json"
    
    # Replace the catalog path
    mock_catalog_service.catalog_path = output_file
    
    # Save the catalog
    success = mock_catalog_service.save_catalog()
    assert success is True
    assert output_file.exists()
    
    # Load the saved catalog and verify contents
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Verify that the saved catalog contains the expected number of texts
    assert len(data["texts"]) == 4 