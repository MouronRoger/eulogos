"""Tests for XMLProcessorServiceAdapter."""

from pathlib import Path  # noqa: F401 - Used by pytest's tmp_path fixture

import pytest

from app.models.enhanced_urn import EnhancedURN
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService
from app.services.xml_processor_adapter import XMLProcessorServiceAdapter


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


@pytest.fixture
def xml_adapter(xml_service, mock_catalog_service):
    """Create an XMLProcessorServiceAdapter for testing."""
    return XMLProcessorServiceAdapter(enhanced_service=xml_service, catalog_service=mock_catalog_service)


def test_resolve_urn_to_file_path(xml_adapter, mock_catalog_service):
    """Test resolving URN to file path."""
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    path = xml_adapter.resolve_urn_to_file_path(urn)

    # Check that the adapter delegates to catalog service
    assert path is not None
    assert path.name == "tlg0012.tlg001.perseus-grc1.xml"


def test_load_xml(xml_adapter):
    """Test loading XML by URN."""
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    root = xml_adapter.load_xml(urn)

    # Check that XML was loaded
    assert root is not None
    assert root.tag.endswith("TEI")


def test_extract_references(xml_adapter):
    """Test extracting references from XML."""
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    root = xml_adapter.load_xml(urn)

    # Extract references
    refs = xml_adapter.extract_references(root)

    # Check references
    assert len(refs) == 5  # 1 book + 4 lines
    assert "1" in refs
    assert "1.1" in refs
    assert "1.2" in refs
    assert "1.3" in refs
    assert "1.4" in refs


def test_get_passage_by_reference(xml_adapter):
    """Test getting passage by reference."""
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    root = xml_adapter.load_xml(urn)

    # Get passage
    element = xml_adapter.get_passage_by_reference(root, "1.1")

    # Check passage
    assert element is not None
    assert element.tag.endswith("l")
    assert element.get("n") == "1"
    assert "Μῆνιν ἄειδε θεὰ" in element.text


def test_get_adjacent_references(xml_adapter):
    """Test getting adjacent references."""
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    root = xml_adapter.load_xml(urn)

    # Get adjacent references
    # First reference
    refs = xml_adapter.get_adjacent_references(root, "1")
    assert refs["prev"] is None
    assert refs["next"] == "1.1"

    # Middle reference
    refs = xml_adapter.get_adjacent_references(root, "1.2")
    assert refs["prev"] == "1.1"
    assert refs["next"] == "1.3"

    # Last reference
    refs = xml_adapter.get_adjacent_references(root, "1.4")
    assert refs["prev"] == "1.3"
    assert refs["next"] is None


def test_transform_to_html(xml_adapter):
    """Test transforming XML to HTML."""
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    root = xml_adapter.load_xml(urn)

    # Transform to HTML
    html = xml_adapter.transform_to_html(root)

    # Check HTML
    assert "<div" in html
    assert "Book 1" in html
    assert "Μῆνιν ἄειδε θεὰ" in html

    # Transform specific reference
    html = xml_adapter.transform_to_html(root, "1.1")
    assert "<span" in html
    assert "Μῆνιν ἄειδε θεὰ" in html


def test_tokenize_text(xml_adapter):
    """Test tokenizing text."""
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    root = xml_adapter.load_xml(urn)

    # Get a passage
    element = xml_adapter.get_passage_by_reference(root, "1.1")

    # Tokenize text
    tokens = xml_adapter.tokenize_text(element)

    # Check tokens
    assert len(tokens) > 0
    assert all(isinstance(token, dict) for token in tokens)
    assert all("type" in token and "text" in token for token in tokens)


def test_parse_urn(xml_adapter):
    """Test parsing URN."""
    urn_str = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1:1.1"
    components = xml_adapter.parse_urn(urn_str)

    # Check components
    assert components["namespace"] == "greekLit"
    assert components["textgroup"] == "tlg0012"
    assert components["work"] == "tlg001"
    assert components["version"] == "perseus-grc1"
    assert components["reference"] == "1.1"


def test_get_file_path(xml_adapter):
    """Test getting file path."""
    urn_str = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
    path = xml_adapter.get_file_path(urn_str)

    # Check path
    assert path is not None
    assert path.name == "tlg0012.tlg001.perseus-grc1.xml"


def test_extract_text_content(xml_adapter, sample_xml_file):
    """Test extracting text content."""
    # Extract text content
    content = xml_adapter.extract_text_content(sample_xml_file)

    # Check content
    assert "Book 1" in content
    assert "Μῆνιν ἄειδε θεὰ" in content
