"""Tests for enhanced XMLProcessorService."""

import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch
from xml.etree.ElementTree import Element

import pytest

from app.models.urn import URN
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
def xml_processor():
    """Create an XMLProcessorService for testing."""
    return XMLProcessorService("test_data")


@pytest.fixture
def sample_xml():
    """Get a sample XML document for testing."""
    return MockXMLFile.get_sample_xml()


@pytest.fixture
def non_tei_xml():
    """Get a non-TEI XML document for testing."""
    return MockXMLFile.get_non_tei_xml()


@pytest.fixture
def mock_catalog_service():
    """Create a mock catalog service."""
    return Mock(spec=CatalogService)


class TestXMLProcessorService:
    """Tests for the enhanced XMLProcessorService."""

    def test_extract_references(self, xml_processor, sample_xml):
        """Test extracting references from XML."""
        references = xml_processor.extract_references(sample_xml)

        assert len(references) >= 7  # 2 books + 5 sections
        assert "1" in references
        assert "1.1" in references
        assert "1.2" in references
        assert "1.3" in references
        assert "2" in references
        assert "2.1" in references
        assert "2.2" in references

    def test_get_passage_by_reference(self, xml_processor, sample_xml):
        """Test getting a passage by reference."""
        passage = xml_processor.get_passage_by_reference(sample_xml, "1.2")

        assert passage is not None
        assert passage.get("n") == "2"

        # Check the text content
        text = "".join(passage.itertext()).strip()
        assert "This is section 1.2" in text

    def test_get_adjacent_references(self, xml_processor, sample_xml):
        """Test getting adjacent references."""
        # Middle reference
        refs = xml_processor.get_adjacent_references(sample_xml, "1.2")
        assert refs["prev"] == "1.1"
        assert refs["next"] == "1.3"

        # First reference
        refs = xml_processor.get_adjacent_references(sample_xml, "1")
        assert refs["prev"] is None
        assert refs["next"] == "1.1"

        # Last reference
        refs = xml_processor.get_adjacent_references(sample_xml, "2.2")
        assert refs["prev"] == "2.1"
        assert refs["next"] is None

        # Non-existent reference
        refs = xml_processor.get_adjacent_references(sample_xml, "3.1")
        assert refs["prev"] is None
        assert refs["next"] is not None  # Should fallback to first reference

    def test_tokenize_text(self, xml_processor):
        """Test tokenizing text."""
        tokens = xml_processor.tokenize_text("This is some Greek text: Θεός.")

        assert len(tokens) == 7  # 6 words + 1 punctuation
        assert tokens[0]["type"] == "word"
        assert tokens[0]["text"] == "This"
        assert tokens[0]["index"] == 1

        assert tokens[-1]["type"] == "punct"
        assert tokens[-1]["text"] == "."

    def test_transform_to_html(self, xml_processor, sample_xml):
        """Test transforming XML to HTML."""
        html = xml_processor.transform_to_html(sample_xml)

        # Check if the HTML contains the reference attributes
        assert 'data-reference="1"' in html
        assert 'data-reference="1.1"' in html
        assert 'data-reference="1.2"' in html

        # Check if the HTML contains the section numbers
        assert '<div class="section-num"><a href="#ref=1">1</a></div>' in html
        assert '<div class="section-num"><a href="#ref=1.1">1</a></div>' in html

        # Check if the HTML contains the tokenized text
        assert '<span class="token"' in html
        assert 'data-token-index="' in html

    def test_transform_to_html_with_target_ref(self, xml_processor, sample_xml):
        """Test transforming XML to HTML with a target reference."""
        html = xml_processor.transform_to_html(sample_xml, "1.2")

        # Should only include the specified section
        assert 'data-reference="1.2"' in html
        assert "This is section 1.2" in html

        # Should not include other sections
        assert "This is section 1.1" not in html
        assert "This is section 1.3" not in html

        # Invalid reference
        with pytest.raises(ValueError):
            xml_processor.transform_to_html(sample_xml, "invalid.ref")

    def test_process_element_to_html(self, xml_processor, sample_xml):
        """Test processing an element to HTML."""
        element = xml_processor.get_passage_by_reference(sample_xml, "2.2")
        html = xml_processor._process_element_to_html(element, "2")

        # Check if the HTML contains the reference attributes
        assert 'data-reference="2.2"' in html

        # Check if the HTML contains the section number
        assert '<div class="section-num"><a href="#ref=2.2">2</a></div>' in html

        # Check if the HTML contains the tokenized text with Greek
        assert "Θεός" in html
        assert "εἶναι" in html
        assert "τὸ" in html
        assert "ἀθάνατον" in html

    def test_resolve_urn_with_catalog(self, mock_catalog_service):
        """Test URN resolution using catalog service."""
        processor = XMLProcessorService("test_data", catalog_service=mock_catalog_service)
        urn = URN("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        expected_path = Path("test_data/some/path.xml")

        # Mock catalog service response
        mock_catalog_service.get_text_by_urn.return_value = Mock(path="some/path.xml")

        # Test resolution
        result = processor.resolve_urn_to_file_path(urn)
        assert result == expected_path
        mock_catalog_service.get_text_by_urn.assert_called_once_with(urn.value)

    def test_resolve_urn_fallback(self, mock_catalog_service):
        """Test URN resolution fallback when catalog fails."""
        processor = XMLProcessorService("test_data", catalog_service=mock_catalog_service)
        urn = URN("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")

        # Mock catalog service to return None
        mock_catalog_service.get_text_by_urn.return_value = None
        mock_catalog_service.get_path_by_urn.return_value = None

        # Test fallback resolution
        result = processor.resolve_urn_to_file_path(urn)
        expected = Path("test_data/tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml")
        assert result == expected

    def test_resolve_urn_invalid(self, xml_processor):
        """Test URN resolution with invalid URN."""
        urn = URN("urn:cts:invalid")
        with pytest.raises(ValueError, match="URN .* missing required components"):
            xml_processor.resolve_urn_to_file_path(urn)

    def test_namespace_handling_tei(self, xml_processor, sample_xml):
        """Test handling of TEI namespace."""
        # Verify namespace is preserved in references
        refs = xml_processor.extract_references(sample_xml)
        for element in refs.values():
            assert element.tag.startswith("{http://www.tei-c.org/ns/1.0}")

        # Verify namespace handling in HTML transformation
        html = xml_processor.transform_to_html(sample_xml)
        assert "xmlns=" not in html  # Namespace should be stripped from HTML output

    def test_namespace_handling_non_tei(self, xml_processor, non_tei_xml):
        """Test handling of non-TEI namespace."""
        # Extract references from non-TEI document
        refs = xml_processor.extract_references(non_tei_xml)
        assert "1" in refs
        assert "1.1" in refs

        # Verify namespace handling in transformation
        html = xml_processor.transform_to_html(non_tei_xml)
        assert "xmlns=" not in html
        assert "This is section 1.1" in html

    def test_load_xml_with_namespace(self, xml_processor):
        """Test loading XML with namespace handling."""
        xml_str = """
        <root xmlns="http://example.org/ns/1.0">
            <element n="1">
                <child n="1">Content</child>
            </element>
        </root>
        """
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.return_value.getroot.return_value = ET.fromstring(xml_str)
            mock_urn = Mock(spec=URN)
            mock_urn.value = "urn:test"
            mock_urn.textgroup = "test"
            mock_urn.work = "work"
            mock_urn.version = "1.0"

            root = xml_processor.load_xml(mock_urn)
            assert root.tag == "{http://example.org/ns/1.0}root"
            assert root.find(".//{http://example.org/ns/1.0}child").text == "Content"

    def test_malformed_xml_handling(self, xml_processor):
        """Test handling of malformed XML."""
        with patch("xml.etree.ElementTree.parse") as mock_parse:
            mock_parse.side_effect = ET.ParseError("XML syntax error")
            mock_urn = Mock(spec=URN)
            mock_urn.value = "urn:test"
            mock_urn.textgroup = "test"
            mock_urn.work = "work"
            mock_urn.version = "1.0"

            with pytest.raises(ET.ParseError):
                xml_processor.load_xml(mock_urn)

    def test_file_not_found_handling(self, xml_processor):
        """Test handling of missing XML files."""
        mock_urn = Mock(spec=URN)
        mock_urn.value = "urn:test:nonexistent"
        mock_urn.textgroup = "test"
        mock_urn.work = "work"
        mock_urn.version = "1.0"

        with pytest.raises(FileNotFoundError):
            xml_processor.load_xml(mock_urn)

    def test_empty_element_handling(self, xml_processor):
        """Test handling of empty XML elements."""
        xml_str = """
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
            <div type="textpart" n="1">
                <p></p>
                <div type="textpart" n="1"/>
            </div>
        </TEI>
        """
        root = ET.fromstring(xml_str)

        # Test reference extraction
        refs = xml_processor.extract_references(root)
        assert "1" in refs
        assert "1.1" in refs

        # Test HTML transformation
        html = xml_processor.transform_to_html(root)
        assert 'data-reference="1"' in html
        assert 'data-reference="1.1"' in html

    def test_deeply_nested_structure(self, xml_processor):
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

        # Test HTML transformation of deeply nested structure
        html = xml_processor.transform_to_html(root)
        assert "Deeply nested content" in html
        assert 'data-reference="1.1.1.1.1"' in html

    def test_special_characters_handling(self, xml_processor):
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

        # Test HTML transformation with special characters
        html = xml_processor.transform_to_html(root)
        assert "&lt;" in html  # HTML entities should be preserved
        assert "&gt;" in html
        assert "&amp;" in html
        assert "漢字" in html  # Unicode should be preserved
        assert "αβγ" in html
        assert "🌟" in html

    def test_mixed_content_model(self, xml_processor):
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

        # Test HTML transformation with mixed content
        html = xml_processor.transform_to_html(root)
        assert "Text" in html
        assert "with" in html
        assert "content" in html
        assert "model" in html

        # Test reference extraction with mixed content
        refs = xml_processor.extract_references(root)
        assert "1" in refs

    def test_invalid_reference_format(self, xml_processor, sample_xml):
        """Test handling of invalid reference formats."""
        # Test with non-existent reference
        invalid_ref = "999.999"
        html = xml_processor.transform_to_html(sample_xml, target_ref=invalid_ref)
        assert f"Reference '{invalid_ref}' not found" in html

        # Test with malformed reference
        malformed_ref = "1.a.b"
        element = xml_processor.get_passage_by_reference(sample_xml, malformed_ref)
        assert element is None

        # Test adjacent references with invalid reference
        refs = xml_processor.get_adjacent_references(sample_xml, malformed_ref)
        assert refs["prev"] is None
        assert refs["next"] is None

    def test_missing_required_attributes(self, xml_processor):
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

        # Test HTML transformation with missing attributes
        html = xml_processor.transform_to_html(root)
        assert "Content" in html
        assert 'data-reference="1"' in html
