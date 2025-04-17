"""Tests for the Enhanced XML Service.

This module contains unit tests for XML processing and transformation.
"""

import xml.etree.ElementTree as ET

import pytest

from app.models.enhanced_urn import EnhancedURN
from app.models.xml_document import XMLDocument
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService


@pytest.fixture
def sample_xml_content():
    """Sample XML content for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Homeri Ilias</title>
        <editor>An Editor</editor>
        <editor role="translator">A Translator</editor>
      </titleStmt>
    </fileDesc>
  </teiHeader>
  <text xml:lang="grc">
    <body>
      <div n="1" type="book">
        <head>Book 1</head>
        <l n="1">Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος</l>
        <l n="2">οὐλομένην, ἣ μυρί᾽ Ἀχαιοῖς ἄλγε᾽ ἔθηκε,</l>
        <l n="3">πολλὰς δ᾽ ἰφθίμους ψυχὰς Ἄϊδι προΐαψεν</l>
        <l n="4">ἡρώων, αὐτοὺς δὲ ἑλώρια τεῦχε κύνεσσιν</l>
      </div>
    </body>
  </text>
</TEI>
"""


@pytest.fixture
def sample_xml_file(sample_xml_content, tmp_path):
    """Create a sample XML file for testing."""
    # Create the directory structure
    work_dir = tmp_path / "tlg0012" / "tlg001"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Create the XML file
    xml_path = work_dir / "tlg0012.tlg001.perseus-grc1.xml"
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(sample_xml_content)

    return xml_path


@pytest.fixture
def mock_catalog_service(sample_xml_file, monkeypatch):
    """Mock catalog service for testing."""
    from app.config import EulogosSettings

    # Get the parent directory of sample_xml_file
    data_dir = sample_xml_file.parent.parent.parent

    # Create settings with test paths
    settings = EulogosSettings(
        data_dir=data_dir, catalog_path=data_dir / "integrated_catalog.json", enable_caching=True, xml_cache_size=10
    )

    # Create a minimal catalog JSON
    catalog_json = {
        "statistics": {"author_count": 1, "work_count": 1, "edition_count": 1},
        "authors": {
            "tlg0012": {
                "id": "tlg0012",
                "name": "Homer",
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
                    }
                },
            }
        },
    }

    # Write catalog JSON
    with open(settings.catalog_path, "w", encoding="utf-8") as f:
        import json

        json.dump(catalog_json, f)

    # Create catalog service
    catalog_service = EnhancedCatalogService(settings=settings)
    catalog_service.load_catalog()

    return catalog_service


@pytest.fixture
def xml_service(mock_catalog_service):
    """Create an EnhancedXMLService for testing."""
    return EnhancedXMLService(catalog_service=mock_catalog_service)


def test_load_document(xml_service):
    """Test loading a document by URN."""
    urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test with string URN
    document = xml_service.load_document(urn)
    assert isinstance(document, XMLDocument)
    assert document.urn == urn
    assert document.root_element is not None

    # Test with EnhancedURN object
    urn_obj = EnhancedURN(value=urn)
    document2 = xml_service.load_document(urn_obj)
    assert document2.urn == urn

    # Test caching
    assert urn in xml_service._cache

    # Test cache hit
    document3 = xml_service.load_document(urn)
    assert document3.access_count == 2


def test_extract_metadata(xml_service, mock_catalog_service):
    """Test metadata extraction from XML."""
    urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
    document = xml_service.load_document(urn)

    # Check extracted metadata
    assert document.metadata["title"] == "Homeri Ilias"
    assert document.metadata["editor"] == "An Editor"
    assert document.metadata["translator"] == "A Translator"
    assert document.metadata["language"] == "grc"


def test_extract_references(xml_service):
    """Test reference extraction from XML."""
    urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
    document = xml_service.load_document(urn)

    # Check references
    assert len(document.references) == 5  # 1 book + 4 lines
    assert "1" in document.references  # Book 1
    assert "1.1" in document.references  # Line 1
    assert "1.2" in document.references  # Line 2
    assert "1.3" in document.references  # Line 3
    assert "1.4" in document.references  # Line 4

    # Check parent-child relationships
    assert document.references["1"].child_refs == ["1.1", "1.2", "1.3", "1.4"]
    assert document.references["1.1"].parent_ref == "1"


def test_get_passage(xml_service):
    """Test getting a passage by reference."""
    urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test without reference (entire document)
    full_text = xml_service.get_passage(urn)
    assert "Μῆνιν ἄειδε θεὰ" in full_text

    # Test with specific reference
    line1 = xml_service.get_passage(urn, "1.1")
    assert "Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος" in line1

    # Test with non-existent reference
    assert xml_service.get_passage(urn, "1.10") is None


def test_get_adjacent_references(xml_service):
    """Test getting adjacent references."""
    urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test first reference
    refs = xml_service.get_adjacent_references(urn, "1")
    assert refs["prev"] is None
    assert refs["next"] == "1.1"

    # Test middle reference
    refs = xml_service.get_adjacent_references(urn, "1.2")
    assert refs["prev"] == "1.1"
    assert refs["next"] == "1.3"

    # Test last reference
    refs = xml_service.get_adjacent_references(urn, "1.4")
    assert refs["prev"] == "1.3"
    assert refs["next"] is None

    # Test non-existent reference
    refs = xml_service.get_adjacent_references(urn, "1.10")
    assert refs["prev"] is None
    assert refs["next"] is None


def test_transform_to_html(xml_service):
    """Test transforming XML to HTML."""
    urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test entire document
    html = xml_service.transform_to_html(urn)
    assert "<div" in html
    assert "Book 1" in html
    assert "Μῆνιν ἄειδε θεὰ" in html

    # Test specific reference
    html = xml_service.transform_to_html(urn, "1.1")
    assert "<span" in html
    assert "Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος" in html


def test_cache_management(xml_service, monkeypatch):
    """Test cache management."""
    # Reduce cache size
    xml_service.settings.xml_cache_size = 2

    # Create multiple URNs
    urn1 = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
    urn2 = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"
    urn3 = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc3"

    # Mock catalog service's resolve_file_path to return the same file for all URNs
    original_resolve = xml_service.catalog_service.resolve_file_path

    def mock_resolve(urn):
        real_path = original_resolve("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        return real_path

    monkeypatch.setattr(xml_service.catalog_service, "resolve_file_path", mock_resolve)

    # Load the first document
    xml_service.load_document(urn1)
    assert len(xml_service._cache) == 1
    assert urn1 in xml_service._cache

    # Load the second document
    xml_service.load_document(urn2)
    assert len(xml_service._cache) == 2
    assert urn1 in xml_service._cache
    assert urn2 in xml_service._cache

    # Load the third document (should evict the first)
    xml_service.load_document(urn3)
    assert len(xml_service._cache) == 2
    assert urn1 not in xml_service._cache
    assert urn2 in xml_service._cache
    assert urn3 in xml_service._cache


def test_element_to_html(xml_service):
    """Test converting XML element to HTML."""
    # Create a simple XML element
    element = ET.fromstring('<div n="1"><head>Title</head><p>Text <foreign>foreign</foreign> content</p></div>')

    # Convert to HTML
    html = xml_service._element_to_html(element)

    # Check HTML
    assert "<div" in html
    assert "<h3" in html
    assert "Title" in html
    assert "<p" in html
    assert "<em" in html
    assert "foreign" in html
