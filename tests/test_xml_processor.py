"""Tests for the XMLProcessorService with catalog path resolution."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models.catalog import Text
from app.models.urn import URN
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService


@pytest.fixture
def mock_catalog_service():
    """Create a mock catalog service for testing."""
    mock_service = MagicMock(spec=CatalogService)

    # Setup test data with path from catalog
    test_text = Text(
        urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
        group_name="Homer",
        work_name="Iliad",
        language="grc",
        wordcount=100000,
        author_id="tlg0012",
        path="tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml",  # Path from catalog
    )

    # Configure the mock to return the test text
    mock_service.get_text_by_urn.return_value = test_text

    return mock_service


@pytest.fixture
def xml_processor(mock_catalog_service):
    """Create an XMLProcessorService instance for testing."""
    return XMLProcessorService(data_path="data", catalog_service=mock_catalog_service)


@pytest.fixture
def xml_processor_no_catalog():
    """Create an XMLProcessorService without a catalog service."""
    return XMLProcessorService(data_path="data")


def test_resolve_urn_to_file_path_with_catalog(xml_processor, mock_catalog_service):
    """Test resolving URN to file path using the catalog service."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

    # Call the method
    file_path = xml_processor.resolve_urn_to_file_path(urn)

    # Verify the catalog service was called to get the text object
    mock_catalog_service.get_text_by_urn.assert_called_once_with(urn.value)

    # Get the text object returned by the mock
    text = mock_catalog_service.get_text_by_urn.return_value
    
    # Verify we're using the path from the text object
    assert text.path == "tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml"
    
    # Verify the path was correctly resolved using the text object's path
    expected_path = Path("data") / text.path
    assert file_path == expected_path


def test_resolve_urn_to_file_path_no_text(xml_processor, mock_catalog_service):
    """Test resolving URN when text is not found in catalog."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
    
    # Configure mock to return None (text not found)
    mock_catalog_service.get_text_by_urn.return_value = None
    
    # Verify that FileNotFoundError is raised
    with pytest.raises(FileNotFoundError) as excinfo:
        xml_processor.resolve_urn_to_file_path(urn)
    
    assert "not found in catalog" in str(excinfo.value)
    mock_catalog_service.get_text_by_urn.assert_called_once_with(urn.value)


def test_resolve_urn_to_file_path_no_path(xml_processor, mock_catalog_service):
    """Test resolving URN when text has no path."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
    
    # Configure mock to return text without path
    text_without_path = Text(
        urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
        group_name="Homer",
        work_name="Iliad",
        language="grc",
        wordcount=100000,
        author_id="tlg0012",
        path=None,  # No path set
    )
    mock_catalog_service.get_text_by_urn.return_value = text_without_path
    
    # Verify that FileNotFoundError is raised
    with pytest.raises(FileNotFoundError) as excinfo:
        xml_processor.resolve_urn_to_file_path(urn)
    
    assert "has no valid path" in str(excinfo.value)
    mock_catalog_service.get_text_by_urn.assert_called_once_with(urn.value)


def test_resolve_urn_to_file_path_fallback(xml_processor_no_catalog):
    """Test the fallback behavior when no catalog service is available."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

    # Patch the logging to avoid warnings in test output
    with patch("loguru.logger.warning") as mock_warning:
        # Call the method
        file_path = xml_processor_no_catalog.resolve_urn_to_file_path(urn)

        # Verify a warning was logged
        mock_warning.assert_called_once()
        assert "single source of truth" in mock_warning.call_args[0][0]

    # Verify the fallback path was correctly constructed
    expected_path = Path("data/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml")
    assert file_path == expected_path


def test_load_xml_with_catalog(xml_processor, mock_catalog_service):
    """Test loading XML when using catalog for path resolution."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

    # Mock the XML parsing
    with patch("xml.etree.ElementTree.parse") as mock_parse:
        # Mock the file exists check
        with patch.object(Path, "exists", return_value=True):
            mock_root = MagicMock()
            mock_parse.return_value.getroot.return_value = mock_root

            # Call the method
            result = xml_processor.load_xml(urn)

            # Verify the catalog service was used for path resolution
            mock_catalog_service.get_text_by_urn.assert_called_once_with(urn.value)

            # Get the text object and verify path usage
            text = mock_catalog_service.get_text_by_urn.return_value
            assert text.path == "tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml"

            # Verify the correct file was parsed using path from catalog
            expected_path = str(Path("data") / text.path)
            mock_parse.assert_called_once_with(expected_path)

            # Verify the result
            assert result == mock_root


def test_load_xml_file_not_found(xml_processor, mock_catalog_service):
    """Test loading XML when the file doesn't exist."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

    # Mock the file exists check to return False
    with patch.object(Path, "exists", return_value=False):
        # Expect a FileNotFoundError
        with pytest.raises(FileNotFoundError) as excinfo:
            xml_processor.load_xml(urn)

        # Verify the error message contains the path from the text object
        text = mock_catalog_service.get_text_by_urn.return_value
        assert text.path in str(excinfo.value)
        assert "XML file not found" in str(excinfo.value)


def test_xml_processor_integration():
    """Integration test for XMLProcessorService with a real CatalogService.

    This test needs to be run with access to actual data files.
    """
    # Skip if running in CI or without data files
    if os.environ.get("CI") == "true" or not os.path.exists("data"):
        pytest.skip("Skipping integration test without data files")

    # Create a real catalog service
    catalog_service = CatalogService(catalog_path="integrated_catalog.json", data_dir="data")

    # Create an XML processor that uses the catalog
    xml_processor = XMLProcessorService(data_path="data", catalog_service=catalog_service)

    # Test a known URN
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

    try:
        # Try to resolve the path
        file_path = xml_processor.resolve_urn_to_file_path(urn)

        # Check if the path exists
        if file_path.exists():
            # Try to load the XML
            xml_root = xml_processor.load_xml(urn)

            # If we get here, the XML was successfully loaded
            assert xml_root is not None

            # Try to extract references
            references = xml_processor.extract_references(xml_root)
            assert isinstance(references, dict)
        else:
            # Skip if the file doesn't exist, but don't fail the test
            pytest.skip(f"Test file not found: {file_path}")
    except Exception as e:
        # Only fail if it's not a file not found error
        if not isinstance(e, FileNotFoundError):
            raise
        pytest.skip(f"Test file not found: {e}")
