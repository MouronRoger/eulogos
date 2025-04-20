"""Unit tests for the XML service.

These tests verify that the XML service correctly loads and processes
XML files and correctly handles paths as canonical identifiers.
"""

import os
import pytest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

from app.services.xml_service import XMLService


def test_load_xml(mock_xml_service: XMLService, sample_xml_file: Path) -> None:
    """Test loading an XML file by path."""
    # Get the relative path
    rel_path = sample_xml_file.relative_to(sample_xml_file.parent.parent.parent)
    
    # Load the XML
    root = mock_xml_service.load_xml(str(rel_path))
    
    # Verify that the XML was loaded
    assert root is not None
    assert root.tag == "{http://www.tei-c.org/ns/1.0}TEI"


def test_load_nonexistent_xml(mock_xml_service: XMLService) -> None:
    """Test loading a nonexistent XML file."""
    # Attempt to load a nonexistent file
    with pytest.raises(FileNotFoundError):
        mock_xml_service.load_xml("nonexistent/path.xml")


def test_extract_text_content(mock_xml_service: XMLService, sample_xml_file: Path) -> None:
    """Test extracting plain text content from an XML element."""
    # Get the relative path and load the XML
    rel_path = sample_xml_file.relative_to(sample_xml_file.parent.parent.parent)
    root = mock_xml_service.load_xml(str(rel_path))
    
    # Find a paragraph element
    paragraph = root.find(".//{http://www.tei-c.org/ns/1.0}p")
    assert paragraph is not None
    
    # Extract text content
    text = mock_xml_service.extract_text_content(paragraph)
    
    # Verify the extracted text
    assert text == "This is section 1 of the text."
    
    # Test with None element
    text = mock_xml_service.extract_text_content(None)
    assert text == ""


def test_extract_references(mock_xml_service: XMLService, sample_xml_file: Path) -> None:
    """Test extracting reference sections from an XML document."""
    # Get the relative path and load the XML
    rel_path = sample_xml_file.relative_to(sample_xml_file.parent.parent.parent)
    root = mock_xml_service.load_xml(str(rel_path))
    
    # Extract references
    references = mock_xml_service.extract_references(root)
    
    # Verify the extracted references
    assert len(references) == 5
    assert "1" in references
    assert "1.1" in references
    assert "1.2" in references
    assert "2" in references
    assert "2.1" in references
    
    # Test with None element
    references = mock_xml_service.extract_references(None)
    assert references == {}


def test_get_passage_by_reference(mock_xml_service: XMLService, sample_xml_file: Path) -> None:
    """Test getting a specific passage by reference."""
    # Get the relative path and load the XML
    rel_path = sample_xml_file.relative_to(sample_xml_file.parent.parent.parent)
    root = mock_xml_service.load_xml(str(rel_path))
    
    # Get a specific passage
    passage = mock_xml_service.get_passage_by_reference(root, "1.1")
    assert passage is not None
    
    # Extract text to verify it's the correct passage
    text = mock_xml_service.extract_text_content(passage)
    assert "This is section 1.1 of the text." in text
    
    # Test getting a non-existent passage
    passage = mock_xml_service.get_passage_by_reference(root, "nonexistent")
    assert passage is None
    
    # Test with None element
    passage = mock_xml_service.get_passage_by_reference(None, "1.1")
    assert passage is None
    
    # Test with empty reference
    passage = mock_xml_service.get_passage_by_reference(root, "")
    assert passage is None


def test_get_adjacent_references(mock_xml_service: XMLService, sample_xml_file: Path) -> None:
    """Test getting adjacent references for navigation."""
    # Get the relative path and load the XML
    rel_path = sample_xml_file.relative_to(sample_xml_file.parent.parent.parent)
    root = mock_xml_service.load_xml(str(rel_path))
    
    # Get adjacent references for a middle reference
    adjacent = mock_xml_service.get_adjacent_references(root, "1.1")
    assert adjacent["prev"] == "1"
    assert adjacent["next"] == "1.2"
    
    # Get adjacent references for the first reference
    adjacent = mock_xml_service.get_adjacent_references(root, "1")
    assert adjacent["prev"] is None
    assert adjacent["next"] == "1.1"
    
    # Get adjacent references for the last reference
    adjacent = mock_xml_service.get_adjacent_references(root, "2.1")
    assert adjacent["prev"] == "2"
    assert adjacent["next"] is None
    
    # Test with non-existent reference
    adjacent = mock_xml_service.get_adjacent_references(root, "nonexistent")
    assert adjacent["prev"] is None
    assert adjacent["next"] is None
    
    # Test with None element
    adjacent = mock_xml_service.get_adjacent_references(None, "1.1")
    assert adjacent["prev"] is None
    assert adjacent["next"] is None
    
    # Test with empty reference
    adjacent = mock_xml_service.get_adjacent_references(root, "")
    assert adjacent["prev"] is None
    assert adjacent["next"] is None


def test_transform_to_html(mock_xml_service: XMLService, sample_xml_file: Path) -> None:
    """Test transforming XML to HTML for display."""
    # Get the relative path and load the XML
    rel_path = sample_xml_file.relative_to(sample_xml_file.parent.parent.parent)
    root = mock_xml_service.load_xml(str(rel_path))
    
    # Transform the entire document to HTML
    html = mock_xml_service.transform_to_html(root)
    
    # Verify the HTML contains expected content
    assert "<div class=\"tei-document\">" in html
    assert "This is section 1 of the text." in html
    assert "This is section 2 of the text." in html
    
    # Transform a specific section to HTML
    html = mock_xml_service.transform_to_html(root, "1.1")
    
    # Verify the HTML contains only the specified section
    assert "This is section 1.1 of the text." in html
    assert "This is section 2 of the text." not in html
    
    # Test with non-existent reference
    html = mock_xml_service.transform_to_html(root, "nonexistent")
    assert "Reference 'nonexistent' not found" in html
    
    # Test with None element
    html = mock_xml_service.transform_to_html(None)
    assert "No content available" in html


def test_get_metadata(mock_xml_service: XMLService, sample_xml_file: Path) -> None:
    """Test extracting metadata from an XML document."""
    # Get the relative path and load the XML
    rel_path = sample_xml_file.relative_to(sample_xml_file.parent.parent.parent)
    root = mock_xml_service.load_xml(str(rel_path))
    
    # Extract metadata
    metadata = mock_xml_service.get_metadata(root)
    
    # Verify the extracted metadata
    assert metadata["title"] == "Sample Text"
    assert metadata["author"] == "Test Author"
    assert metadata["publisher"] == "Test Publisher"
    assert metadata["date"] == "2023"
    assert metadata["language"] == "eng"
    assert "source" in metadata
    assert "Test Source" in metadata["source"]
    
    # Test with None element
    metadata = mock_xml_service.get_metadata(None)
    assert metadata == {} 