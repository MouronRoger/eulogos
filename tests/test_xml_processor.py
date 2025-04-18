"""Tests for the XMLProcessorService with catalog path resolution."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models.catalog import Text

from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService


@pytest.fixture
def mock_catalog_service():
    """Create a mock catalog service for testing."""
    mock_service = MagicMock(spec=CatalogService)

    # Setup test data with path from catalog
    test_text = Text(
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


