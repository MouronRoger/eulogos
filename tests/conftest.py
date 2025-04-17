"""Test configuration and fixtures for the Eulogos test suite."""

import json
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict

import pytest

from app.config import EulogosSettings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_catalog_data() -> Dict[str, Any]:
    """Create sample catalog data for tests."""
    return {
        "statistics": {
            "author_count": 1,
            "work_count": 1,
            "edition_count": 1,
            "translation_count": 0,
            "greek_word_count": 100,
            "latin_word_count": 0,
            "arabic_word_count": 0,
        },
        "authors": {
            "tlg0012": {
                "id": "tlg0012",
                "name": "Homer",
                "century": -8,
                "type": "Author",
                "works": {
                    "tlg001": {
                        "id": "tlg001",
                        "title": "Iliad",
                        "urn": "urn:cts:greekLit:tlg0012.tlg001",
                        "language": "grc",
                        "editions": {
                            "perseus-grc1": {
                                "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
                                "label": "Homeri Ilias",
                                "language": "grc",
                                "path": "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml",
                                "word_count": 100,
                            }
                        },
                        "translations": {},
                    }
                },
            }
        },
    }


@pytest.fixture
def sample_catalog_file(temp_dir, sample_catalog_data):
    """Create a sample catalog file for tests."""
    catalog_path = temp_dir / "integrated_catalog.json"

    with open(catalog_path, "w") as f:
        json.dump(sample_catalog_data, f)

    return catalog_path


@pytest.fixture
def sample_xml_file(temp_dir):
    """Create a sample XML file for tests."""
    # Create directory structure
    xml_dir = temp_dir / "data" / "tlg0012" / "tlg001"
    os.makedirs(xml_dir, exist_ok=True)

    # Create XML file
    xml_path = xml_dir / "tlg0012.tlg001.perseus-grc1.xml"

    # Create simple TEI XML
    root = ET.Element("{http://www.tei-c.org/ns/1.0}TEI")
    header = ET.SubElement(root, "{http://www.tei-c.org/ns/1.0}teiHeader")
    file_desc = ET.SubElement(header, "{http://www.tei-c.org/ns/1.0}fileDesc")
    title_stmt = ET.SubElement(file_desc, "{http://www.tei-c.org/ns/1.0}titleStmt")
    title = ET.SubElement(title_stmt, "{http://www.tei-c.org/ns/1.0}title")
    title.text = "Homeri Ilias"

    # Add text element with book and lines
    text_elem = ET.SubElement(root, "{http://www.tei-c.org/ns/1.0}text")
    body = ET.SubElement(text_elem, "{http://www.tei-c.org/ns/1.0}body")

    # Add book 1
    book = ET.SubElement(body, "{http://www.tei-c.org/ns/1.0}div", n="1", type="book")
    book_title = ET.SubElement(book, "{http://www.tei-c.org/ns/1.0}head")
    book_title.text = "Book 1"

    # Add some lines
    for i in range(1, 5):
        line = ET.SubElement(book, "{http://www.tei-c.org/ns/1.0}l", n=str(i))
        line.text = f"This is line {i} of Book 1"

    # Write to file
    tree = ET.ElementTree(root)
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    return xml_path


@pytest.fixture
def test_settings(sample_catalog_file, temp_dir):
    """Create test settings with temp paths."""
    return EulogosSettings(
        catalog_path=sample_catalog_file,
        data_dir=temp_dir / "data",
        xml_cache_size=10,
        enable_caching=True,
        compatibility_mode=True,
    )
