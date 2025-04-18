"""Tests for export service."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


from app.services.export_service import ExportService
from app.services.xml_processor_service import XMLProcessorService


class MockXMLRoot:
    """Mock XML root element for testing."""

    def __init__(self, references=None):
        """Initialize with references."""
        self.references = references or {}

    def findall(self, xpath, namespaces=None):
        """Mock findall method."""
        return []

    def itertext(self):
        """Mock itertext method."""
        return ["This is test text with some Greek: Θεός εἶναι τὸ ἀθάνατον."]

    def get(self, attr):
        """Mock get method."""
        if attr == "n":
            return "1"
        return None


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def xml_processor():
    """Create a mock XMLProcessorService."""
    processor = MagicMock(spec=XMLProcessorService)

    # Mock load_xml to return a mock XML root
    processor.load_xml.return_value = MockXMLRoot()

    # Mock extract_references to return a mock references dict
    references = {
        "1": MockXMLRoot(),
        "1.1": MockXMLRoot(),
        "1.2": MockXMLRoot(),
    }
    processor.extract_references.return_value = references

    # Mock transform_to_html to return a simple HTML string
    processor.transform_to_html.return_value = """
    <div class="text-part" data-reference="1">
        <div class="section-num"><a href="#ref=1">1</a></div>
        <div class="content">
            <span class="token" data-token="This" data-token-index="1">This</span>
            <span class="token" data-token="is" data-token-index="2">is</span>
            <span class="token" data-token="test" data-token-index="3">test</span>
            <span class="token" data-token="text" data-token-index="4">text</span>
            <span class="token" data-token="with" data-token-index="5">with</span>
            <span class="token" data-token="some" data-token-index="6">some</span>
            <span class="token" data-token="Greek" data-token-index="7">Greek</span>
            <span class="punct">:</span>
            <span class="token" data-token="Θεός" data-token-index="8">Θεός</span>
            <span class="token" data-token="εἶναι" data-token-index="9">εἶναι</span>
            <span class="token" data-token="τὸ" data-token-index="10">τὸ</span>
            <span class="token" data-token="ἀθάνατον" data-token-index="11">ἀθάνατον</span>
            <span class="punct">.</span>
        </div>
    </div>
    """

    return processor


@pytest.fixture
def export_service(xml_processor, temp_dir):
    """Create an ExportService instance for testing."""
    return ExportService(xml_processor, temp_dir)


@pytest.fixture
def sample_urn():
    """Create a sample URN for testing."""
    return "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"


class TestExportService:
    """Tests for ExportService."""

    