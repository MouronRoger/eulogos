"""Integration tests for the Eulogos application."""

from pathlib import Path
from unittest.mock import Mock, MagicMock
from xml.etree.ElementTree import Element

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_catalog_service, get_xml_service, get_export_service
from app.middleware.security import get_current_user
from app.models.catalog import Text
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService
from app.services.export_service import ExportService


@pytest.fixture
def sample_text():
    """Create a sample text for testing."""
    return Text(
        id="sample-text-1",
        group_name="Test Group",
        work_name="Test Work",
        language="grc",
        wordcount=1000,
        author_id="author1",
        path="test_path.xml"
    )


@pytest.fixture
def mock_catalog_service(sample_text):
    """Create a mock catalog service."""
    service = Mock(spec=CatalogService)
    
    def get_text_by_id(text_id):
        if text_id == sample_text.id:
            return sample_text
        if text_id == "text1":
            return sample_text  # Return sample text for test1 as well
        return None
    
    service.get_text_by_id.side_effect = get_text_by_id
    service.get_all_authors.return_value = [{
        "id": "author1",
        "name": "Test Author",
        "works": [sample_text.id],
        "century": 1,
        "type": "ancient"
    }]
    
    return service


@pytest.fixture
def mock_xml_service():
    """Create a mock XML service."""
    service = Mock(spec=XMLProcessorService)
    
    # Create proper Element objects for references
    def create_mock_element(text="Test content", tag="{http://www.tei-c.org/ns/1.0}div", **attrs):
        element = MagicMock()
        element.tag = tag
        element.text = text
        element.tail = None
        element.attrib = attrs
        element.__iter__.return_value = iter([])
        element.get = lambda key, default=None: attrs.get(key, default)
        element.find = lambda _: None
        element.findall = lambda _: []
        element.items = lambda: list(attrs.items())
        return element
    
    # Mock XML root
    root = create_mock_element()
    service.load_xml_from_path.return_value = root
    
    # Mock HTML transformation
    service.transform_to_html.return_value = "<div>Test content</div>"
    service._process_element_to_html.return_value = "<div>Test content</div>"
    
    # Create references dictionary with proper structure
    references = {
        "1": create_mock_element("Book 1", n="1", type="book"),
        "1.1": create_mock_element("Line 1", "{http://www.tei-c.org/ns/1.0}l", n="1"),
        "1.2": create_mock_element("Line 2", "{http://www.tei-c.org/ns/1.0}l", n="2"),
        "1.3": create_mock_element("Line 3", "{http://www.tei-c.org/ns/1.0}l", n="3")
    }
    service.extract_references.return_value = references
    
    # Mock passage retrieval with proper reference handling
    def get_passage_by_reference(root, ref):
        if ref in references:
            return references[ref]
        return None
    
    service.get_passage_by_reference.side_effect = get_passage_by_reference
    
    # Mock adjacent references with proper handling
    def get_adjacent(root, ref):
        ref_keys = sorted(list(references.keys()))
        try:
            idx = ref_keys.index(ref)
            prev_ref = ref_keys[idx - 1] if idx > 0 else None
            next_ref = ref_keys[idx + 1] if idx < len(ref_keys) - 1 else None
            return {"prev": prev_ref, "next": next_ref}
        except ValueError:
            return {"prev": None, "next": None}
    
    service.get_adjacent_references.side_effect = get_adjacent
    
    return service


@pytest.fixture
def mock_export_service(tmp_path):
    """Create a mock export service."""
    service = Mock(spec=ExportService)
    export_path = tmp_path / "export.html"
    with open(export_path, "w") as f:
        f.write("<html><body>Test export</body></html>")
    
    # Mock all export methods to return the same path
    service.export_to_html.return_value = export_path
    service.export_to_markdown.return_value = export_path
    service.export_to_latex.return_value = export_path
    service.export_to_pdf.return_value = export_path
    service.export_to_epub.return_value = export_path
    
    return service


@pytest.fixture
def client(mock_catalog_service, mock_xml_service, mock_export_service):
    """Configure test client with mocked dependencies."""
    # Mock authentication middleware
    def mock_get_current_user():
        return {"id": "test_user", "scopes": ["export:texts"]}
    
    app.dependency_overrides[get_catalog_service] = lambda: mock_catalog_service
    app.dependency_overrides[get_xml_service] = lambda: mock_xml_service
    app.dependency_overrides[get_export_service] = lambda: mock_export_service
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    yield TestClient(app)
    app.dependency_overrides = {}


def test_complete_text_access_workflow(client, sample_text):
    """Test the complete workflow from catalog access to text display."""
    # Test text reading endpoint
    response = client.get(f"/api/v2/read/{sample_text.id}")
    assert response.status_code == 200
    assert "Test content" in response.text

    # Test document info endpoint
    response = client.get(f"/api/v2/document/{sample_text.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Test passage endpoint
    response = client.get(f"/api/v2/passage/{sample_text.id}/1.1")
    assert response.status_code == 200
    assert "Test content" in response.text


async def test_export_workflow(client, mock_catalog_service, mock_xml_service, mock_export_service, sample_text):
    """Test the complete export workflow."""
    # First get the document
    response = await client.get(f"/read/document/{sample_text.id}")
    assert response.status_code == 200
    
    # Then request the export
    export_format = "pdf"
    response = await client.post(
        f"/read/export/{sample_text.id}",
        json={"format": export_format}
    )
    assert response.status_code == 200
    
    # Mock export service should have been called with correct parameters
    mock_export_service.export_text.assert_called_once_with(
        text_id=sample_text.id,
        format=export_format
    )


def test_reference_navigation(client, sample_text):
    """Test reference navigation using ID-based access."""
    # Test references endpoint
    response = client.get(f"/api/v2/references/{sample_text.id}")
    assert response.status_code == 200
    data = response.json()
    assert "references" in data
    assert len(data["references"]) > 0

    # Test passage navigation
    response = client.get(f"/api/v2/passage/{sample_text.id}/1.1")
    assert response.status_code == 200
    assert "Test content" in response.text


def test_catalog_integrity(client, sample_text):
    """Test catalog integrity and text metadata."""
    # Test text metadata
    response = client.get(f"/api/v2/document/{sample_text.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_error_handling(client):
    """Test error handling for invalid IDs and missing paths."""
    # Test with non-existent ID
    response = client.get("/api/v2/read/nonexistent")
    assert response.status_code == 404

    # Test with invalid reference
    response = client.get("/api/v2/passage/text1/invalid")
    assert response.status_code == 404


