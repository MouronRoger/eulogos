"""Integration tests for reader with reference navigation."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.reader import get_catalog_service, get_xml_processor
from app.services.xml_processor_service import XMLProcessorService


@pytest.fixture
def mock_xml_processor():
    """Create a mock XMLProcessorService."""
    processor = MagicMock(spec=XMLProcessorService)

    # Mock load_xml to return a mock XML root
    processor.load_xml.return_value = MagicMock()

    # Mock extract_references to return a mock references dict
    references = {"1": MagicMock(), "1.1": MagicMock(), "1.2": MagicMock()}
    processor.extract_references.return_value = references

    # Mock get_adjacent_references to return mock prev/next refs
    processor.get_adjacent_references.return_value = {"prev": "1.1", "next": "1.3"}

    # Mock transform_to_html to return a simple HTML string
    processor.transform_to_html.return_value = "<div>Test content</div>"

    return processor


@pytest.fixture
def client(mock_xml_processor):
    """Create a test client with mocked dependencies."""
    app.dependency_overrides[get_xml_processor] = lambda: mock_xml_processor

    # Also mock catalog_service to return a dummy text
    mock_catalog = MagicMock()
    mock_catalog.get_text_by_urn.return_value = {
        "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
        "group_name": "Homer",
        "work_name": "Iliad",
        "language": "grc",
    }
    app.dependency_overrides[get_catalog_service] = lambda: mock_catalog

    yield TestClient(app)
    app.dependency_overrides = {}


class TestReaderReferenceNavigation:
    """Tests for reader reference navigation."""

    def test_read_text_with_reference(self, client, mock_xml_processor):
        """Test reading a text with a specific reference."""
        response = client.get("/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.2")

        assert response.status_code == 200

        # Check that the correct methods were called
        mock_xml_processor.load_xml.assert_called_once()
        mock_xml_processor.get_adjacent_references.assert_called_once_with(
            mock_xml_processor.load_xml.return_value, "1.2"
        )
        mock_xml_processor.transform_to_html.assert_called_once_with(mock_xml_processor.load_xml.return_value, "1.2")

        # Check that the response contains navigation elements
        html = response.text
        assert "Currently viewing: <strong>1.2</strong>" in html
        assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.1"' in html
        assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.3"' in html

    def test_get_references(self, client, mock_xml_processor):
        """Test the references API endpoint."""
        response = client.get("/api/references/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

        assert response.status_code == 200

        # Check that the correct methods were called
        mock_xml_processor.load_xml.assert_called_once()
        mock_xml_processor.extract_references.assert_called_once_with(mock_xml_processor.load_xml.return_value)

        # Check that the response contains reference links
        html = response.text
        assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1"' in html
        assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.1"' in html
        assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.2"' in html
