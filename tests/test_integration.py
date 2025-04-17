"""Integration tests for the Eulogos export functionality.

This module contains end-to-end tests that verify:
- Complete export workflows across different formats
- API endpoint functionality
- Backward compatibility with legacy adapters
- Export performance and caching
- File cleanup and resource management
"""

import tempfile

from fastapi.testclient import TestClient

from app.main import app
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_export_service import EnhancedExportService
from app.services.enhanced_xml_service import EnhancedXMLService


def test_end_to_end_export(test_settings, sample_xml_file):
    """Test an end-to-end export workflow."""
    # Set up services
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    # Create temporary directory for exports
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up export service
        export_service = EnhancedExportService(
            catalog_service=catalog_service, xml_service=xml_service, settings=test_settings, output_dir=temp_dir
        )

        # Export to different formats
        html_path = export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        md_path = export_service.export_to_markdown("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        latex_path = export_service.export_to_latex("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")

        # Verify files exist
        assert html_path.exists()
        assert md_path.exists()
        assert latex_path.exists()

        # Verify file contents
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            assert "<!DOCTYPE html>" in html_content
            assert "Homeri Ilias" in html_content
            assert "Book 1" in html_content

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            assert "# Homeri Ilias" in md_content
            assert "Book 1" in md_content

        with open(latex_path, "r", encoding="utf-8") as f:
            latex_content = f.read()
            assert "\\documentclass{article}" in latex_content
            assert "Homeri Ilias" in latex_content
            assert "\\section" in latex_content


def test_api_endpoints(test_settings, sample_xml_file):
    """Test the export API endpoints."""
    # Create test client
    client = TestClient(app)

    # Test getting available formats
    response = client.get("/export/formats")
    assert response.status_code == 200
    formats = response.json()["formats"]
    assert len(formats) == 3
    assert any(f["id"] == "html" for f in formats)
    assert any(f["id"] == "markdown" for f in formats)
    assert any(f["id"] == "latex" for f in formats)

    # Test HTML export
    options = {"reference": "1.1", "include_metadata": True, "custom_css": "body { font-size: 14px; }"}
    response = client.post("/export/urn:cts:greekLit:tlg0012.tlg001.perseus-grc1/html", json=options)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "Homeri Ilias" in response.text
    assert "Book 1" in response.text

    # Test Markdown export
    response = client.post("/export/urn:cts:greekLit:tlg0012.tlg001.perseus-grc1/markdown", json=options)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert "# Homeri Ilias" in response.text
    assert "Book 1" in response.text

    # Test LaTeX export
    response = client.post("/export/urn:cts:greekLit:tlg0012.tlg001.perseus-grc1/latex", json=options)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-latex; charset=utf-8"
    assert "\\documentclass{article}" in response.text
    assert "Homeri Ilias" in response.text

    # Test invalid URN
    response = client.post("/export/invalid-urn/html", json=options)
    assert response.status_code == 400
    assert "Invalid URN" in response.json()["detail"]

    # Test non-existent text
    response = client.post("/export/urn:cts:greekLit:tlg0013.tlg001.perseus-grc1/html", json=options)
    assert response.status_code == 404
    assert "Text not found" in response.json()["detail"]


def test_backward_compatibility(test_settings, sample_xml_file):
    """Test backward compatibility with existing code."""
    from app.services.catalog_service_adapter import CatalogServiceAdapter
    from app.services.xml_processor_adapter import XMLProcessorServiceAdapter

    # Set up services
    enhanced_catalog_service = EnhancedCatalogService(settings=test_settings)
    enhanced_xml_service = EnhancedXMLService(catalog_service=enhanced_catalog_service, settings=test_settings)

    # Create adapters
    catalog_adapter = CatalogServiceAdapter(enhanced_service=enhanced_catalog_service)
    xml_adapter = XMLProcessorServiceAdapter(
        enhanced_service=enhanced_xml_service, catalog_service=enhanced_catalog_service
    )

    # Use adapter methods
    # Test catalog adapter
    text = catalog_adapter.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert text is not None
    assert text.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test XML adapter
    root = xml_adapter.load_xml("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert root is not None

    # Test reference extraction
    refs = xml_adapter.extract_references(root)
    assert refs is not None
    assert len(refs) > 0

    # Test HTML transformation
    html = xml_adapter.transform_to_html(root)
    assert html is not None
    assert "Book 1" in html


def test_export_performance(test_settings, sample_xml_file):
    """Test export performance with caching."""
    import time

    # Set up services
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    with tempfile.TemporaryDirectory() as temp_dir:
        export_service = EnhancedExportService(
            catalog_service=catalog_service, xml_service=xml_service, settings=test_settings, output_dir=temp_dir
        )

        # First export (cold cache)
        start_time = time.time()
        export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        cold_time = time.time() - start_time

        # Second export (warm cache)
        start_time = time.time()
        export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        warm_time = time.time() - start_time

        # Verify that warm cache is faster
        assert warm_time < cold_time


def test_export_cleanup(test_settings, sample_xml_file):
    """Test that exported files are cleaned up properly."""
    # Set up services
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    # Create temporary directory for exports
    temp_dir = tempfile.mkdtemp(prefix="eulogos_export_test_")
    export_service = EnhancedExportService(
        catalog_service=catalog_service, xml_service=xml_service, settings=test_settings, output_dir=temp_dir
    )

    # Export a file
    html_path = export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert html_path.exists()

    # Clean up
    from app.routers.export import cleanup_export_file

    cleanup_export_file(html_path)

    # Verify file and directory are gone
    assert not html_path.exists()
    assert not html_path.parent.exists()
