"""Tests for export router."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_catalog_service, get_xml_service
from app.services.export_service import ExportService


@pytest.fixture
def client():
    """Create a test client for the router."""
    return TestClient(app)


@pytest.fixture
def mock_export_service():
    """Create a mock export service that returns predictable paths."""
    service = MagicMock(spec=ExportService)

    # Mock export methods to return a path
    for format_name in ["pdf", "epub", "markdown", "latex", "html"]:
        method_name = f"export_to_{format_name}"
        mock_method = MagicMock(return_value=Path(f"/tmp/test_export.{format_name}"))
        setattr(service, method_name, mock_method)

    return service


@pytest.fixture
def app_with_mock_service(mock_export_service):
    """Set up the app with a mock export service."""
    # Using the new dependency paths directly from app.dependencies
    app.dependency_overrides[get_catalog_service] = lambda: MagicMock()
    app.dependency_overrides[get_xml_service] = lambda: MagicMock()
    yield app
    app.dependency_overrides = {}


class TestExportRouter:
    """Tests for the export router."""

    