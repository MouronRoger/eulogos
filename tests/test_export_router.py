"""Tests for export router."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.export import get_export_service
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
    for format_name in ["pdf", "epub", "mobi", "markdown", "docx", "latex", "html"]:
        method_name = f"export_to_{format_name}"
        mock_method = MagicMock(return_value=Path(f"/tmp/test_export.{format_name}"))
        setattr(service, method_name, mock_method)

    return service


@pytest.fixture
def app_with_mock_service(mock_export_service):
    """Set up the app with a mock export service."""
    app.dependency_overrides[get_export_service] = lambda: mock_export_service
    yield app
    app.dependency_overrides = {}


class TestExportRouter:
    """Tests for the export router."""

    def test_get_export_formats(self, client):
        """Test getting export formats."""
        response = client.get("/export/formats")
        assert response.status_code == 200
        formats = response.json()
        assert len(formats) == 7
        assert {f["id"] for f in formats} == {"pdf", "epub", "mobi", "markdown", "docx", "latex", "html"}
        assert all("name" in f for f in formats)
        assert all("description" in f for f in formats)
        assert all("content_type" in f for f in formats)
        assert all("extension" in f for f in formats)

    def test_get_export_options(self, client):
        """Test getting export options."""
        response = client.get("/export/options")
        assert response.status_code == 200
        options = response.json()

        # Check common option IDs
        option_ids = {o["id"] for o in options}
        expected_ids = {"title", "creators", "reference", "include_metadata", "filename", "custom_css"}
        assert option_ids >= expected_ids

        # Check option structure
        assert all("id" in o for o in options)
        assert all("name" in o for o in options)
        assert all("description" in o for o in options)
        assert all("type" in o for o in options)

    @patch("os.path.exists", return_value=True)
    @patch("fastapi.responses.FileResponse.__init__", return_value=None)
    @patch("fastapi.responses.FileResponse.__new__", return_value=MagicMock())
    def test_export_text(self, mock_new, mock_init, mock_exists, client, app_with_mock_service, mock_export_service):
        """Test exporting text in various formats."""
        urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"

        for format_name in ["pdf", "epub", "mobi", "markdown", "docx", "latex", "html"]:
            response = client.get(f"/export/{urn}?format={format_name}")
            assert response.status_code == 200

            # Check that the correct export method was called
            method = getattr(mock_export_service, f"export_to_{format_name}")
            assert method.called

            # Check that FileResponse was created with correct parameters
            mock_init.assert_called()
            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["path"] == f"/tmp/test_export.{format_name}"
            assert format_name in call_kwargs["media_type"]

    @patch("os.path.exists", return_value=True)
    @patch("fastapi.responses.FileResponse.__init__", return_value=None)
    @patch("fastapi.responses.FileResponse.__new__", return_value=MagicMock())
    def test_export_text_with_options(
        self, mock_new, mock_init, mock_exists, client, app_with_mock_service, mock_export_service
    ):
        """Test exporting text with various options."""
        urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"

        options = {
            "format": "pdf",
            "title": "Custom Title",
            "creators": "Author 1, Author 2",
            "reference": "1.1-1.10",
            "include_metadata": "true",
            "filename": "custom_filename",
            "custom_css": "body { font-family: Arial; }",
        }

        url = f"/export/{urn}?" + "&".join([f"{k}={v}" for k, v in options.items()])
        response = client.get(url)
        assert response.status_code == 200

        # Check that the export method was called with correct options
        mock_export_service.export_to_pdf.assert_called_once()
        call_args, call_kwargs = mock_export_service.export_to_pdf.call_args

        # Check that URN is correct
        assert call_args[0].value == urn

        # Check that options are correct
        options_dict = call_args[1]
        assert options_dict["title"] == "Custom Title"
        assert options_dict["creators"] == ["Author 1", "Author 2"]
        assert options_dict["reference"] == "1.1-1.10"
        assert options_dict["include_metadata"] is True
        assert options_dict["filename"] == "custom_filename"
        assert options_dict["custom_css"] == "body { font-family: Arial; }"

        # Check that FileResponse was created with correct parameters
        mock_init.assert_called()
        assert mock_init.call_args[1]["path"] == "/tmp/test_export.pdf"

    def test_export_text_invalid_format(self, client, app_with_mock_service):
        """Test exporting text with an invalid format."""
        urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"

        response = client.get(f"/export/{urn}?format=invalid")
        assert response.status_code == 400
        assert "Unsupported format" in response.json()["detail"]

    @patch.object(ExportService, "export_to_pdf", side_effect=ImportError("Missing dependency"))
    def test_export_text_missing_dependency(self, mock_export, client):
        """Test handling missing dependencies."""
        urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"

        response = client.get(f"/export/{urn}?format=pdf")
        assert response.status_code == 500
        assert "Missing dependency" in response.json()["detail"]

    @patch.object(ExportService, "export_to_pdf", side_effect=FileNotFoundError("File not found"))
    def test_export_text_file_not_found(self, mock_export, client):
        """Test handling file not found errors."""
        urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"

        response = client.get(f"/export/{urn}?format=pdf")
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    @patch.object(ExportService, "export_to_pdf", side_effect=ValueError("Invalid value"))
    def test_export_text_value_error(self, mock_export, client):
        """Test handling validation errors."""
        urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"

        response = client.get(f"/export/{urn}?format=pdf")
        assert response.status_code == 400
        assert "Invalid value" in response.json()["detail"]
