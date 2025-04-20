"""Integration tests for read endpoints.

These tests verify that the read endpoints correctly handle text retrieval
and references, using paths as canonical identifiers.
"""

import pytest
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.models.catalog import Text


def test_read_text(client: TestClient) -> None:
    """Test reading a text by path."""
    text_path = "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    
    # Create mock catalog service and XML service responses
    with patch("app.routers.read.get_catalog_service") as mock_get_catalog, \
         patch("app.routers.read.XMLService") as mock_xml_service_class:
        
        # Mock the catalog service
        mock_catalog_service = mock_get_catalog.return_value
        mock_catalog_service.get_text_by_path.return_value = Text(
            path=text_path,
            title="Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
            author="Diogenes Laertius",
            language="Greek"
        )
        
        # Mock the XML service instance
        mock_xml_service = mock_xml_service_class.return_value
        mock_xml_service.load_xml.return_value = ET.fromstring("<TEI></TEI>")
        mock_xml_service.get_metadata.return_value = {
            "title": "Sample Text",
            "author": "Test Author",
        }
        mock_xml_service.transform_to_html.return_value = "<div>Sample content</div>"
        mock_xml_service.extract_references.return_value = {"1": MagicMock(), "2": MagicMock()}
        
        # Make request to read the text
        response = client.get(f"/read/{text_path}")
        
        # Check response status
        assert response.status_code == 200
        
        # Check that the correct text was requested
        mock_catalog_service.get_text_by_path.assert_called_with(text_path)
        mock_xml_service.load_xml.assert_called_with(text_path)
        
        # Check content
        assert "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων" in response.text
        assert "Diogenes Laertius" in response.text
        assert "Sample content" in response.text


def test_read_text_with_reference(client: TestClient) -> None:
    """Test reading a specific section of a text by reference."""
    text_path = "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    reference = "1.1"
    
    # Create mock catalog service and XML service responses
    with patch("app.routers.read.get_catalog_service") as mock_get_catalog, \
         patch("app.routers.read.XMLService") as mock_xml_service_class:
        
        # Mock the catalog service
        mock_catalog_service = mock_get_catalog.return_value
        mock_catalog_service.get_text_by_path.return_value = Text(
            path=text_path,
            title="Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
            author="Diogenes Laertius",
            language="Greek"
        )
        
        # Mock the XML service instance
        mock_xml_service = mock_xml_service_class.return_value
        mock_xml_service.load_xml.return_value = ET.fromstring("<TEI></TEI>")
        mock_xml_service.get_metadata.return_value = {
            "title": "Sample Text",
            "author": "Test Author",
        }
        mock_xml_service.transform_to_html.return_value = "<div>Section 1.1 content</div>"
        mock_xml_service.extract_references.return_value = {
            "1": MagicMock(),
            "1.1": MagicMock(),
            "1.2": MagicMock()
        }
        mock_xml_service.get_adjacent_references.return_value = {
            "prev": "1",
            "next": "1.2"
        }
        
        # Make request to read the text with reference
        response = client.get(f"/read/{text_path}?reference={reference}")
        
        # Check response status
        assert response.status_code == 200
        
        # Check that the correct text and reference were requested
        mock_catalog_service.get_text_by_path.assert_called_with(text_path)
        mock_xml_service.load_xml.assert_called_with(text_path)
        mock_xml_service.transform_to_html.assert_called_with(mock_xml_service.load_xml.return_value, reference)
        
        # Check content
        assert "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων" in response.text
        assert "Diogenes Laertius" in response.text
        assert "Section 1.1 content" in response.text


def test_read_nonexistent_text(client: TestClient) -> None:
    """Test reading a nonexistent text."""
    text_path = "nonexistent/path.xml"
    
    # Create mock catalog service response
    with patch("app.routers.read.get_catalog_service") as mock_get_catalog:
        # Mock the catalog service to return None for the nonexistent text
        mock_catalog_service = mock_get_catalog.return_value
        mock_catalog_service.get_text_by_path.return_value = None
        
        # Make request to read the nonexistent text
        response = client.get(f"/read/{text_path}")
        
        # Check response status (should be 404)
        assert response.status_code == 404
        
        # Check error message
        assert "not found" in response.text.lower()


def test_get_references(client: TestClient) -> None:
    """Test getting references for a text."""
    text_path = "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    
    # Create mock XML service response
    with patch("app.routers.read.XMLService") as mock_xml_service_class:
        # Mock the XML service instance
        mock_xml_service = mock_xml_service_class.return_value
        mock_xml_service.load_xml.return_value = ET.fromstring("<TEI></TEI>")
        mock_xml_service.extract_references.return_value = {
            "1": MagicMock(),
            "1.1": MagicMock(),
            "1.2": MagicMock(),
            "2": MagicMock(),
            "2.1": MagicMock()
        }
        
        # Make request to get references
        response = client.get(f"/read/references/{text_path}")
        
        # Check response status
        assert response.status_code == 200
        
        # Check that the correct text was requested
        mock_xml_service.load_xml.assert_called_with(text_path)
        
        # Check content
        assert "1" in response.text
        assert "1.1" in response.text
        assert "1.2" in response.text
        assert "2" in response.text
        assert "2.1" in response.text
        
        # Check that the path is included in the links
        assert text_path in response.text


def test_get_references_nonexistent_text(client: TestClient) -> None:
    """Test getting references for a nonexistent text."""
    text_path = "nonexistent/path.xml"
    
    # Create mock XML service response
    with patch("app.routers.read.XMLService") as mock_xml_service_class:
        # Mock the XML service to raise an error for the nonexistent file
        mock_xml_service = mock_xml_service_class.return_value
        mock_xml_service.load_xml.side_effect = FileNotFoundError("File not found")
        
        # Make request to get references for the nonexistent text
        response = client.get(f"/read/references/{text_path}")
        
        # Check response status (should be 404)
        assert response.status_code == 404
        
        # Check error message
        assert "failed to load xml" in response.text.lower()


def test_xml_loading_error(client: TestClient) -> None:
    """Test handling of XML loading errors."""
    text_path = "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    
    # Create mock catalog service and XML service responses
    with patch("app.routers.read.get_catalog_service") as mock_get_catalog, \
         patch("app.routers.read.XMLService") as mock_xml_service_class:
        
        # Mock the catalog service
        mock_catalog_service = mock_get_catalog.return_value
        mock_catalog_service.get_text_by_path.return_value = Text(
            path=text_path,
            title="Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
            author="Diogenes Laertius",
            language="Greek"
        )
        
        # Mock the XML service to return None for load_xml (failed to parse)
        mock_xml_service = mock_xml_service_class.return_value
        mock_xml_service.load_xml.return_value = None
        
        # Make request to read the text
        response = client.get(f"/read/{text_path}")
        
        # Check response status (should be 404)
        assert response.status_code == 404
        
        # Check error message
        assert "failed to load xml" in response.text.lower() 