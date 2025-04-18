"""Tests for XMLProcessorServiceAdapter."""

from pathlib import Path  # noqa: F401 - Used by pytest's tmp_path fixture

import pytest


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


