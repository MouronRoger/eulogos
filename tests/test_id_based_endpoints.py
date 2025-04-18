"""Tests for ID-based endpoints.

This module contains tests for the ID-based endpoints in the Eulogos application.
"""

import json
from typing import Dict, Any
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.models.catalog import Text
from app.services.catalog_service import CatalogService
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService
from app.main import app
from app.dependencies import get_enhanced_catalog_service, get_enhanced_xml_service


@pytest.fixture
def client():
    """Create a test client for the application."""
    return TestClient(app)


@pytest.fixture
def mock_catalog_service(mocker):
    """Create a mock catalog service with sample texts."""
    mock_service = mocker.Mock(spec=EnhancedCatalogService)
    
    # Create sample texts
    sample_texts = {
        "text1": Text(
            id="text1",
            group_name="Homer",
            work_name="Iliad",
            language="grc",
            wordcount=100000,
            author_id="auth1",
            path="data/grc/homer/iliad.xml",
        ),
        "text2": Text(
            id="text2",
            group_name="Plato",
            work_name="Republic",
            language="grc",
            wordcount=80000,
            author_id="auth2",
            path="data/grc/plato/republic.xml",
        ),
        "invalid_path": Text(
            id="invalid_path",
            group_name="Test",
            work_name="Invalid Path",
            language="test",
            wordcount=1000,
            author_id="auth_test",
            path=None,  # Missing path for testing
        ),
    }
    
    # Configure the mock to return appropriate texts
    mock_service.get_text_by_id.side_effect = lambda id: sample_texts.get(id)
    
    return mock_service


@pytest.fixture
def mock_xml_service(mocker):
    """Create a mock XML service."""
    mock_service = mocker.Mock(spec=EnhancedXMLService)
    
    # Create a mock document
    mock_document = mocker.Mock()
    
    # Configure the mock methods that actually exist in EnhancedXMLService
    
    # Mock load_xml_from_path
    def mock_load_xml_from_path(path):
        if path is None:
            raise ValueError("Text has no associated file path")
        if "nonexistent" in str(path):
            raise ValueError("File not found")
        return mock_document
    
    mock_service.load_xml_from_path.side_effect = mock_load_xml_from_path
    
    # Configure metadata extraction
    mock_service.extract_metadata.return_value = {
        "title": "Mock Document Title",
        "author": "Mock Author",
        "language": "grc",
    }
    
    # Configure reference extraction
    mock_service.extract_references.return_value = ["1.1", "1.2", "1.3"]
    
    # Configure document statistics
    mock_service.get_document_statistics.return_value = {
        "element_count": 100,
        "text_length": 5000,
        "word_count": 1000,
        "reference_count": 3,
    }
    
    # Configure passage retrieval
    def get_passage_by_reference(doc, ref):
        if ref == "invalid":
            return None
        return mocker.Mock()  # Mock Element
    
    mock_service.get_passage_by_reference.side_effect = get_passage_by_reference
    
    # Configure format conversions
    mock_service.transform_element_to_html.return_value = "<p>Mock HTML content</p>"
    mock_service.extract_text_from_element.return_value = "Mock text content"
    mock_service.serialize_element.return_value = "<element>Mock XML</element>"
    
    # Add transform_to_html which is used by the endpoints
    mock_service.transform_to_html.return_value = "<div>Mock HTML content</div>"
    
    # Add get_adjacent_references
    mock_service.get_adjacent_references.return_value = {"prev": "1.0", "next": "1.2"}
    
    # Add a method to simulate load_document_by_id
    def load_document_by_id(text_id):
        # This simulates the behavior of loading a document by ID
        return mock_document
        
    # Attach it directly to the mock
    mock_service.load_document_by_id = load_document_by_id
    
    return mock_service


@pytest.fixture
def app_with_mocks(monkeypatch, mock_catalog_service, mock_xml_service):
    """Configure app with mocked dependencies."""
    # Monkeypatch dependency functions to return our mocks
    monkeypatch.setattr("app.dependencies.get_enhanced_catalog_service", lambda: mock_catalog_service)
    monkeypatch.setattr("app.dependencies.get_enhanced_xml_service", lambda: mock_xml_service)
    
    # Also monkeypatch directly in router modules
    monkeypatch.setattr("app.routers.v2.reader.get_enhanced_catalog_service", lambda: mock_catalog_service)
    monkeypatch.setattr("app.routers.v2.reader.get_enhanced_xml_service", lambda: mock_xml_service)
    
    # Return the app with mocked dependencies
    return app


@pytest.fixture
def client_with_mocks(app_with_mocks):
    """Create a test client with mocked dependencies."""
    return TestClient(app_with_mocks)


def test_read_text_by_id(client_with_mocks):
    """Test reading a text by ID."""
    # Test successful retrieval
    response = client_with_mocks.get("/read/id/text1")
    assert response.status_code == 200
    
    # Test with reference parameter
    response = client_with_mocks.get("/read/id/text1?reference=1.1")
    assert response.status_code == 200
    
    # Test with non-existent ID
    response = client_with_mocks.get("/read/id/nonexistent")
    assert response.status_code == 404
    
    # Test with text that has no path
    response = client_with_mocks.get("/read/id/invalid_path") 
    assert response.status_code in [404, 500]  # Either not found or error is acceptable


def test_document_info_by_id(client_with_mocks):
    """Test getting document info by ID."""
    # Test successful retrieval
    response = client_with_mocks.get("/document/id/text1")
    assert response.status_code == 200
    data = response.json()
    assert data["text_id"] == "text1"
    assert "metadata" in data
    assert "statistics" in data
    
    # Test with non-existent ID
    response = client_with_mocks.get("/document/id/nonexistent")
    assert response.status_code == 404
    
    # Test with text that has no path
    response = client_with_mocks.get("/document/id/invalid_path")
    assert response.status_code in [404, 500]  # Either not found or error is acceptable


def test_passage_by_id(client_with_mocks):
    """Test getting passage by ID and reference."""
    # Test successful retrieval with HTML format
    response = client_with_mocks.get("/passage/id/text1?reference=1.1&format=html")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    # Test with text format
    response = client_with_mocks.get("/passage/id/text1?reference=1.1&format=text")
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "reference" in data
    
    # Test with XML format
    response = client_with_mocks.get("/passage/id/text1?reference=1.1&format=xml")
    assert response.status_code == 200
    data = response.json()
    assert "xml" in data
    
    # Test with invalid format
    response = client_with_mocks.get("/passage/id/text1?reference=1.1&format=invalid")
    assert response.status_code == 400
    
    # Test with invalid reference
    response = client_with_mocks.get("/passage/id/text1?reference=invalid&format=html")
    assert response.status_code == 404
    
    # Test with non-existent ID
    response = client_with_mocks.get("/passage/id/nonexistent?reference=1.1&format=html")
    assert response.status_code in [404, 500]  # Either not found or error is acceptable 