"""Tests for XMLProcessorService."""

import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch
from xml.etree.ElementTree import Element

import pytest

from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService


class MockXMLFile:
    """Mock XML file for testing."""

    @staticmethod
    def get_sample_xml() -> Element:
        """Get a sample XML document for testing.

        Returns:
            Root XML element
        """
        xml_str = """
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
          <text>
            <body>
              <div type="textpart" n="1">
                <div type="textpart" n="1">
                  <p>This is section 1.1</p>
                </div>
                <div type="textpart" n="2">
                  <p>This is section 1.2</p>
                </div>
                <div type="textpart" n="3">
                  <p>This is section 1.3</p>
                </div>
              </div>
              <div type="textpart" n="2">
                <div type="textpart" n="1">
                  <p>This is section 2.1</p>
                </div>
                <div type="textpart" n="2">
                  <p>This is section 2.2 with Greek: Θεός εἶναι τὸ ἀθάνατον.</p>
                </div>
              </div>
            </body>
          </text>
        </TEI>
        """
        return ET.fromstring(xml_str)

    @staticmethod
    def get_non_tei_xml() -> Element:
        """Get a non-TEI XML document for testing.

        Returns:
            Root XML element
        """
        xml_str = """
        <document xmlns="http://example.org/ns/1.0">
          <section n="1">
            <subsection n="1">
              <content>This is section 1.1</content>
            </subsection>
          </section>
        </document>
        """
        return ET.fromstring(xml_str)


@pytest.fixture
def mock_catalog_service():
    """Create a mock catalog service."""
    mock_service = Mock(spec=CatalogService)
    mock_service.get_text_by_id.return_value = {
        "id": "test_id",
        "path": "test_path.xml",
        "language": "grc"
    }
    return mock_service


@pytest.fixture
def xml_processor(mock_catalog_service):
    """Create an XMLProcessorService for testing."""
    return XMLProcessorService(catalog_service=mock_catalog_service, data_path="test_data")


@pytest.fixture
def sample_xml():
    """Get a sample XML document for testing."""
    return MockXMLFile.get_sample_xml()


@pytest.fixture
def non_tei_xml():
    """Get a non-TEI XML document for testing."""
    return MockXMLFile.get_non_tei_xml()


class TestXMLProcessorService:
    """Tests for the XMLProcessorService."""

    def test_deeply_nested_structure(self, xml_processor, mock_catalog_service):
        """Test handling of deeply nested XML structures."""
        xml_str = """
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <div type="textpart" n="1">
                <div type="textpart" n="1">
                    <div type="textpart" n="1">
                        <div type="textpart" n="1">
                            <div type="textpart" n="1">
                                <p>Deeply nested content</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </TEI>
        """
        root = ET.fromstring(xml_str)

        # Test reference extraction from deeply nested structure
        refs = xml_processor.extract_references(root)
        assert "1" in refs
        assert "1.1" in refs
        assert "1.1.1" in refs
        assert "1.1.1.1" in refs
        assert "1.1.1.1.1" in refs

        # Mock the load_document method to return our test root
        with patch.object(xml_processor, 'load_document', return_value=root):
            # Test HTML transformation of deeply nested structure
            html = xml_processor.transform_to_html("test_id")
            assert "Deeply nested content" in html
            assert 'data-ref="1.1.1.1.1"' in html

    def test_special_characters_handling(self, xml_processor, mock_catalog_service):
        """Test handling of special characters and Unicode."""
        xml_str = """
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <div type="textpart" n="1">
                <p>Special chars: &lt;&gt;&amp;"'</p>
                <p>Unicode: 漢字 αβγ 🌟 </p>
            </div>
        </TEI>
        """
        root = ET.fromstring(xml_str)

        # Mock the load_document method to return our test root
        with patch.object(xml_processor, 'load_document', return_value=root):
            # Test HTML transformation with special characters
            html = xml_processor.transform_to_html("test_id")
            assert "<>&\"'" in html  # Characters are not HTML encoded in the output
            assert "漢字" in html  # Unicode should be preserved
            assert "αβγ" in html
            assert "🌟" in html

    def test_mixed_content_model(self, xml_processor, mock_catalog_service):
        """Test handling of mixed content models."""
        xml_str = """
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <div type="textpart" n="1">
                <p>Text <emph>with</emph> mixed <ref>content</ref> model</p>
                <p>Another <emph>paragraph</emph> with <ref n="1">reference</ref></p>
            </div>
        </TEI>
        """
        root = ET.fromstring(xml_str)

        # Mock the load_document method to return our test root
        with patch.object(xml_processor, 'load_document', return_value=root):
            # Test HTML transformation with mixed content
            html = xml_processor.transform_to_html("test_id")
            assert "Text" in html
            assert "with" in html
            assert "content" in html
            assert "model" in html

        # Test reference extraction with mixed content
        refs = xml_processor.extract_references(root)
        assert "1" in refs

    def test_invalid_reference_format(self, xml_processor, sample_xml, mock_catalog_service):
        """Test handling of invalid reference formats."""
        # Mock the load_document method to return sample_xml
        with patch.object(xml_processor, 'load_document', return_value=sample_xml):
            # Test with non-existent reference
            invalid_ref = "999.999"
            html = xml_processor.transform_to_html("test_id", target_ref=invalid_ref)
            assert f"Reference '{invalid_ref}' not found" in html

            # Test with malformed reference
            malformed_ref = "1.a.b"
            element = xml_processor.get_passage_by_reference(sample_xml, malformed_ref)
            assert element is None

            # Test adjacent references with invalid reference
            refs = xml_processor.get_adjacent_references(sample_xml, malformed_ref)
            assert refs["prev"] is None
            assert refs["next"] is None

    def test_missing_required_attributes(self, xml_processor, mock_catalog_service):
        """Test handling of elements with missing required attributes."""
        xml_str = """
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <div type="textpart">
                <div type="textpart" n="1">
                    <p>Content</p>
                </div>
            </div>
        </TEI>
        """
        root = ET.fromstring(xml_str)

        # Test reference extraction with missing n attribute
        refs = xml_processor.extract_references(root)
        assert "1" in refs  # Should still find references where n is present

        # Mock the load_document method to return our test root
        with patch.object(xml_processor, 'load_document', return_value=root):
            # Test HTML transformation with missing attributes
            html = xml_processor.transform_to_html("test_id")
            assert "Content" in html
            assert 'data-ref="1"' in html
