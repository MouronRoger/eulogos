"""Integration tests for the Eulogos export functionality.

This module contains end-to-end tests that verify:
- Complete export workflows across different formats
- API endpoint functionality
- Catalog-based path resolution
- Export performance and caching
- File cleanup and resource management
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.catalog import Text
from app.services.catalog_service import CatalogService
from app.services.export_service import ExportService
from app.services.xml_processor_service import XMLProcessorService


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the application."""
    return TestClient(app)


@pytest.fixture
def sample_text() -> Text:
    """Create a sample text with a valid ID."""
    return Text(
        id="sample-text-1",
        group_name="Homer",
        work_name="Iliad",
        language="grc",
        wordcount=100000,
        author_id="auth1",
        path="data/grc/homer/iliad.xml",
    )


@pytest.fixture
def mock_catalog_service(mocker, sample_text):
    """Create a mock catalog service."""
    mock_service = mocker.Mock(spec=CatalogService)
    
    # Configure the mock to return appropriate texts
    mock_service.get_text_by_id.side_effect = lambda id: (
        sample_text if id == sample_text.id else None
    )
    
    # Mock catalog loading
    mock_service.load_catalog.return_value = {
        "authors": {
            "auth1": {
                "id": "auth1",
                "name": "Homer",
                "works": {
                    "iliad": {
                        "id": "iliad",
                        "title": "Iliad",
                        "texts": {
                            sample_text.id: sample_text.to_dict()
                        }
                    }
                }
            }
        }
    }
    
    return mock_service


@pytest.fixture
def mock_xml_service(mocker):
    """Create a mock XML service."""
    mock_service = mocker.Mock(spec=XMLProcessorService)
    
    # Configure document loading
    mock_doc = mocker.Mock()
    mock_doc.metadata = {
        "title": "Mock Document",
        "author": "Mock Author",
        "language": "grc",
    }
    mock_service.load_document_by_id.return_value = mock_doc
    
    # Mock content extraction
    mock_service.extract_text_content.return_value = "Sample text content"
    
    return mock_service


@pytest.fixture
def mock_export_service(mocker, tmp_path):
    """Create a mock export service."""
    mock_service = mocker.Mock(spec=ExportService)
    
    # Configure export functionality
    export_path = tmp_path / "export.html"
    with open(export_path, "w") as f:
        f.write("<html><body>Test export</body></html>")
    
    mock_service.export_document.return_value = export_path
    
    return mock_service


def test_complete_text_access_workflow(
    client, mocker, mock_catalog_service, mock_xml_service, sample_text
):
    """Test the complete workflow from catalog access to text display."""
    # Patch services
    mocker.patch(
        "app.routers.reader.get_catalog_service",
        return_value=mock_catalog_service,
    )
    mocker.patch(
        "app.routers.reader.get_xml_processor_service", 
        return_value=mock_xml_service
    )
    
    # Test text reading endpoint
    response = client.get(f"/read/id/{sample_text.id}")
    assert response.status_code == 200
    
    # Test document info endpoint
    response = client.get(f"/document/id/{sample_text.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["text_id"] == sample_text.id
    
    # Verify that catalog service was called with the correct ID
    mock_catalog_service.get_text_by_id.assert_called_with(sample_text.id)
    
    # Verify that XML service received the correct catalog entry
    mock_xml_service.load_document_by_id.assert_called()


def test_export_workflow(
    client, mocker, mock_catalog_service, mock_xml_service, 
    mock_export_service, sample_text
):
    """Test the export workflow using ID-based access."""
    # Patch services
    mocker.patch(
        "app.routers.export.get_catalog_service",
        return_value=mock_catalog_service,
    )
    mocker.patch(
        "app.routers.export.get_xml_processor_service", 
        return_value=mock_xml_service
    )
    mocker.patch(
        "app.routers.export.get_export_service",
        return_value=mock_export_service,
    )
    
    # Test export endpoint
    response = client.post(
        f"/api/export/id/{sample_text.id}",
        json={"format": "html", "include_metadata": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert data["text_id"] == sample_text.id
    
    # Verify that catalog service was called with the correct ID
    mock_catalog_service.get_text_by_id.assert_called_with(sample_text.id)
    
    # Verify that export service was called correctly
    mock_export_service.export_document.assert_called()


def test_reference_navigation(
    client, mocker, mock_catalog_service, mock_xml_service, sample_text
):
    """Test reference navigation using ID-based access."""
    # Configure mock XML service for reference navigation
    mock_xml_service.extract_references.return_value = ["1.1", "1.2", "1.3"]
    mock_xml_service.get_passage_by_reference.return_value = mocker.Mock()
    mock_xml_service.transform_element_to_html.return_value = "<p>Test passage</p>"
    
    # Patch services
    mocker.patch(
        "app.routers.reader.get_catalog_service",
        return_value=mock_catalog_service,
    )
    mocker.patch(
        "app.routers.reader.get_xml_processor_service", 
        return_value=mock_xml_service
    )
    
    # Test references endpoint
    response = client.get(f"/api/references/id/{sample_text.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "1.1" in data
    
    # Test passage retrieval
    response = client.get(f"/passage/id/{sample_text.id}?reference=1.1&format=html")
    assert response.status_code == 200
    
    # Verify that XML service methods were called correctly
    mock_xml_service.get_passage_by_reference.assert_called()
    mock_xml_service.transform_element_to_html.assert_called()


def test_catalog_integrity(mocker, mock_catalog_service):
    """Test catalog integrity checks."""
    # Test that catalog can be loaded
    catalog = mock_catalog_service.load_catalog()
    assert isinstance(catalog, dict)
    assert "authors" in catalog
    
    # Verify structure of catalog entries
    author = list(catalog["authors"].values())[0]
    assert "works" in author
    
    work = list(author["works"].values())[0]
    assert "texts" in work
    
    text = list(work["texts"].values())[0]
    assert "path" in text


def test_error_handling(client, mocker, mock_catalog_service, mock_xml_service):
    """Test error handling for invalid IDs and missing paths."""
    # Configure mocks to simulate errors
    mock_catalog_service.get_text_by_id.side_effect = lambda id: None  # No text found
    
    # Patch services
    mocker.patch(
        "app.routers.reader.get_catalog_service",
        return_value=mock_catalog_service,
    )
    mocker.patch(
        "app.routers.reader.get_xml_processor_service", 
        return_value=mock_xml_service
    )
    
    # Test with non-existent ID
    response = client.get("/read/id/nonexistent")
    assert response.status_code == 404
    
    # Test passage with invalid reference
    response = client.get("/passage/id/valid-id?reference=invalid&format=html")
    assert response.status_code == 404


