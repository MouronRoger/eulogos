"""Tests for export service."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models.urn import URN
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
    return URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")


class TestExportService:
    """Tests for ExportService."""

    def test_init(self, xml_processor, temp_dir):
        """Test initialization of ExportService."""
        service = ExportService(xml_processor, temp_dir)
        assert service.xml_processor == xml_processor
        assert service.output_dir == temp_dir

        # Test default output_dir
        service = ExportService(xml_processor)
        assert service.output_dir == tempfile.gettempdir()

    def test_get_metadata(self, export_service, sample_urn):
        """Test getting metadata."""
        metadata = export_service._get_metadata(sample_urn)
        assert metadata["title"] == "Text tlg0012.tlg001"
        assert metadata["language"] == "grc"
        assert metadata["urn"] == sample_urn.value

        # Test with custom options
        options = {"title": "Custom Title", "creators": ["Author 1", "Author 2"]}
        metadata = export_service._get_metadata(sample_urn, options)
        assert metadata["title"] == "Custom Title"
        assert metadata["creators"] == ["Author 1", "Author 2"]

    def test_get_output_path(self, export_service, sample_urn, temp_dir):
        """Test getting output path."""
        # Test default filename
        path = export_service._get_output_path(sample_urn, "pdf")
        expected = os.path.join(temp_dir, "tlg0012_tlg001_perseus-grc2.pdf")
        assert path == expected

        # Test custom filename
        options = {"filename": "custom_name"}
        path = export_service._get_output_path(sample_urn, "pdf", options)
        expected = os.path.join(temp_dir, "custom_name.pdf")
        assert path == expected

        # Test custom output directory
        custom_dir = os.path.join(temp_dir, "custom_dir")
        options = {"output_dir": custom_dir}
        path = export_service._get_output_path(sample_urn, "pdf", options)
        expected = os.path.join(custom_dir, "tlg0012_tlg001_perseus-grc2.pdf")
        assert path == expected
        assert os.path.isdir(custom_dir)

    def test_get_html_content(self, export_service, sample_urn):
        """Test getting HTML content."""
        content = export_service._get_html_content(sample_urn)
        assert '<div class="text-part"' in content
        assert 'data-token="Θεός"' in content

        # Test with reference option
        options = {"reference": "1.1"}
        export_service._get_html_content(sample_urn, options)
        export_service.xml_processor.transform_to_html.assert_called_with(
            export_service.xml_processor.load_xml.return_value, "1.1"
        )

    def test_escape_latex(self, export_service):
        """Test escaping LaTeX special characters."""
        text = "Test with special chars: & % $ # _ { } ~ ^ \\ < >"
        escaped = export_service._escape_latex(text)
        assert "\\&" in escaped
        assert "\\%" in escaped
        assert "\\$" in escaped
        assert "\\#" in escaped
        assert "\\_" in escaped
        assert "\\{" in escaped
        assert "\\}" in escaped
        assert "\\textasciitilde{}" in escaped
        assert "\\textasciicircum{}" in escaped
        assert "\\textbackslash{}" in escaped
        assert "\\textless{}" in escaped
        assert "\\textgreater{}" in escaped

    def test_wrap_greek_in_textgreek(self, export_service):
        r"""Test wrapping Greek text in \textgreek{}."""
        # Text with Greek
        text = "Text with Greek: Θεός εἶναι τὸ ἀθάνατον."
        wrapped = export_service._wrap_greek_in_textgreek(text)
        assert wrapped == "\\textgreek{Text with Greek: Θεός εἶναι τὸ ἀθάνατον.}"

        # Text without Greek
        text = "Text without Greek."
        wrapped = export_service._wrap_greek_in_textgreek(text)
        assert wrapped == text

    @patch("weasyprint.HTML")
    def test_export_to_pdf(self, mock_html, export_service, sample_urn, temp_dir):
        """Test exporting to PDF."""
        # Mock WeasyPrint
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        # Export to PDF
        result = export_service.export_to_pdf(sample_urn)

        # Verify calls and result
        assert mock_html.called
        assert mock_html_instance.write_pdf.called
        assert result.suffix == ".pdf"
        assert result.parent == Path(temp_dir)

    @patch("ebooklib.epub.write_epub")
    def test_export_to_epub(self, mock_write_epub, export_service, sample_urn, temp_dir):
        """Test exporting to ePub."""
        # Export to ePub
        result = export_service.export_to_epub(sample_urn)

        # Verify calls and result
        assert mock_write_epub.called
        assert result.suffix == ".epub"
        assert result.parent == Path(temp_dir)

    @patch("subprocess.run")
    @patch("ebooklib.epub.write_epub")
    def test_export_to_mobi(self, mock_write_epub, mock_run, export_service, sample_urn, temp_dir):
        """Test exporting to MOBI."""
        # Export to MOBI
        result = export_service.export_to_mobi(sample_urn)

        # Verify calls and result
        assert mock_write_epub.called
        assert mock_run.called
        assert result.suffix == ".mobi"
        assert result.parent == Path(temp_dir)

    @patch("html2text.HTML2Text")
    def test_export_to_markdown(self, mock_html2text, export_service, sample_urn, temp_dir):
        """Test exporting to Markdown."""
        # Mock html2text
        mock_h2t = MagicMock()
        mock_h2t.handle.return_value = "# Test Markdown\n\nSome content."
        mock_html2text.return_value = mock_h2t

        # Export to Markdown
        result = export_service.export_to_markdown(sample_urn)

        # Verify calls and result
        assert mock_html2text.called
        assert mock_h2t.handle.called
        assert result.suffix == ".md"
        assert result.parent == Path(temp_dir)

        # Check file content
        with open(result, "r", encoding="utf-8") as f:
            content = f.read()
            assert "# Test" in content

    @patch("docx.Document")
    def test_export_to_docx(self, mock_document, export_service, sample_urn, temp_dir):
        """Test exporting to DOCX."""
        # Mock Document
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        # Export to DOCX
        result = export_service.export_to_docx(sample_urn)

        # Verify calls and result
        assert mock_document.called
        assert mock_doc.save.called
        assert result.suffix == ".docx"
        assert result.parent == Path(temp_dir)

    def test_export_to_latex(self, export_service, sample_urn, temp_dir):
        """Test exporting to LaTeX."""
        # Export to LaTeX
        result = export_service.export_to_latex(sample_urn)

        # Verify result
        assert result.suffix == ".tex"
        assert result.parent == Path(temp_dir)

        # Check file content
        with open(result, "r", encoding="utf-8") as f:
            content = f.read()
            assert "\\documentclass{article}" in content
            assert "\\usepackage{fontspec}" in content
            assert "\\usepackage{polyglossia}" in content
            assert "\\setotherlanguage{greek}" in content
            assert "\\begin{document}" in content
            assert "\\end{document}" in content

    def test_export_to_html(self, export_service, sample_urn, temp_dir):
        """Test exporting to HTML."""
        # Export to HTML
        result = export_service.export_to_html(sample_urn)

        # Verify result
        assert result.suffix == ".html"
        assert result.parent == Path(temp_dir)

        # Check file content
        with open(result, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert '<html lang="grc">' in content
            assert '<meta charset="UTF-8">' in content
            assert "<style>" in content
            assert 'data-token="Θεός"' in content
            assert "</html>" in content
