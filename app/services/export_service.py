"""Service for exporting texts to various formats."""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from app.models.urn import URN
from app.services.xml_processor_service import XMLProcessorService


class ExportService:
    """Service for exporting texts to various formats."""

    def __init__(self, xml_processor: XMLProcessorService, output_dir: Optional[str] = None):
        """Initialize the export service.

        Args:
            xml_processor: XMLProcessorService instance for processing XML
            output_dir: Optional directory for temporary files
        """
        self.xml_processor = xml_processor
        self.output_dir = output_dir or tempfile.gettempdir()

    def export_to_pdf(self, urn: URN, options: Dict[str, Any] = None) -> Path:
        """Export text to PDF using WeasyPrint.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated PDF file

        Raises:
            ImportError: If WeasyPrint is not installed
            ValueError: If text cannot be found or processed
        """
        try:
            from weasyprint import CSS, HTML
        except ImportError:
            raise ImportError("WeasyPrint is required for PDF export. Install with: pip install weasyprint")

        options = options or {}

        # Get HTML content
        html_content = self._get_html_content(urn, options)

        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as html_file:
            html_file.write(html_content)
            html_path = html_file.name

        try:
            # Define output PDF path
            pdf_path = self._get_output_path(urn, "pdf", options)

            # Create PDF
            css_string = self._get_pdf_css(options)
            HTML(html_path).write_pdf(pdf_path, stylesheets=[CSS(string=css_string)])

            return Path(pdf_path)
        finally:
            # Clean up temporary file
            if os.path.exists(html_path):
                os.unlink(html_path)

    def export_to_epub(self, urn: URN, options: Dict[str, Any] = None) -> Path:
        """Export text to ePub using ebooklib.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated ePub file

        Raises:
            ImportError: If ebooklib is not installed
            ValueError: If text cannot be found or processed
        """
        try:
            from ebooklib import epub
        except ImportError:
            raise ImportError("ebooklib is required for ePub export. Install with: pip install ebooklib")

        options = options or {}

        # Get metadata
        metadata = self._get_metadata(urn, options)

        # Create a new ePub book
        book = epub.EpubBook()

        # Set metadata
        book.set_identifier(urn.value)
        book.set_title(metadata.get("title", "Untitled"))
        book.set_language("grc")  # Greek
        for creator in metadata.get("creators", []):
            book.add_author(creator)

        # Get HTML content
        html_content = self._get_html_content(urn, options)

        # Create chapter
        chapter = epub.EpubHtml(title=metadata.get("title", "Untitled"), file_name="text.xhtml")
        chapter.content = html_content

        # Add chapter to book
        book.add_item(chapter)

        # Define TOC
        book.toc = (epub.Link("text.xhtml", metadata.get("title", "Untitled"), "text"),)

        # Add default NCX and Nav
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Basic spine
        book.spine = ["nav", chapter]

        # Define output ePub path
        epub_path = self._get_output_path(urn, "epub", options)

        # Write ePub file
        epub.write_epub(epub_path, book, {})

        return Path(epub_path)

    def export_to_mobi(self, urn: URN, options: Dict[str, Any] = None) -> Path:
        """Export text to MOBI using Calibre.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated MOBI file

        Raises:
            FileNotFoundError: If Calibre ebook-convert is not installed
            ValueError: If text cannot be found or processed
        """
        options = options or {}

        # First export to ePub
        epub_path = self.export_to_epub(urn, options)

        # Define output MOBI path
        mobi_path = self._get_output_path(urn, "mobi", options)

        # Convert ePub to MOBI using Calibre's ebook-convert
        import subprocess

        try:
            subprocess.run(
                ["ebook-convert", str(epub_path), str(mobi_path)], check=True, capture_output=True, text=True
            )
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            raise FileNotFoundError(
                "Calibre's ebook-convert is required for MOBI export. "
                "Install Calibre and ensure ebook-convert is in your PATH."
            ) from e

        return Path(mobi_path)

    def export_to_markdown(self, urn: URN, options: Dict[str, Any] = None) -> Path:
        """Export text to Markdown.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated Markdown file

        Raises:
            ImportError: If html2text is not installed
            ValueError: If text cannot be found or processed
        """
        try:
            import html2text
        except ImportError:
            raise ImportError("html2text is required for Markdown export. Install with: pip install html2text")

        options = options or {}

        # Get HTML content
        html_content = self._get_html_content(urn, options)

        # Convert HTML to Markdown
        h2t = html2text.HTML2Text()
        h2t.unicode_snob = True  # Preserve unicode characters
        h2t.body_width = 0  # No wrapping
        markdown_content = h2t.handle(html_content)

        # Get metadata
        metadata = self._get_metadata(urn, options)

        # Add title and metadata
        if options.get("include_metadata", True):
            markdown_header = f"# {metadata.get('title', 'Untitled')}\n\n"
            if metadata.get("creators"):
                markdown_header += "By " + ", ".join(metadata.get("creators", [])) + "\n\n"
            markdown_content = markdown_header + markdown_content

        # Define output Markdown path
        md_path = self._get_output_path(urn, "md", options)

        # Write Markdown file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return Path(md_path)

    def export_to_docx(self, urn: URN, options: Dict[str, Any] = None) -> Path:
        """Export text to DOCX using python-docx.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated DOCX file

        Raises:
            ImportError: If python-docx is not installed
            ValueError: If text cannot be found or processed
        """
        try:
            import docx
            from docx.shared import Pt
        except ImportError:
            raise ImportError("python-docx is required for DOCX export. Install with: pip install python-docx")

        options = options or {}

        # Get metadata
        metadata = self._get_metadata(urn, options)

        # Create a new document
        doc = docx.Document()

        # Add title
        doc.add_heading(metadata.get("title", "Untitled"), 0)

        # Add creators if available
        if metadata.get("creators"):
            creators_paragraph = doc.add_paragraph("By " + ", ".join(metadata.get("creators", [])))
            creators_paragraph.style = "Subtitle"

        # Load XML
        xml_root = self.xml_processor.load_xml(urn)

        # Extract references
        references = self.xml_processor.extract_references(xml_root)

        # Sort references naturally
        sorted_refs = sorted(references.keys(), key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])

        # Process each reference
        for ref in sorted_refs:
            element = references[ref]
            n_attr = element.get("n")

            # Add section heading
            if n_attr:
                heading_level = len(ref.split("."))
                if heading_level > 9:
                    heading_level = 9  # docx supports heading levels 1-9
                doc.add_heading(f"Section {ref}", heading_level)

            # Add text content
            text = "".join(element.itertext()).strip()
            if text:
                p = doc.add_paragraph(text)
                # Use Unicode font for Greek
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(12)

        # Define output DOCX path
        docx_path = self._get_output_path(urn, "docx", options)

        # Save document
        doc.save(docx_path)

        return Path(docx_path)

    def export_to_latex(self, urn: URN, options: Dict[str, Any] = None) -> Path:
        """Export text to LaTeX with XeLaTeX support.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated LaTeX file

        Raises:
            ValueError: If text cannot be found or processed
        """
        options = options or {}

        # Get metadata
        metadata = self._get_metadata(urn, options)

        # Start building LaTeX document
        latex_content = [
            "\\documentclass{article}",
            "\\usepackage{fontspec}",
            "\\usepackage{polyglossia}",
            "\\setmainlanguage{english}",
            "\\setotherlanguage{greek}",
            "\\setmainfont{Times New Roman}",
            "\\newfontfamily\\greekfont[Script=Greek]{Times New Roman}",
            "\\title{" + metadata.get("title", "Untitled") + "}",
        ]

        # Add authors if available
        if metadata.get("creators"):
            latex_content.append("\\author{" + " \\and ".join(metadata.get("creators", [])) + "}")

        # Begin document
        latex_content.extend(
            [
                "\\begin{document}",
                "\\maketitle",
            ]
        )

        # Load XML
        xml_root = self.xml_processor.load_xml(urn)

        # Extract references
        references = self.xml_processor.extract_references(xml_root)

        # Sort references naturally
        sorted_refs = sorted(references.keys(), key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])

        # Process each reference
        for ref in sorted_refs:
            element = references[ref]
            n_attr = element.get("n")

            # Add section heading
            if n_attr:
                heading_level = len(ref.split("."))
                if heading_level == 1:
                    latex_content.append(f"\\section*{{Section {ref}}}")
                elif heading_level == 2:
                    latex_content.append(f"\\subsection*{{Section {ref}}}")
                else:
                    latex_content.append(f"\\subsubsection*{{Section {ref}}}")

            # Add text content
            text = "".join(element.itertext()).strip()
            if text:
                # Escape special LaTeX characters
                text = self._escape_latex(text)

                # Wrap Greek text in \textgreek{}
                text = self._wrap_greek_in_textgreek(text)

                latex_content.append(text)
                latex_content.append("")  # Empty line between paragraphs

        # End document
        latex_content.append("\\end{document}")

        # Define output LaTeX path
        latex_path = self._get_output_path(urn, "tex", options)

        # Write LaTeX file
        with open(latex_path, "w", encoding="utf-8") as f:
            f.write("\n".join(latex_content))

        return Path(latex_path)

    def export_to_html(self, urn: URN, options: Dict[str, Any] = None) -> Path:
        """Export text to standalone HTML.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated HTML file

        Raises:
            ValueError: If text cannot be found or processed
        """
        options = options or {}

        # Get metadata
        metadata = self._get_metadata(urn, options)

        # Get HTML content
        html_content = self._get_html_content(urn, options)

        # Add HTML boilerplate
        standalone_html = [
            "<!DOCTYPE html>",
            '<html lang="grc">',
            "<head>",
            f"<title>{metadata.get('title', 'Untitled')}</title>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "<style>",
            self._get_html_css(options),
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{metadata.get('title', 'Untitled')}</h1>",
        ]

        # Add creators if available
        if metadata.get("creators"):
            standalone_html.append("<h2>By " + ", ".join(metadata.get("creators", [])) + "</h2>")

        # Add content
        standalone_html.append(html_content)

        # Close HTML
        standalone_html.extend(["</body>", "</html>"])

        # Define output HTML path
        html_path = self._get_output_path(urn, "html", options)

        # Write HTML file
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("\n".join(standalone_html))

        return Path(html_path)

    def _get_html_content(self, urn: URN, options: Dict[str, Any] = None) -> str:
        """Get HTML content for export.

        Args:
            urn: URN of the text
            options: Dictionary of export options

        Returns:
            HTML content as string
        """
        options = options or {}

        # Load XML
        xml_root = self.xml_processor.load_xml(urn)

        # Transform to HTML
        target_ref = options.get("reference")
        html_content = self.xml_processor.transform_to_html(xml_root, target_ref)

        return html_content

    def _get_metadata(self, urn: URN, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get metadata for export.

        Args:
            urn: URN of the text
            options: Dictionary of export options

        Returns:
            Dictionary of metadata
        """
        options = options or {}

        # Basic metadata
        metadata = {
            "title": options.get("title", f"Text {urn.text_group}.{urn.work}"),
            "creators": options.get("creators", []),
            "language": "grc",
            "urn": urn.value,
        }

        # TODO: Extract more metadata from TEI header

        return metadata

    def _get_output_path(self, urn: URN, extension: str, options: Dict[str, Any] = None) -> str:
        """Get output path for export.

        Args:
            urn: URN of the text
            extension: File extension (without dot)
            options: Dictionary of export options

        Returns:
            Path as string
        """
        options = options or {}

        # Use custom filename if provided
        if options.get("filename"):
            filename = options.get("filename")
            if not filename.endswith(f".{extension}"):
                filename = f"{filename}.{extension}"
        else:
            # Generate filename from URN
            filename = f"{urn.text_group}_{urn.work}_{urn.version}.{extension}"

        # Custom output directory or default
        output_dir = options.get("output_dir", self.output_dir)

        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        return os.path.join(output_dir, filename)

    def _get_pdf_css(self, options: Dict[str, Any] = None) -> str:
        """Get CSS for PDF export.

        Args:
            options: Dictionary of export options

        Returns:
            CSS as string
        """
        options = options or {}

        css = """
        @page {
            margin: 2cm;
        }
        body {
            font-family: "Times New Roman", Times, serif;
            font-size: 12pt;
            line-height: 1.5;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: "Times New Roman", Times, serif;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        .text-part {
            margin-bottom: 1em;
        }
        .section-num {
            font-weight: bold;
            margin-right: 0.5em;
            float: left;
        }
        .token, .punct {
            font-family: "Times New Roman", Times, serif;
        }
        """

        # Add custom CSS if provided
        if options.get("custom_css"):
            css += options.get("custom_css")

        return css

    def _get_html_css(self, options: Dict[str, Any] = None) -> str:
        """Get CSS for HTML export.

        Args:
            options: Dictionary of export options

        Returns:
            CSS as string
        """
        options = options or {}

        css = """
        body {
            font-family: "Times New Roman", Times, serif;
            font-size: 16px;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 1em;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: "Times New Roman", Times, serif;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        .text-part {
            margin-bottom: 1em;
            position: relative;
        }
        .section-num {
            font-weight: bold;
            margin-right: 0.5em;
            display: inline-block;
        }
        .section-num a {
            text-decoration: none;
            color: #444;
        }
        .content {
            margin-left: 2em;
        }
        .token, .punct {
            font-family: "Times New Roman", Times, serif;
        }
        .token:hover {
            background-color: #f0f0f0;
            cursor: pointer;
        }
        """

        # Add custom CSS if provided
        if options.get("custom_css"):
            css += options.get("custom_css")

        return css

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        escape_chars = {
            "&": "\\&",
            "%": "\\%",
            "$": "\\$",
            "#": "\\#",
            "_": "\\_",
            "{": "\\{",
            "}": "\\}",
            "~": "\\textasciitilde{}",
            "^": "\\textasciicircum{}",
            "\\": "\\textbackslash{}",
            "<": "\\textless{}",
            ">": "\\textgreater{}",
        }

        for char, replacement in escape_chars.items():
            text = text.replace(char, replacement)

        return text

    def _wrap_greek_in_textgreek(self, text: str) -> str:
        r"""Wrap Greek text in \textgreek{}.

        This is a simplified approach that assumes any text with Greek
        characters should be wrapped. A more sophisticated approach would
        analyze the text and wrap only the Greek portions.

        Args:
            text: Text to process

        Returns:
            Text with Greek portions wrapped in \textgreek{}
        """
        # Check if there are any Greek characters in the text
        greek_chars = set("αβγδεζηθικλμνξοπρσςτυφχψω΄῾᾿῀῁῍῎῏῝῞῟῭΅`´῾ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")

        if any(c.lower() in greek_chars for c in text):
            # Simple approach: wrap the entire text if it contains Greek
            return f"\\textgreek{{{text}}}"

        return text
