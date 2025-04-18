"""Stress and performance tests for the Enhanced Export Service.

This module contains tests that verify the export service's behavior under:
- Large document processing
- Concurrent export operations
- Resource constraints
- Edge cases and error conditions
- Various export options
- Network failures
- Performance benchmarks
"""

import asyncio
import logging
import os
import resource
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_export_service import EnhancedExportService
from app.services.enhanced_xml_service import EnhancedXMLService

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestPerformanceMetrics:
    """Context manager for measuring performance metrics."""

    def __init__(self, test_name: str):
        """Initialize the performance metrics context manager.

        Args:
            test_name: Name of the test being measured
        """
        self.test_name = test_name
        self.start_time = None
        self.start_memory = None

    def __enter__(self):
        """Start measuring performance metrics.

        Returns:
            The context manager instance
        """
        self.start_time = time.time()
        self.start_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop measuring and log performance metrics.

        Args:
            exc_type: Type of exception that occurred, if any
            exc_val: Exception instance that occurred, if any
            exc_tb: Traceback of exception that occurred, if any

        Returns:
            False to not suppress exceptions
        """
        end_time = time.time()
        end_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        duration = end_time - self.start_time
        memory_used = end_memory - self.start_memory

        logger.info(f"Performance metrics for {self.test_name}:")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Memory used: {memory_used / 1024:.2f} MB")

        return False  # Don't suppress exceptions


@pytest.fixture
def large_xml_file(temp_dir):
    """Create a large XML file for stress testing."""
    xml_dir = temp_dir / "data" / "tlg0012" / "tlg001"
    os.makedirs(xml_dir, exist_ok=True)
    xml_path = xml_dir / "tlg0012.tlg001.large-test.xml"

    # Create large TEI XML
    root = ET.Element("{http://www.tei-c.org/ns/1.0}TEI")
    header = ET.SubElement(root, "{http://www.tei-c.org/ns/1.0}teiHeader")
    file_desc = ET.SubElement(header, "{http://www.tei-c.org/ns/1.0}fileDesc")
    title_stmt = ET.SubElement(file_desc, "{http://www.tei-c.org/ns/1.0}titleStmt")
    title = ET.SubElement(title_stmt, "{http://www.tei-c.org/ns/1.0}title")
    title.text = "Large Test Document"

    # Add text element with many books and lines
    text_elem = ET.SubElement(root, "{http://www.tei-c.org/ns/1.0}text")
    body = ET.SubElement(text_elem, "{http://www.tei-c.org/ns/1.0}body")

    # Add 24 books with 1000 lines each
    for book_num in range(1, 25):
        book = ET.SubElement(body, "{http://www.tei-c.org/ns/1.0}div", n=str(book_num), type="book")
        book_title = ET.SubElement(book, "{http://www.tei-c.org/ns/1.0}head")
        book_title.text = f"Book {book_num}"

        for line_num in range(1, 1001):
            line = ET.SubElement(book, "{http://www.tei-c.org/ns/1.0}l", n=str(line_num))
            line.text = f"This is line {line_num} of Book {book_num}"

    # Write to file
    tree = ET.ElementTree(root)
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    return xml_path


@pytest.fixture
def services(test_settings, large_xml_file):
    """Set up services for testing."""
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    with tempfile.TemporaryDirectory() as temp_dir:
        export_service = EnhancedExportService(
            catalog_service=catalog_service, xml_service=xml_service, settings=test_settings, output_dir=temp_dir
        )
        yield catalog_service, xml_service, export_service


def mock_network_error(*args, **kwargs):
        raise ConnectionError("Simulated network failure")

    # Patch network-dependent operations
    monkeypatch.setattr(export_service.catalog_service, "resolve_file_path", mock_network_error)

    with pytest.raises(ConnectionError):
        export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.test")
