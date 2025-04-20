"""Pytest fixtures for Eulogos test suite.

This module provides shared fixtures for all tests, focusing on handling 
the principle that integrated_catalog.json is the sole source of truth
and all text references are the full path to the text.
"""

import json
import os
import pytest
import shutil
from pathlib import Path
from typing import Dict, List, Any, Generator

from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import app
from app.models.catalog import Catalog, Text
from app.services.catalog_service import CatalogService
from app.services.xml_service import XMLService


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_catalog_data() -> Dict[str, Any]:
    """Create a sample hierarchical catalog structure for testing."""
    return {
        "tlg0004": {
            "name": "Diogenes Laertius",
            "urn": "urn:cts:greekLit:tlg0004",
            "century": 3,
            "type": "Biographer",
            "works": {
                "tlg001": {
                    "title": "Vitae philosophorum",
                    "urn": "urn:cts:greekLit:tlg0004.tlg001",
                    "language": "grc",
                    "editions": {
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
                    "translations": {
                        "perseus-eng2": {
                            "urn": "urn:cts:greekLit:tlg0004.tlg001.perseus-eng2",
                            "label": "Lives of Eminent Philosophers",
                            "description": "Diogenes Laertius. Hicks, R. D., editor.",
                            "lang": "eng",
                            "language": "English",
                            "translator": "R. D. Hicks",
                            "path": "tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
                            "filename": "tlg0004.tlg001.perseus-eng2.xml"
                        }
                    }
                }
            }
        },
        "tlg0085": {
            "name": "Herodotus",
            "urn": "urn:cts:greekLit:tlg0085",
            "century": 5,
            "type": "Historian",
            "works": {
                "tlg001": {
                    "title": "Histories",
                    "urn": "urn:cts:greekLit:tlg0085.tlg001",
                    "language": "grc",
                    "editions": {
                        "perseus-grc2": {
                            "urn": "urn:cts:greekLit:tlg0085.tlg001.perseus-grc2",
                            "label": "Ἱστορίαι",
                            "description": "Herodotus with an English translation.",
                            "lang": "grc",
                            "language": "Greek",
                            "editor": "A. D. Godley",
                            "path": "tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml",
                            "filename": "tlg0085.tlg001.perseus-grc2.xml"
                        }
                    },
                    "translations": {
                        "perseus-eng2": {
                            "urn": "urn:cts:greekLit:tlg0085.tlg001.perseus-eng2",
                            "label": "Histories",
                            "description": "Herodotus with an English translation.",
                            "lang": "eng",
                            "language": "English",
                            "translator": "A. D. Godley",
                            "path": "tlg0085/tlg001/tlg0085.tlg001.perseus-eng2.xml",
                            "filename": "tlg0085.tlg001.perseus-eng2.xml"
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_catalog_file(tmp_path: Path, sample_catalog_data: Dict[str, Any]) -> Path:
    """Create a sample catalog file for testing."""
    catalog_file = tmp_path / "test_integrated_catalog.json"
    with open(catalog_file, "w", encoding="utf-8") as f:
        json.dump(sample_catalog_data, f, indent=2, ensure_ascii=False)
    return catalog_file


@pytest.fixture
def expected_texts() -> List[Text]:
    """Create expected Text objects for testing."""
    return [
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
            title="Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
            author="Diogenes Laertius",
            language="Greek",
            metadata={
                "urn": "urn:cts:greekLit:tlg0004.tlg001.perseus-grc2",
                "label": "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
                "description": "Diogenes Laertius. Hicks, R. D., editor.",
                "editor": "R. D. Hicks",
                "work_id": "tlg001",
                "author_id": "tlg0004",
                "edition_id": "perseus-grc2",
            }
        ),
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
            title="Lives of Eminent Philosophers",
            author="Diogenes Laertius",
            language="English",
            metadata={
                "urn": "urn:cts:greekLit:tlg0004.tlg001.perseus-eng2",
                "label": "Lives of Eminent Philosophers",
                "description": "Diogenes Laertius. Hicks, R. D., editor.",
                "translator": "R. D. Hicks",
                "work_id": "tlg001",
                "author_id": "tlg0004",
                "translation_id": "perseus-eng2",
            }
        ),
        Text(
            path="tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml",
            title="Ἱστορίαι",
            author="Herodotus",
            language="Greek",
            metadata={
                "urn": "urn:cts:greekLit:tlg0085.tlg001.perseus-grc2",
                "label": "Ἱστορίαι",
                "description": "Herodotus with an English translation.",
                "editor": "A. D. Godley",
                "work_id": "tlg001",
                "author_id": "tlg0085",
                "edition_id": "perseus-grc2",
            }
        ),
        Text(
            path="tlg0085/tlg001/tlg0085.tlg001.perseus-eng2.xml",
            title="Histories",
            author="Herodotus",
            language="English",
            metadata={
                "urn": "urn:cts:greekLit:tlg0085.tlg001.perseus-eng2",
                "label": "Histories",
                "description": "Herodotus with an English translation.",
                "translator": "A. D. Godley",
                "work_id": "tlg001",
                "author_id": "tlg0085",
                "translation_id": "perseus-eng2",
            }
        )
    ]


@pytest.fixture
def mock_catalog_service(sample_catalog_file: Path) -> CatalogService:
    """Create a catalog service using the test catalog file."""
    service = CatalogService(catalog_path=str(sample_catalog_file))
    return service


@pytest.fixture
def sample_xml_content() -> str:
    """Create a sample XML file content in TEI format."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Sample Text</title>
        <author>Test Author</author>
        <editor>Test Editor</editor>
      </titleStmt>
      <publicationStmt>
        <publisher>Test Publisher</publisher>
        <date>2023</date>
      </publicationStmt>
      <sourceDesc>
        <p>Test Source</p>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text xml:lang="eng">
    <body>
      <div type="textpart" n="1">
        <p>This is section 1 of the text.</p>
        <div type="textpart" n="1">
          <p>This is section 1.1 of the text.</p>
        </div>
        <div type="textpart" n="2">
          <p>This is section 1.2 of the text.</p>
        </div>
      </div>
      <div type="textpart" n="2">
        <p>This is section 2 of the text.</p>
        <div type="textpart" n="1">
          <p>This is section 2.1 of the text.</p>
        </div>
      </div>
    </body>
  </text>
</TEI>"""


@pytest.fixture
def sample_xml_file(test_data_dir: Path, sample_xml_content: str) -> Path:
    """Create a sample XML file for testing."""
    # Create directory structure
    author_dir = test_data_dir / "tlg0004"
    author_dir.mkdir(exist_ok=True)
    work_dir = author_dir / "tlg001"
    work_dir.mkdir(exist_ok=True)
    
    # Create file
    xml_file = work_dir / "tlg0004.tlg001.perseus-grc2.xml"
    with open(xml_file, "w", encoding="utf-8") as f:
        f.write(sample_xml_content)
    
    return xml_file


@pytest.fixture
def mock_xml_service(test_data_dir: Path) -> XMLService:
    """Create an XML service using the test data directory."""
    return XMLService(data_dir=str(test_data_dir))


@pytest.fixture
def client() -> Generator:
    """Create a TestClient for testing the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client 