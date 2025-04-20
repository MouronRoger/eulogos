"""Unit tests for the canonical catalog builder.

These tests verify that the canonical catalog builder correctly processes
XML files and generates the catalog with paths as canonical identifiers.
"""

import json
import os
import pytest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, mock_open, MagicMock

from canonical_catalog_builder import (
    extract_author_info,
    extract_work_info,
    extract_version_info,
    extract_editions_and_translations,
    build_catalog,
    NAMESPACE
)


@pytest.fixture
def sample_author_cts_content() -> str:
    """Create sample content for author-level __cts__.xml."""
    return """
    <textgroup xmlns="http://chs.harvard.edu/xmlns/cts" urn="urn:cts:greekLit:tlg0004">
        <groupname>Diogenes Laertius</groupname>
    </textgroup>
    """


@pytest.fixture
def sample_work_cts_content() -> str:
    """Create sample content for work-level __cts__.xml."""
    return """
    <work xmlns="http://chs.harvard.edu/xmlns/cts" 
          xml:lang="grc" 
          urn="urn:cts:greekLit:tlg0004.tlg001">
        <title>Vitae philosophorum</title>
        <edition urn="urn:cts:greekLit:tlg0004.tlg001.perseus-grc2">
            <label>Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων</label>
            <description>Diogenes Laertius. Hicks, R. D., editor.</description>
        </edition>
        <translation xml:lang="eng" urn="urn:cts:greekLit:tlg0004.tlg001.perseus-eng2">
            <label>Lives of Eminent Philosophers</label>
            <description>Diogenes Laertius. Hicks, R. D., editor.</description>
        </translation>
    </work>
    """


@pytest.fixture
def sample_xml_header() -> str:
    """Create sample XML header content with editor information."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
      <teiHeader>
        <fileDesc>
          <titleStmt>
            <title>Sample Text</title>
            <author>Test Author</author>
            <editor>R. D. Hicks</editor>
            <editor role="translator">R. D. Hicks</editor>
          </titleStmt>
        </fileDesc>
      </teiHeader>
    </TEI>
    """


def test_extract_author_info(sample_author_cts_content: str) -> None:
    """Test extracting author URN and name from __cts__.xml."""
    with patch("xml.etree.ElementTree.parse") as mock_parse:
        # Mock the parsed ElementTree
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree
        
        # Mock the root element and its find method
        mock_root = ET.fromstring(sample_author_cts_content)
        mock_tree.getroot.return_value = mock_root
        
        # Call the function to test
        result = extract_author_info("mock/path/__cts__.xml")
        
        # Check the result
        assert result["urn"] == "urn:cts:greekLit:tlg0004"
        assert result["name"] == "Diogenes Laertius"


def test_extract_work_info(sample_work_cts_content: str) -> None:
    """Test extracting work URN, title, and language from __cts__.xml."""
    with patch("xml.etree.ElementTree.parse") as mock_parse:
        # Mock the parsed ElementTree
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree
        
        # Mock the root element and its find method
        mock_root = ET.fromstring(sample_work_cts_content)
        mock_tree.getroot.return_value = mock_root
        
        # Call the function to test
        result = extract_work_info("mock/path/__cts__.xml")
        
        # Check the result
        assert result["urn"] == "urn:cts:greekLit:tlg0004.tlg001"
        assert result["title"] == "Vitae philosophorum"
        assert result["language"] == "grc"


def test_extract_version_info(sample_xml_header: str) -> None:
    """Test extracting info for an edition or translation."""
    # Setup test data
    edition_elem = ET.fromstring(
        '<edition xmlns="http://chs.harvard.edu/xmlns/cts" '
        'xml:lang="grc" '
        'urn="urn:cts:greekLit:tlg0004.tlg001.perseus-grc2">'
        '<label>Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων</label>'
        '<description>Diogenes Laertius. Hicks, R. D., editor.</description>'
        '</edition>'
    )
    
    xml_files = ["tlg0004.tlg001.perseus-grc2.xml"]
    work_dir = "data/tlg0004/tlg001"
    data_dir = "data"
    
    # Mock the open function to return sample XML header
    with patch("builtins.open", mock_open(read_data=sample_xml_header)):
        # Mock os.path.join to return the expected path
        with patch("os.path.join", return_value="data/tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"):
            # Mock os.path.relpath to return the expected relative path
            with patch("os.path.relpath", return_value="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"):
                # Call the function to test
                result = extract_version_info(edition_elem, xml_files, work_dir, data_dir)
                
                # Check the result
                assert result["id"] == "perseus-grc2"
                assert result["urn"] == "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2"
                assert result["label"] == "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων"
                assert result["description"] == "Diogenes Laertius. Hicks, R. D., editor."
                assert result["lang"] == "grc"
                assert result["language"] == "Greek"
                assert result["editor"] == "R. D. Hicks"
                assert result["translator"] == "R. D. Hicks"
                assert result["path"] == "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
                assert result["filename"] == "tlg0004.tlg001.perseus-grc2.xml"


def test_extract_editions_and_translations(sample_work_cts_content: str, sample_xml_header: str) -> None:
    """Test extracting editions and translations from a work-level __cts__.xml."""
    # Parse the sample work CTS content
    root = ET.fromstring(sample_work_cts_content)
    
    # Setup test files
    xml_files = ["tlg0004.tlg001.perseus-grc2.xml", "tlg0004.tlg001.perseus-eng2.xml"]
    work_dir = "data/tlg0004/tlg001"
    data_dir = "data"
    
    # Mock extract_version_info to return expected data
    with patch("canonical_catalog_builder.extract_version_info") as mock_extract:
        # Mock different returns for different calls
        mock_extract.side_effect = [
            {
                "id": "perseus-grc2",
                "urn": "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2",
                "label": "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
                "description": "Diogenes Laertius. Hicks, R. D., editor.",
                "lang": "grc",
                "language": "Greek",
                "editor": "R. D. Hicks",
                "path": "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
                "filename": "tlg0004.tlg001.perseus-grc2.xml"
            },
            {
                "id": "perseus-eng2",
                "urn": "urn:cts:greekLit:tlg0004.tlg001.perseus-eng2",
                "label": "Lives of Eminent Philosophers",
                "description": "Diogenes Laertius. Hicks, R. D., editor.",
                "lang": "eng",
                "language": "English",
                "translator": "R. D. Hicks",
                "path": "tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
                "filename": "tlg0004.tlg001.perseus-eng2.xml"
            }
        ]
        
        # Call the function to test
        editions, translations = extract_editions_and_translations(
            root, xml_files, work_dir, data_dir
        )
        
        # Check the result
        assert "perseus-grc2" in editions
        assert "perseus-eng2" in translations
        assert editions["perseus-grc2"]["language"] == "Greek"
        assert translations["perseus-eng2"]["language"] == "English"
        assert editions["perseus-grc2"]["path"] == "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
        assert translations["perseus-eng2"]["path"] == "tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml"


def test_build_catalog() -> None:
    """Test building the hierarchical catalog."""
    # Create a temporary directory structure with test data
    with patch("pathlib.Path.iterdir") as mock_iterdir, \
         patch("pathlib.Path.glob") as mock_glob, \
         patch("pathlib.Path.is_dir") as mock_is_dir, \
         patch("pathlib.Path.exists") as mock_exists, \
         patch("canonical_catalog_builder.extract_author_info") as mock_extract_author, \
         patch("canonical_catalog_builder.extract_work_info") as mock_extract_work, \
         patch("canonical_catalog_builder.extract_editions_and_translations") as mock_extract_versions, \
         patch("xml.etree.ElementTree.parse") as mock_parse:
        
        # Mock directory structure
        mock_iterdir.side_effect = [
            # First call: list author directories
            [Path("data/tlg0004")],
            # Second call: list work directories in tlg0004
            [Path("data/tlg0004/tlg001")]
        ]
        
        # Mock directory and file existence checks
        mock_is_dir.return_value = True
        mock_exists.return_value = True
        
        # Mock globbing for XML files
        mock_glob.return_value = [Path("data/tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml")]
        
        # Mock author information extraction
        mock_extract_author.return_value = {
            "urn": "urn:cts:greekLit:tlg0004",
            "name": "Diogenes Laertius"
        }
        
        # Mock work information extraction
        mock_extract_work.return_value = {
            "urn": "urn:cts:greekLit:tlg0004.tlg001",
            "title": "Vitae philosophorum",
            "language": "grc"
        }
        
        # Mock editions and translations extraction
        mock_extract_versions.return_value = (
            {
                "perseus-grc2": {
                    "urn": "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2",
                    "label": "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
                    "description": "Diogenes Laertius. Hicks, R. D., editor.",
                    "lang": "grc",
                    "language": "Greek",
                    "editor": "R. D. Hicks",
                    "path": "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
                    "filename": "tlg0004.tlg001.perseus-grc2.xml"
                }
            },
            {}  # No translations for this test
        )
        
        # Mock parsing XML
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree
        mock_root = MagicMock()
        mock_tree.getroot.return_value = mock_root
        
        # Create test author index
        author_index = {
            "tlg0004": {
                "name": "Diogenes Laertius",
                "century": 3,
                "type": "Biographer"
            }
        }
        
        # Call the function to test
        catalog = build_catalog("data", author_index)
        
        # Check the result
        assert "tlg0004" in catalog
        assert catalog["tlg0004"]["name"] == "Diogenes Laertius"
        assert catalog["tlg0004"]["century"] == 3
        assert catalog["tlg0004"]["type"] == "Biographer"
        assert "tlg001" in catalog["tlg0004"]["works"]
        assert catalog["tlg0004"]["works"]["tlg001"]["title"] == "Vitae philosophorum"
        assert "perseus-grc2" in catalog["tlg0004"]["works"]["tlg001"]["editions"]
        assert catalog["tlg0004"]["works"]["tlg001"]["editions"]["perseus-grc2"]["path"] == "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml" 