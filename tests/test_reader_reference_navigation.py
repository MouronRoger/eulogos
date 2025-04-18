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

    