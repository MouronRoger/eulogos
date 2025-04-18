"""Tests for URN to file path resolution."""

from pathlib import Path

from app.models.urn import URN
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService
from app.utils.path_utils import resolve_urn_to_path


def test_resolve_urn_to_path_without_catalog():
    """Test resolving URN to path without a catalog service."""
    urn_str = "urn:cts:greekLit:tlg4026.tlg001.1st1K-grc1"
    data_path = Path("data")
    expected_path = data_path / "tlg4026" / "tlg001" / "tlg4026.tlg001.1st1K-grc1.xml"

    # Test the utility function
    path = resolve_urn_to_path(urn=urn_str, data_path=str(data_path))
    assert path == expected_path

    # Test the XMLProcessorService directly
    xml_service = XMLProcessorService(data_path=str(data_path))
    urn_obj = URN(value=urn_str)
    path = xml_service.resolve_urn_to_file_path(urn_obj)
    assert path == expected_path


def test_xml_processor_get_file_path():
    """Test the get_file_path method in XMLProcessorService."""
    urn_str = "urn:cts:greekLit:tlg4026.tlg001.1st1K-grc1"
    data_path = Path("data")
    expected_path = data_path / "tlg4026" / "tlg001" / "tlg4026.tlg001.1st1K-grc1.xml"

    xml_service = XMLProcessorService(data_path=str(data_path))
    path = xml_service.get_file_path(urn_str)
    assert path == expected_path


def test_catalog_service_validate_paths():
    """Test that CatalogService._validate_paths generates correct paths."""
    # Create a minimal catalog service
    catalog_service = CatalogService(catalog_path="integrated_catalog.json", data_dir="data")

    # Create and validate the unified catalog
    catalog_service.create_unified_catalog()  # This triggers path validation

    # Get text by URN
    urn_str = "urn:cts:greekLit:tlg4026.tlg001.1st1K-grc1"
    text = catalog_service.get_text_by_urn(urn_str)

    # Verify the path is correct
    assert text is not None
    assert text.path is not None
    assert "tlg4026/tlg001/tlg4026.tlg001.1st1K-grc1.xml" == text.path


def test_xml_processor_with_catalog():
    """Test XMLProcessorService using catalog for path resolution."""
    urn_str = "urn:cts:greekLit:tlg4026.tlg001.1st1K-grc1"
    data_path = Path("data")
    expected_path = data_path / "tlg4026" / "tlg001" / "tlg4026.tlg001.1st1K-grc1.xml"

    # Create catalog service
    catalog_service = CatalogService(catalog_path="integrated_catalog.json", data_dir=str(data_path))
    catalog_service.create_unified_catalog()

    # Create XML processor with catalog service
    xml_service = XMLProcessorService(data_path=str(data_path), catalog_service=catalog_service)

    # Test path resolution
    urn_obj = URN(value=urn_str)
    path = xml_service.resolve_urn_to_file_path(urn_obj)

    assert path == expected_path

    # Also test the string version
    path2 = xml_service.get_file_path(urn_str)
    assert path2 == expected_path
