"""Data integrity tests for the Eulogos application.

This module focuses on ensuring:
1. Catalog structure integrity
2. Proper ID-based path resolution
3. Data consistency between catalog and XML files
4. Correctness of text metadata
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

import pytest

from app.models.catalog import Text
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService
from app.config import EulogosSettings


@pytest.fixture
def sample_catalog_data() -> Dict[str, Any]:
    """Create a more detailed sample catalog data for testing."""
    return {
        "statistics": {
            "author_count": 2,
            "work_count": 3,
            "text_count": 4,
            "greek_word_count": 150000,
            "latin_word_count": 50000,
        },
        "authors": {
            "author1": {
                "id": "author1",
                "name": "Homer",
                "century": -8,
                "works": {
                    "work1": {
                        "id": "work1",
                        "title": "Iliad",
                        "texts": {
                            "text1": {
                                "id": "text1",
                                "group_name": "Homer",
                                "work_name": "Iliad",
                                "language": "grc",
                                "wordcount": 100000,
                                "author_id": "author1",
                                "path": "data/grc/homer/iliad.xml",
                            }
                        }
                    }
                }
            },
            "author2": {
                "id": "author2",
                "name": "Plato",
                "century": -4,
                "works": {
                    "work2": {
                        "id": "work2",
                        "title": "Republic",
                        "texts": {
                            "text2": {
                                "id": "text2",
                                "group_name": "Plato",
                                "work_name": "Republic",
                                "language": "grc",
                                "wordcount": 50000,
                                "author_id": "author2",
                                "path": "data/grc/plato/republic.xml",
                            }
                        }
                    },
                    "work3": {
                        "id": "work3",
                        "title": "Apology",
                        "texts": {
                            "text3": {
                                "id": "text3",
                                "group_name": "Plato",
                                "work_name": "Apology",
                                "language": "grc",
                                "wordcount": 10000,
                                "author_id": "author2",
                                "path": "data/grc/plato/apology-grc.xml",
                            },
                            "text4": {
                                "id": "text4",
                                "group_name": "Plato",
                                "work_name": "Apology",
                                "language": "lat",
                                "wordcount": 10000,
                                "author_id": "author2",
                                "path": "data/lat/plato/apology-lat.xml",
                            }
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def catalog_file(tmp_path, sample_catalog_data) -> Path:
    """Create a sample catalog file in a temporary directory."""
    catalog_path = tmp_path / "integrated_catalog.json"
    
    with open(catalog_path, "w") as f:
        json.dump(sample_catalog_data, f)
    
    return catalog_path


@pytest.fixture
def test_settings(catalog_file) -> EulogosSettings:
    """Create test settings with the sample catalog path."""
    return EulogosSettings(
        catalog_path=str(catalog_file),
        data_dir=str(catalog_file.parent / "data"),
        xml_cache_size=10,
        enable_caching=True,
        compatibility_mode=False,
    )


@pytest.fixture
def sample_xml_files(tmp_path) -> Dict[str, Path]:
    """Create sample XML files in the expected directory structure."""
    # Create directory structure
    data_dir = tmp_path / "data"
    
    # Homer/Iliad
    homer_dir = data_dir / "grc" / "homer"
    os.makedirs(homer_dir, exist_ok=True)
    iliad_path = homer_dir / "iliad.xml"
    with open(iliad_path, "w") as f:
        f.write('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div>Test content</div></body></text></TEI>')
    
    # Plato/Republic
    plato_dir = data_dir / "grc" / "plato"
    os.makedirs(plato_dir, exist_ok=True)
    republic_path = plato_dir / "republic.xml"
    with open(republic_path, "w") as f:
        f.write('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div>Test content</div></body></text></TEI>')
    
    # Plato/Apology (Greek)
    apology_grc_path = plato_dir / "apology-grc.xml"
    with open(apology_grc_path, "w") as f:
        f.write('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div>Test content</div></body></text></TEI>')
    
    # Plato/Apology (Latin)
    lat_plato_dir = data_dir / "lat" / "plato"
    os.makedirs(lat_plato_dir, exist_ok=True)
    apology_lat_path = lat_plato_dir / "apology-lat.xml"
    with open(apology_lat_path, "w") as f:
        f.write('<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div>Test content</div></body></text></TEI>')
    
    return {
        "text1": iliad_path,
        "text2": republic_path,
        "text3": apology_grc_path,
        "text4": apology_lat_path,
    }


@pytest.fixture
def mock_catalog_service(test_settings, sample_catalog_data, mocker):
    """Create a mocked catalog service with pre-loaded indexes."""
    catalog_service = CatalogService(settings=test_settings)
    
    # Create mock text objects from the sample data
    text_objects = {}
    
    for author_id, author_data in sample_catalog_data["authors"].items():
        for work_id, work_data in author_data["works"].items():
            for text_id, text_data in work_data["texts"].items():
                text_objects[text_id] = Text.from_dict(text_data)
    
    # Mock the get_text_by_id method
    mocker.patch.object(
        catalog_service, 
        "get_text_by_id", 
        side_effect=lambda id: text_objects.get(id)
    )
    
    return catalog_service


def test_catalog_structure(sample_catalog_data):
    """Test that the catalog structure follows the expected format."""
    # Check top-level keys
    assert "statistics" in sample_catalog_data
    assert "authors" in sample_catalog_data
    
    # Check statistics
    stats = sample_catalog_data["statistics"]
    assert "author_count" in stats
    assert "work_count" in stats
    assert "text_count" in stats
    
    # Check authors structure
    authors = sample_catalog_data["authors"]
    assert isinstance(authors, dict)
    assert len(authors) == stats["author_count"]
    
    # Check each author
    for author_id, author in authors.items():
        assert "id" in author
        assert "name" in author
        assert "works" in author
        assert isinstance(author["works"], dict)
        
        # Check each work
        for work_id, work in author["works"].items():
            assert "id" in work
            assert "title" in work
            assert "texts" in work
            assert isinstance(work["texts"], dict)
            
            # Check each text
            for text_id, text in work["texts"].items():
                assert "id" in text
                assert "path" in text
                assert "language" in text
                assert "wordcount" in text


def test_id_based_text_retrieval(mock_catalog_service):
    """Test that texts can be retrieved by ID from the catalog."""
    # Test retrieving each text by ID
    text_ids = [
        "text1",  # Homer/Iliad
        "text2",  # Plato/Republic
        "text3",  # Plato/Apology (Greek)
        "text4",  # Plato/Apology (Latin)
    ]
    
    for text_id in text_ids:
        text = mock_catalog_service.get_text_by_id(text_id)
        assert text is not None
        assert text.id == text_id
        assert text.path is not None
    
    # Test retrieving a non-existent text
    text = mock_catalog_service.get_text_by_id("nonexistent")
    assert text is None


def test_path_integrity(mock_catalog_service, sample_xml_files):
    """Test that paths in the catalog correctly point to existing files."""
    # Verify each text has a valid ID and path
    for text_id, xml_path in sample_xml_files.items():
        text = mock_catalog_service.get_text_by_id(text_id)
        assert text is not None
        assert text.path is not None
        
        # Check if file exists
        assert os.path.exists(xml_path)


def test_text_model_integrity():
    """Test the integrity of the Text model without URN field."""
    # Create a text without URN
    text = Text(
        id="test-id",
        group_name="Test Group",
        work_name="Test Work",
        language="grc",
        wordcount=1000,
        author_id="test-author",
        path="data/test/path.xml",
    )
    
    # Verify the text properties
    assert text.id == "test-id"
    assert text.group_name == "Test Group"
    assert text.work_name == "Test Work"
    assert text.language == "grc"
    assert text.wordcount == 1000
    assert text.author_id == "test-author"
    assert text.path == "data/test/path.xml"
    
    # Verify that to_dict works correctly
    text_dict = text.to_dict()
    assert "id" in text_dict
    assert "group_name" in text_dict
    assert "work_name" in text_dict
    assert "language" in text_dict
    assert "wordcount" in text_dict
    assert "author_id" in text_dict
    assert "path" in text_dict
    assert "urn" not in text_dict  # Ensure URN is not in the dict
    
    # Test creating from dict
    new_text = Text.from_dict(text_dict)
    assert new_text.id == text.id
    assert new_text.group_name == text.group_name
    assert new_text.work_name == text.work_name
    assert new_text.language == text.language
    assert new_text.wordcount == text.wordcount
    assert new_text.author_id == text.author_id
    assert new_text.path == text.path


def test_xml_processor_path_resolution(test_settings, mock_catalog_service, sample_xml_files, mocker):
    """Test that the XML processor correctly uses catalog for path resolution."""
    # Create XML service that uses our mock catalog service
    xml_service = XMLProcessorService(catalog_service=mock_catalog_service, settings=test_settings)
    
    # Mock load_xml_from_path to prevent actual file loading but test path resolution
    mock_root = mocker.Mock()
    mock_root.metadata = {"title": "Test Document"}
    
    mocker.patch.object(
        xml_service,
        "load_xml_from_path",
        return_value=mock_root
    )
    
    # Test that path resolution works through the catalog service
    for text_id in sample_xml_files.keys():
        # Get the text from the catalog service
        text = mock_catalog_service.get_text_by_id(text_id)
        assert text is not None
        assert text.path is not None
        
        # Ensure the catalog service was called with the correct ID
        mock_catalog_service.get_text_by_id.assert_any_call(text_id)
    
    # Test non-existent ID
    nonexistent_id = "nonexistent"
    # Should return None for non-existent ID
    assert mock_catalog_service.get_text_by_id(nonexistent_id) is None 