"""Tests for the SimpleCatalogService."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.simple_catalog_service import SimpleCatalogService


@pytest.fixture
def sample_catalog_data():
    """Provide a sample catalog data structure."""
    return {
        "tlg0012": {
            "name": "Homer",
            "century": -8,
            "type": "poetry",
            "works": {
                "tlg001": {
                    "title": "Iliad",
                    "urn": "urn:cts:greekLit:tlg0012.tlg001",
                    "editions": {
                        "perseus-grc1": {
                            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
                            "language": "grc",
                            "word_count": 112016,
                            "path": "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml",
                        }
                    },
                    "translations": {
                        "perseus-eng1": {
                            "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-eng1",
                            "language": "eng",
                            "word_count": 150000,
                            "path": "tlg0012/tlg001/tlg0012.tlg001.perseus-eng1.xml",
                        }
                    },
                }
            },
        }
    }


@pytest.fixture
def mock_catalog_service(sample_catalog_data, tmp_path):
    """Create a mock catalog service with sample data."""
    # Create a temporary catalog file
    catalog_path = tmp_path / "test_catalog.json"
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(sample_catalog_data, f)

    # Create a data directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)

    author_dir = data_dir / "tlg0012"
    author_dir.mkdir(exist_ok=True)

    work_dir = author_dir / "tlg001"
    work_dir.mkdir(exist_ok=True)

    # Create mock text files
    greek_file = work_dir / "tlg0012.tlg001.perseus-grc1.xml"
    greek_file.write_text("<xml>Greek text</xml>")

    english_file = work_dir / "tlg0012.tlg001.perseus-eng1.xml"
    english_file.write_text("<xml>English translation</xml>")

    # Create and return the service
    service = SimpleCatalogService(catalog_path=str(catalog_path), data_dir=str(data_dir))

    return service


def test_init():
    """Test initialization with default values."""
    service = SimpleCatalogService()
    assert service.catalog_path == Path("integrated_catalog.json")
    assert service.data_dir == Path("data")
    assert service._catalog_data is None
    assert service._unified_catalog is None


def test_load_catalog(mock_catalog_service, sample_catalog_data):
    """Test loading the catalog from file."""
    catalog = mock_catalog_service.load_catalog()
    assert catalog == sample_catalog_data
    assert mock_catalog_service._catalog_data == sample_catalog_data
    assert mock_catalog_service._unified_catalog is not None


def test_resolve_urn_to_path(mock_catalog_service):
    """Test resolving URN to file path."""
    mock_catalog_service.load_catalog()

    # Test with URN in catalog
    path = mock_catalog_service.resolve_urn_to_path("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    expected_path = mock_catalog_service.data_dir / "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml"
    assert path == expected_path

    # Test with URN not in catalog (uses direct transformation)
    path = mock_catalog_service.resolve_urn_to_path("urn:cts:greekLit:tlg0013.tlg001.perseus-grc1")
    expected_path = mock_catalog_service.data_dir / "tlg0013/tlg001/tlg0013.tlg001.perseus-grc1.xml"
    assert path == expected_path


def test_get_text_by_urn(mock_catalog_service):
    """Test getting text by URN."""
    mock_catalog_service.load_catalog()

    # Test with existing URN
    text = mock_catalog_service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert text is not None
    assert text.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
    assert text.language == "grc"

    # Test with non-existent URN
    text = mock_catalog_service.get_text_by_urn("urn:cts:greekLit:tlg9999.tlg999.unknown")
    assert text is None


def test_get_texts_by_author(mock_catalog_service):
    """Test getting texts by author."""
    mock_catalog_service.load_catalog()

    texts = mock_catalog_service.get_texts_by_author("tlg0012")
    assert len(texts) == 2  # Greek original and English translation

    # Check we have both the Greek and English versions
    languages = {text.language for text in texts}
    assert languages == {"grc", "eng"}


def test_archive_and_favorite(mock_catalog_service):
    """Test archiving and favoriting texts."""
    mock_catalog_service.load_catalog()

    # Test archiving
    with patch.object(mock_catalog_service, "_save_catalog", return_value=True):
        result = mock_catalog_service.archive_text("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1", True)
        assert result is True

        text = mock_catalog_service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        assert text.archived is True

        # Unarchive
        result = mock_catalog_service.archive_text("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1", False)
        assert result is True
        assert text.archived is False

    # Test favoriting
    with patch.object(mock_catalog_service, "_save_catalog", return_value=True):
        result = mock_catalog_service.favorite_text("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1", True)
        assert result is True

        text = mock_catalog_service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        assert text.favorite is True

        # Toggle favorite
        result = mock_catalog_service.toggle_favorite("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        assert result is False  # Because _save_catalog returns True, toggle returns False (new state)
        assert text.favorite is False
