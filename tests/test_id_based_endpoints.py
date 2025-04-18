"""Integration tests for ID-based endpoints."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_catalog_service, get_xml_service
from app.models.catalog import Text
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService


@pytest.fixture
def mock_catalog_service():
    """Create a mock catalog service."""
    service = Mock(spec=CatalogService)
    text = Text(
        id="text1",
        path="test_path.xml",
        language="grc",
        author_id="author1",
        group_name="Test Group",
        work_name="Test Work",
        wordcount=1000
    )
    service.get_text_by_id.return_value = text
    service.get_all_authors.return_value = [{
        "id": "author1",
        "name": "Test Author",
        "works": ["text1"]
    }]
    return service


@pytest.fixture
def mock_xml_service():
    """Create a mock XML service."""
    service = Mock(spec=XMLProcessorService)
    service.load_xml_from_path.return_value = Mock()
    service.transform_to_html.return_value = "<div>Test content</div>"
    service.get_passage_by_reference.return_value = Mock()
    service.extract_references.return_value = {"1": Mock(), "1.1": Mock(), "1.2": Mock()}
    service.get_adjacent_references.return_value = {"prev": "1.1", "next": "1.3"}
    return service


@pytest.fixture
def client_with_mocks(mock_catalog_service, mock_xml_service):
    """Configure test client with mocked dependencies."""
    app.dependency_overrides[get_catalog_service] = lambda: mock_catalog_service
    app.dependency_overrides[get_xml_service] = lambda: mock_xml_service
    yield TestClient(app)
    app.dependency_overrides = {}


def test_read_text_by_id(client_with_mocks):
    """Test reading a text by ID."""
    # Test successful retrieval
    response = client_with_mocks.get("/api/v2/read/text1")
    assert response.status_code == 200
    assert "Test content" in response.text

    # Test with reference
    response = client_with_mocks.get("/api/v2/read/text1?reference=1.1")
    assert response.status_code == 200
    assert "Test content" in response.text


def test_document_info_by_id(client_with_mocks):
    """Test getting document info by ID."""
    # Test successful retrieval
    response = client_with_mocks.get("/api/v2/document/text1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_passage_by_id(client_with_mocks):
    """Test getting passage by ID and reference."""
    # Test successful retrieval with HTML format
    response = client_with_mocks.get("/api/v2/passage/text1/1.1")
    assert response.status_code == 200
    assert "Test content" in response.text 