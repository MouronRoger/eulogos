"""Tests for enhanced XMLProcessorService."""

import xml.etree.ElementTree as ET

import pytest

from app.services.xml_processor_service import XMLProcessorService


class MockXMLFile:
    """Mock XML file for testing."""

    @staticmethod
    def get_sample_xml() -> ET._Element:
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


@pytest.fixture
def xml_processor():
    """Create an XMLProcessorService for testing."""
    return XMLProcessorService("test_data")


@pytest.fixture
def sample_xml():
    """Get a sample XML document for testing."""
    return MockXMLFile.get_sample_xml()


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
