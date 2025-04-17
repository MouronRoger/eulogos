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


def test_large_document_export(services, large_xml_file):
    """Test exporting a large document."""
    _, _, export_service = services
    urn = "urn:cts:greekLit:tlg0012.tlg001.large-test"

    with TestPerformanceMetrics("large_document_export"):
        # Export to different formats
        html_path = export_service.export_to_html(urn)
        md_path = export_service.export_to_markdown(urn)
        latex_path = export_service.export_to_latex(urn)

        # Verify files exist and have content
        assert html_path.exists()
        assert md_path.exists()
        assert latex_path.exists()

        # Check file sizes
        assert os.path.getsize(html_path) > 0
        assert os.path.getsize(md_path) > 0
        assert os.path.getsize(latex_path) > 0


@pytest.mark.asyncio
async def test_concurrent_exports(services, large_xml_file):
    """Test concurrent export operations."""
    _, _, export_service = services
    urn = "urn:cts:greekLit:tlg0012.tlg001.large-test"

    async def export_task(format_type: str) -> Path:
        if format_type == "html":
            return export_service.export_to_html(urn)
        elif format_type == "markdown":
            return export_service.export_to_markdown(urn)
        else:
            return export_service.export_to_latex(urn)

    with TestPerformanceMetrics("concurrent_exports"):
        # Run exports concurrently
        tasks = [export_task("html"), export_task("markdown"), export_task("latex")]
        results = await asyncio.gather(*tasks)

        # Verify all exports completed successfully
        assert all(path.exists() for path in results)


def test_edge_cases(services):
    """Test edge cases and error conditions."""
    _, _, export_service = services

    # Test invalid URN
    with pytest.raises(ValueError):
        export_service.export_to_html("invalid:urn")

    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg999.test")

    # Test empty document
    # TODO: Implement test for empty document

    # Test malformed XML
    # TODO: Implement test for malformed XML


def test_export_with_options(services, large_xml_file):
    """Test export with various options."""
    _, _, export_service = services
    urn = "urn:cts:greekLit:tlg0012.tlg001.large-test"

    options = {
        "reference": "1.1-1.10",
        "filename": "custom_export",
        "include_metadata": True,
        "custom_css": "body { font-size: 14px; }",
    }

    with TestPerformanceMetrics("export_with_options"):
        html_path = export_service.export_to_html(urn, options=options)
        assert html_path.exists()
        assert html_path.name == "custom_export.html"

        # Verify content
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "font-size: 14px" in content
            assert "Book 1" in content


def test_resource_limits(services, large_xml_file):
    """Test behavior under resource constraints."""
    _, _, export_service = services
    urn = "urn:cts:greekLit:tlg0012.tlg001.large-test"

    # Set low memory limit
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    new_limit = 1024 * 1024 * 100  # 100MB
    try:
        resource.setrlimit(resource.RLIMIT_AS, (new_limit, hard))

        # Attempt export under constrained resources
        with pytest.raises(MemoryError):
            export_service.export_to_html(urn)
    finally:
        # Restore original limit
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))


@pytest.mark.benchmark
def test_export_performance_benchmark(benchmark, services, large_xml_file):
    """Benchmark export performance."""
    _, _, export_service = services
    urn = "urn:cts:greekLit:tlg0012.tlg001.large-test"

    def run_export():
        return export_service.export_to_html(urn)

    # Run benchmark
    result = benchmark(run_export)
    assert result.exists()


def test_network_failure_simulation(services, monkeypatch):
    """Test behavior during network failures."""
    _, _, export_service = services

    def mock_network_error(*args, **kwargs):
        raise ConnectionError("Simulated network failure")

    # Patch network-dependent operations
    monkeypatch.setattr(export_service.catalog_service, "resolve_file_path", mock_network_error)

    with pytest.raises(ConnectionError):
        export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.test")
