# Eulogos Text Export System Implementation Plan

## Overview

This document outlines the implementation plan for enhancing the Eulogos project with a robust text display and export system, focusing on proper XML processing and multi-format export capabilities. This implementation will ensure ancient Greek texts are both readable in the browser and exportable in various formats (PDF, ePub, Markdown, DOCX) for offline access.

## Background

The Eulogos project currently has limitations in its XML processing that affect the quality of text display and export capabilities. The project requires:

1. Enhanced XML formatting for proper text display in the browser
2. Export functionality for multiple document formats
3. Preservation of textual structure, references, and formatting

## Implementation Components

### 1. Reference Handling System

Implement the enhanced reference handling system from `xml_reference-handling-implementation.md` that provides:

- Sophisticated XML parsing preserving hierarchical structure
- Proper handling of references and citations
- Token-level processing for word analysis
- Interactive text reading interface

### 2. Export Service

Develop a new ExportService that leverages the improved XML processing to generate high-quality exports in multiple formats.

### 3. Export API Endpoints

Create API endpoints for text export with various format options and customization parameters.

### 4. UI Integration

Extend the reader interface with export options and format selection controls.

## Technical Specifications

### 1. Reference Handling System

#### 1.1 URN Model (`app/models/urn.py`)

```python
from pydantic import BaseModel
from typing import Optional

class URN(BaseModel):
    """
    Model for Canonical Text Services URNs.

    Example: urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7
    """
    value: str
    urn_namespace: Optional[str] = None
    cts_namespace: Optional[str] = None
    text_group: Optional[str] = None
    work: Optional[str] = None
    version: Optional[str] = None
    reference: Optional[str] = None

    def __init__(self, value: str, **kwargs):
        super().__init__(value=value, **kwargs)
        self.parse()

    def parse(self):
        """Parse the URN into its components."""
        urn = self.value.split('#')[0]
        bits = urn.split(':')[1:]
        if len(bits) > 2:
            self.urn_namespace = bits[0]
            self.cts_namespace = bits[1]
            work_identifier = bits[2]
            if len(bits) > 3:
                self.reference = bits[3]

            # Parse work identifier
            work_parts = work_identifier.split('.')
            if len(work_parts) >= 1:
                self.text_group = work_parts[0]
            if len(work_parts) >= 2:
                self.work = work_parts[1]
            if len(work_parts) >= 3:
                self.version = work_parts[2]

    def up_to(self, segment: str) -> str:
        """
        Return the URN up to a specific segment.

        Example: urn_obj.up_to("version") for urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1
        Returns: urn:cts:greekLit:tlg0012.tlg001.perseus-grc2
        """
        segments = ["urn", self.urn_namespace, self.cts_namespace]

        if segment in ["text_group", "work", "version", "reference"] and self.text_group:
            segments.append(self.text_group)

        if segment in ["work", "version", "reference"] and self.work:
            segments.append(f"{self.text_group}.{self.work}")

        if segment in ["version", "reference"] and self.version:
            segments.append(f"{self.text_group}.{self.work}.{self.version}")

        if segment == "reference" and self.reference:
            segments.append(self.reference)

        return ":".join(segments)

    def replace(self, **kwargs) -> 'URN':
        """
        Return a new URN with replaced components.

        Example: urn_obj.replace(reference="1.2")
        Creates a new URN with the same components but a different reference.
        """
        value = self.value
        new_obj = URN(value)

        for key, val in kwargs.items():
            setattr(new_obj, key, val)

        # Rebuild the URN value
        work_part = ""
        if new_obj.text_group:
            work_part = new_obj.text_group
            if new_obj.work:
                work_part += f".{new_obj.work}"
                if new_obj.version:
                    work_part += f".{new_obj.version}"

        urn_parts = [
            "urn",
            new_obj.urn_namespace or self.urn_namespace,
            new_obj.cts_namespace or self.cts_namespace,
            work_part
        ]

        new_value = ":".join(urn_parts)

        if new_obj.reference:
            new_value += f":{new_obj.reference}"

        new_obj.value = new_value
        return new_obj

    def __str__(self):
        return self.value
```

#### 1.2 Enhanced XMLProcessorService (`app/services/xml_processor_service.py`)

```python
from lxml import etree
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import BaseModel

from app.models.urn import URN

class XMLProcessorService:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}

    def resolve_urn_to_file_path(self, urn_obj: URN) -> Path:
        """
        Convert a CTS URN to a file path.

        Example:
        urn:cts:greekLit:tlg0012.tlg001.perseus-grc2
        -> data/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml
        """
        path = Path(self.data_path)
        if urn_obj.text_group:
            path = path / urn_obj.text_group
            if urn_obj.work:
                path = path / urn_obj.work
                if urn_obj.version:
                    return path / f"{urn_obj.text_group}.{urn_obj.work}.{urn_obj.version}.xml"
        raise ValueError(f"Could not resolve URN to file path: {urn_obj.value}")

    def load_xml(self, urn_obj: URN) -> etree._Element:
        """Load XML file based on URN."""
        filepath = self.resolve_urn_to_file_path(urn_obj)
        if not filepath.exists():
            raise FileNotFoundError(f"XML file not found: {filepath}")
        return etree.parse(str(filepath)).getroot()

    def extract_references(self, element: etree._Element, parent_ref: str = "") -> Dict[str, etree._Element]:
        """Extract hierarchical references from TEI XML elements."""
        references = {}
        n_attr = element.get("n")

        if n_attr:
            ref = f"{parent_ref}.{n_attr}" if parent_ref else n_attr
            references[ref] = element
        else:
            ref = parent_ref

        # Process child textparts and lines recursively
        for child in element.xpath(".//tei:div[@type='textpart'] | .//tei:l", namespaces=self.namespaces):
            child_refs = self.extract_references(child, ref)
            references.update(child_refs)

        return references

    def get_passage_by_reference(self, xml_root: etree._Element, reference: str) -> Optional[etree._Element]:
        """Retrieve a specific passage by its reference."""
        references = self.extract_references(xml_root)
        return references.get(reference)

    def get_adjacent_references(self, xml_root: etree._Element, current_ref: str) -> Dict[str, Optional[str]]:
        """Get previous and next references relative to the current one."""
        references = list(self.extract_references(xml_root).keys())
        try:
            idx = references.index(current_ref)
            prev_ref = references[idx - 1] if idx > 0 else None
            next_ref = references[idx + 1] if idx < len(references) - 1 else None
            return {"prev": prev_ref, "next": next_ref}
        except ValueError:
            return {"prev": None, "next": None}

    def _build_reference(self, element: etree._Element) -> str:
        """Build hierarchical reference from element and its ancestors."""
        refs = []

        # Add current element's n attribute if present
        if "n" in element.attrib:
            refs.append(element.get("n"))

        # Add ancestor references
        for ancestor in element.xpath("ancestor::tei:div[@type='textpart']", namespaces=self.namespaces):
            if "n" in ancestor.attrib:
                refs.insert(0, ancestor.get("n"))

        return ".".join(refs)

    def tokenize_text(self, text: str) -> List[Dict]:
        """Split text into tokens (words and punctuation)."""
        import re

        if not text or text.strip() == '':
            return []

        tokens = []
        words = text.split()

        for i, word in enumerate(words):
            # Extract punctuation from the end of words
            match = re.match(r'(\w+)([,.;:!?]*)$', word)
            if match:
                word_text, punct = match.groups()
                tokens.append({
                    'type': 'word',
                    'text': word_text,
                    'index': i + 1
                })

                if punct:
                    tokens.append({
                        'type': 'punct',
                        'text': punct
                    })
            else:
                tokens.append({
                    'type': 'word',
                    'text': word,
                    'index': i + 1
                })

        return tokens

    def process_text_node(self, text_node: etree._ElementUnicodeResult) -> str:
        """Process a text node, adding markup for words and tokens."""
        tokens = self.tokenize_text(text_node)
        html = []

        for token in tokens:
            if token['type'] == 'word':
                html.append(f'<span class="token" data-token="{token["text"]}" data-token-index="{token["index"]}">{token["text"]}</span>')
            elif token['type'] == 'punct':
                html.append(f'<span class="punct">{token["text"]}</span>')

        return ''.join(html)

    def transform_to_html(self, xml_root: etree._Element, target_ref: Optional[str] = None) -> str:
        """Transform XML to HTML with reference attributes."""
        # If a specific reference is targeted, find that element
        if target_ref:
            element = self.get_passage_by_reference(xml_root, target_ref)
            if not element:
                raise ValueError(f"Reference not found: {target_ref}")
            # Include only the specified element and its children
            elements = [element]
        else:
            # Include all top-level textparts
            elements = xml_root.xpath("//tei:div[@type='textpart' and not(parent::tei:div[@type='textpart'])] | //tei:l[not(parent::tei:div[@type='textpart'])]", namespaces=self.namespaces)

        html = []

        for element in elements:
            ref = self._build_reference(element)

            # Create HTML with data attributes
            html.append(f'<div class="text-part" data-reference="{ref}">')

            # Add section number as clickable element
            section_num = element.get("n", "")
            if section_num:
                html.append(f'<div class="section-num"><a href="/reader/{ref}">{section_num}</a></div>')

            # Add content
            html.append('<div class="content">')

            # Process text content
            for node in element.xpath(".//text()", namespaces=self.namespaces):
                if node.is_text:
                    html.append(self.process_text_node(node))

            # Add nested elements
            for child in element.xpath("./tei:div[@type='textpart'] | ./tei:l", namespaces=self.namespaces):
                child_html = self.transform_to_html(child, None)
                html.append(child_html)

            # Close elements
            html.append('</div></div>')

        return ''.join(html)

    def transform_to_markdown(self, xml_root: etree._Element, target_ref: Optional[str] = None) -> str:
        """Transform XML to Markdown format."""
        # Similar to transform_to_html but generate Markdown instead
        # Implementation details...
        pass

    def transform_to_plaintext(self, xml_root: etree._Element, target_ref: Optional[str] = None) -> str:
        """Transform XML to plain text format."""
        # Implementation details...
        pass
```

### 2. Export Service (`app/services/export_service.py`)

```python
import tempfile
from pathlib import Path
from typing import Dict, Optional, BinaryIO
import os
import subprocess
import shutil

from app.models.urn import URN
from app.services.xml_processor_service import XMLProcessorService
from app.services.catalog_service import CatalogService

class ExportService:
    """Service for exporting texts in various formats."""

    def __init__(
        self,
        xml_processor: XMLProcessorService,
        catalog_service: CatalogService
    ):
        self.xml_processor = xml_processor
        self.catalog_service = catalog_service

    def get_text_metadata(self, urn: str) -> Dict:
        """Get metadata for a text."""
        text = self.catalog_service.get_text_by_urn(urn)
        if not text:
            raise ValueError(f"Text not found: {urn}")

        return {
            "title": text.work_name,
            "author": text.group_name,
            "language": text.language,
            "urn": urn
        }

    def export_to_pdf(self, urn: str, options: Optional[Dict] = None) -> bytes:
        """Export text to PDF format.

        Args:
            urn: Text URN
            options: Optional export options
                - font_size: Font size (default: 12)
                - paper_size: Paper size (default: A4)
                - margins: Margins in mm (default: 20)
                - include_toc: Include table of contents (default: True)

        Returns:
            PDF file content as bytes
        """
        # Set default options
        options = options or {}
        font_size = options.get("font_size", 12)
        paper_size = options.get("paper_size", "A4")
        margins = options.get("margins", 20)
        include_toc = options.get("include_toc", True)

        # Parse URN
        urn_obj = URN(urn)

        # Get text metadata
        metadata = self.get_text_metadata(urn)

        # Load XML
        xml_root = self.xml_processor.load_xml(urn_obj)

        # Transform to HTML
        html_content = self.xml_processor.transform_to_html(xml_root, urn_obj.reference)

        # Create PDF using WeasyPrint
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration

        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            html_file = f.name

            # Create HTML with proper styling
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{metadata['title']}</title>
                <style>
                    @page {{
                        size: {paper_size};
                        margin: {margins}mm;
                    }}
                    body {{
                        font-family: "Noto Serif", serif;
                        font-size: {font_size}pt;
                        line-height: 1.5;
                    }}
                    .text-part {{
                        margin-bottom: 1rem;
                    }}
                    .section-num {{
                        float: left;
                        font-weight: bold;
                        margin-right: 0.5rem;
                    }}
                    .token {{
                        display: inline;
                    }}
                    h1 {{
                        font-size: 24pt;
                        text-align: center;
                        margin-bottom: 2rem;
                    }}
                    h2 {{
                        font-size: 18pt;
                        text-align: center;
                        margin-bottom: 1rem;
                    }}
                    .author {{
                        text-align: center;
                        font-style: italic;
                        margin-bottom: 3rem;
                    }}
                </style>
            </head>
            <body>
                <h1>{metadata['title']}</h1>
                <div class="author">{metadata['author']}</div>
                {html_content}
            </body>
            </html>
            """

            f.write(full_html.encode('utf-8'))

        try:
            # Generate PDF
            font_config = FontConfiguration()
            html = HTML(filename=html_file)
            pdf_bytes = html.write_pdf(font_config=font_config)

            return pdf_bytes
        finally:
            # Clean up temporary file
            if os.path.exists(html_file):
                os.unlink(html_file)

    def export_to_epub(self, urn: str, options: Optional[Dict] = None) -> bytes:
        """Export text to ePub format.

        Args:
            urn: Text URN
            options: Optional export options
                - cover_image: Include cover image (default: True)
                - css_style: Custom CSS styling (default: None)

        Returns:
            ePub file content as bytes
        """
        # Implementation using ebooklib
        import ebooklib
        from ebooklib import epub

        # Set default options
        options = options or {}
        cover_image = options.get("cover_image", True)
        css_style = options.get("css_style")

        # Parse URN
        urn_obj = URN(urn)

        # Get text metadata
        metadata = self.get_text_metadata(urn)

        # Load XML
        xml_root = self.xml_processor.load_xml(urn_obj)

        # Transform to HTML
        html_content = self.xml_processor.transform_to_html(xml_root, urn_obj.reference)

        # Create ePub
        book = epub.EpubBook()

        # Set metadata
        book.set_identifier(urn)
        book.set_title(metadata['title'])
        book.set_language(metadata['language'])
        book.add_author(metadata['author'])

        # Create chapters
        chapter = epub.EpubHtml(title=metadata['title'], file_name='text.xhtml')

        # Add CSS
        default_style = '''
        body {
            font-family: "Noto Serif", serif;
            font-size: 1em;
            line-height: 1.5;
        }
        .text-part {
            margin-bottom: 1rem;
        }
        .section-num {
            float: left;
            font-weight: bold;
            margin-right: 0.5rem;
        }
        .token {
            display: inline;
        }
        '''

        style_content = css_style if css_style else default_style

        css = epub.EpubItem(
            uid="style",
            file_name="style.css",
            media_type="text/css",
            content=style_content
        )
        book.add_item(css)

        # Set chapter content
        chapter_content = f"""
        <html>
        <head>
            <title>{metadata['title']}</title>
            <link rel="stylesheet" href="style.css" type="text/css" />
        </head>
        <body>
            <h1>{metadata['title']}</h1>
            <div class="author">{metadata['author']}</div>
            {html_content}
        </body>
        </html>
        """

        chapter.content = chapter_content
        book.add_item(chapter)

        # Add chapter to table of contents
        book.toc = [epub.Link('text.xhtml', metadata['title'], 'text')]

        # Add default NCX and Nav files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Define spine
        book.spine = ['nav', chapter]

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            epub_file = f.name

        try:
            # Write ePub file
            epub.write_epub(epub_file, book, {})

            # Read file content
            with open(epub_file, 'rb') as f:
                epub_content = f.read()

            return epub_content
        finally:
            # Clean up temporary file
            if os.path.exists(epub_file):
                os.unlink(epub_file)

    def export_to_mobi(self, urn: str, options: Optional[Dict] = None) -> bytes:
        """Export text to MOBI/KF8 format for Kindle.

        Args:
            urn: Text URN
            options: Optional export options
                - cover_image: Include cover image (default: True)
                - kindlegen_path: Path to kindlegen executable (default: auto-detect)

        Returns:
            MOBI file content as bytes
        """
        # Set default options
        options = options or {}
        cover_image = options.get("cover_image", True)
        kindlegen_path = options.get("kindlegen_path", shutil.which("kindlegen") or "/usr/local/bin/kindlegen")

        # First, generate ePub as intermediate format
        epub_content = self.export_to_epub(urn, options)

        # Create temporary directory for conversion
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save ePub to temporary file
            epub_file = os.path.join(temp_dir, "book.epub")
            with open(epub_file, "wb") as f:
                f.write(epub_content)

            # Output MOBI file
            mobi_file = os.path.join(temp_dir, "book.mobi")

            # Use kindlegen to convert ePub to MOBI
            try:
                subprocess.run(
                    [kindlegen_path, epub_file, "-o", "book.mobi"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # Read MOBI file
                with open(mobi_file, "rb") as f:
                    mobi_content = f.read()

                return mobi_content
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                # Fall back to Calibre's ebook-convert if kindlegen fails or is not found
                try:
                    subprocess.run(
                        ["ebook-convert", epub_file, mobi_file],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )

                    # Read MOBI file
                    with open(mobi_file, "rb") as f:
                        mobi_content = f.read()

                    return mobi_content
                except (subprocess.SubprocessError, FileNotFoundError):
                    raise ValueError(
                        "Failed to convert to MOBI format. "
                        "Please ensure kindlegen or Calibre's ebook-convert is installed."
                    )

    def export_to_markdown(self, urn: str, options: Optional[Dict] = None) -> str:
        """Export text to Markdown format.

        Args:
            urn: Text URN
            options: Optional export options
                - include_metadata: Include title and author (default: True)
                - format: Markdown format (github, commonmark, etc.) (default: github)

        Returns:
            Markdown content as string
        """
        # Set default options
        options = options or {}
        include_metadata = options.get("include_metadata", True)
        md_format = options.get("format", "github")

        # Parse URN
        urn_obj = URN(urn)

        # Get text metadata
        metadata = self.get_text_metadata(urn)

        # Load XML
        xml_root = self.xml_processor.load_xml(urn_obj)

        # Transform to HTML
        html_content = self.xml_processor.transform_to_html(xml_root, urn_obj.reference)

        # Convert HTML to Markdown
        import html2text

        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.unicode_snob = True
        converter.body_width = 0  # No text wrapping

        md_content = converter.handle(html_content)

        # Add metadata at the beginning if requested
        if include_metadata:
            md_header = f"# {metadata['title']}\n\n_{metadata['author']}_\n\n"
            return md_header + md_content
        else:
            return md_content

    def export_to_docx(self, urn: str, options: Optional[Dict] = None) -> bytes:
        """Export text to DOCX (Word) format.

        Args:
            urn: Text URN
            options: Optional export options
                - style: Document style (default: None)
                - include_toc: Include table of contents (default: True)

        Returns:
            DOCX file content as bytes
        """
        # Set default options
        options = options or {}
        include_toc = options.get("include_toc", True)

        # Parse URN
        urn_obj = URN(urn)

        # Get text metadata
        metadata = self.get_text_metadata(urn)

        # Load XML
        xml_root = self.xml_processor.load_xml(urn_obj)

        # Transform to HTML
        html_content = self.xml_processor.transform_to_html(xml_root, urn_obj.reference)

        # Create Word document using python-docx
        from docx import Document
        from docx.shared import Pt

        # Create document
        doc = Document()

        # Add title
        title = doc.add_heading(metadata['title'], level=1)

        # Add author
        author = doc.add_paragraph(metadata['author'])
        author.style = 'Subtitle'

        # Add table of contents if requested
        if include_toc:
            doc.add_paragraph("Table of Contents", style='TOC Heading')
            doc.add_paragraph("", style='TOC 1')
            # Note: TOC needs to be updated by Word after opening

        # Use a library like htmldocx to convert HTML to DOCX
        # For simplicity, we'll parse the HTML ourselves
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, 'html.parser')

        # Process text parts
        for text_part in soup.find_all('div', class_='text-part'):
            # Get reference
            ref = text_part.get('data-reference', '')

            # Get section number
            section_num = text_part.find('div', class_='section-num')
            section_text = section_num.text if section_num else ''

            # Get content
            content = text_part.find('div', class_='content')
            content_text = content.get_text() if content else ''

            # Add to document
            if section_text:
                p = doc.add_paragraph()
                run = p.add_run(f"{section_text} ")
                run.bold = True
                p.add_run(content_text)
            else:
                doc.add_paragraph(content_text)

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            docx_file = f.name

        try:
            # Save document
            doc.save(docx_file)

            # Read file content
            with open(docx_file, 'rb') as f:
                docx_content = f.read()

            return docx_content
        finally:
            # Clean up temporary file
            if os.path.exists(docx_file):
                os.unlink(docx_file)

    def export_to_latex(self, urn: str, options: Optional[Dict] = None) -> str:
        """Export text to LaTeX format.

        Args:
            urn: Text URN
            options: Optional export options
                - document_class: LaTeX document class (default: article)
                - include_packages: Additional packages to include (default: [])
                - create_pdf: Also generate PDF from LaTeX (default: False)

        Returns:
            LaTeX content as string, or PDF bytes if create_pdf is True
        """
        # Set default options
        options = options or {}
        document_class = options.get("document_class", "article")
        include_packages = options.get("include_packages", [])
        create_pdf = options.get("create_pdf", False)

        # Parse URN
        urn_obj = URN(urn)

        # Get text metadata
        metadata = self.get_text_metadata(urn)

        # Load XML
        xml_root = self.xml_processor.load_xml(urn_obj)

        # Transform to HTML as intermediate format
        html_content = self.xml_processor.transform_to_html(xml_root, urn_obj.reference)

        # Convert HTML to LaTeX
        # This is a simplified approach; a more sophisticated HTMLtoLaTeX converter should be used
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, 'html.parser')

        # Create LaTeX document structure
        latex_header = [
            f"\\documentclass{{{document_class}}}",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage{fontspec}",
            "\\usepackage{polyglossia}",
            "\\setmainlanguage{english}",
            "\\setotherlanguage{greek}",
        ]

        # Add additional packages
        for package in include_packages:
            latex_header.append(f"\\usepackage{{{package}}}")

        # Add document metadata
        latex_document = [
            "\\begin{document}",
            f"\\title{{{metadata['title']}}}",
            f"\\author{{{metadata['author']}}}",
            "\\maketitle",
            "\\tableofcontents",
            "\\begin{abstract}",
            f"Text from the Eulogos project. URN: {urn}",
            "\\end{abstract}",
        ]

        # Process text parts to LaTeX
        for text_part in soup.find_all('div', class_='text-part'):
            # Get reference
            ref = text_part.get('data-reference', '')

            # Get section number
            section_num = text_part.find('div', class_='section-num')
            section_text = section_num.text if section_num else ''

            # Get content
            content = text_part.find('div', class_='content')
            content_text = content.get_text() if content else ''

            # Add to LaTeX document
            if section_text:
                latex_document.append(f"\\section*{{{section_text}}}")
                latex_document.append(content_text)
            else:
                latex_document.append(content_text)

        # Close document
        latex_document.append("\\end{document}")

        # Combine header and document
        latex_content = "\n".join(latex_header + latex_document)

        # Return LaTeX source or generate PDF
        if not create_pdf:
            return latex_content
        else:
            # Create temporary directory for LaTeX compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save LaTeX to file
                tex_file = os.path.join(temp_dir, "document.tex")
                with open(tex_file, "w", encoding="utf-8") as f:
                    f.write(latex_content)

                # Compile LaTeX to PDF using xelatex
                try:
                    # Run xelatex twice to ensure references are resolved
                    for _ in range(2):
                        subprocess.run(
                            ["xelatex", "-interaction=nonstopmode", "document.tex"],
                            cwd=temp_dir,
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )

                    # Read PDF file
                    pdf_file = os.path.join(temp_dir, "document.pdf")
                    with open(pdf_file, "rb") as f:
                        pdf_content = f.read()

                    return pdf_content
                except subprocess.SubprocessError:
                    raise ValueError("Failed to compile LaTeX to PDF")

    def export_to_html(self, urn: str, options: Optional[Dict] = None) -> str:
        """Export text to standalone HTML format.

        Args:
            urn: Text URN
            options: Optional export options
                - include_css: Include CSS styling (default: True)
                - include_js: Include JavaScript for interactivity (default: False)
                - template: HTML template to use (default: None)

        Returns:
            HTML content as string
        """
        # Set default options
        options = options or {}
        include_css = options.get("include_css", True)
        include_js = options.get("include_js", False)
        template = options.get("template")

        # Parse URN
        urn_obj = URN(urn)

        # Get text metadata
        metadata = self.get_text_metadata(urn)

        # Load XML
        xml_root = self.xml_processor.load_xml(urn_obj)

        # Transform to HTML
        html_content = self.xml_processor.transform_to_html(xml_root, urn_obj.reference)

        # Default CSS
        default_css = """
        body {
            font-family: "Noto Serif", serif;
            font-size: 16px;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        h1 {
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 1rem;
        }
        .author {
            text-align: center;
            font-style: italic;
            margin-bottom: 3rem;
        }
        .text-part {
            margin-bottom: 1rem;
            position: relative;
        }
        .section-num {
            font-weight: bold;
            margin-right: 0.5rem;
        }
        .token {
            display: inline;
        }
        """

        # Default JavaScript for interactivity
        default_js = """
        document.addEventListener('DOMContentLoaded', function() {
            // Make section numbers clickable for copying references
            document.querySelectorAll('.section-num').forEach(function(el) {
                el.addEventListener('click', function() {
                    const ref = this.closest('[data-reference]').getAttribute('data-reference');
                    navigator.clipboard.writeText(ref).then(function() {
                        alert('Reference copied: ' + ref);
                    });
                });
            });
        });
        """

        # If a template is provided, use it
        if template:
            # Replace placeholders in template
            html = template.replace("{{title}}", metadata['title'])
            html = html.replace("{{author}}", metadata['author'])
            html = html.replace("{{content}}", html_content)
            return html

        # Otherwise, create a standard HTML document
        html = ["<!DOCTYPE html>", "<html>", "<head>", f"<title>{metadata['title']}</title>"]

        # Add metadata
        html.append('<meta charset="UTF-8">')
        html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')

        # Add CSS if requested
        if include_css:
            html.append("<style>")
            html.append(default_css)
            html.append("</style>")

        # Add JavaScript if requested
        if include_js:
            html.append("<script>")
            html.append(default_js)
            html.append("</script>")

        # Close head and start body
        html.append("</head>")
        html.append("<body>")

        # Add title and author
        html.append(f"<h1>{metadata['title']}</h1>")
        html.append(f'<div class="author">{metadata["author"]}</div>')

        # Add content
        html.append(html_content)

        # Close body and html
        html.append("</body>")
        html.append("</html>")

        return "\n".join(html)
```

### 3. API Endpoints (`app/routers/export.py`)

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response, PlainTextResponse
from typing import Dict, Optional

from app.models.urn import URN
from app.services.export_service import ExportService
from app.services.xml_processor_service import XMLProcessorService
from app.services.catalog_service import CatalogService

router = APIRouter(tags=["export"])

def get_export_service():
    """Dependency for ExportService."""
    xml_processor = XMLProcessorService(data_path="data")
    catalog_service = CatalogService(catalog_path="integrated_catalog.json")
    return ExportService(xml_processor, catalog_service)

def parse_export_options(
    font_size: Optional[int] = Query(12, description="Font size for PDFs"),
    paper_size: Optional[str] = Query("A4", description="Paper size for PDFs"),
    margins: Optional[int] = Query(20, description="Margins in mm for PDFs"),
    include_toc: Optional[bool] = Query(True, description="Include table of contents"),
    cover_image: Optional[bool] = Query(True, description="Include cover image for ebooks"),
    create_pdf: Optional[bool] = Query(False, description="Generate PDF from LaTeX"),
    document_class: Optional[str] = Query("article", description="LaTeX document class"),
    include_js: Optional[bool] = Query(False, description="Include JavaScript in HTML export"),
    format: Optional[str] = Query("github", description="Markdown format"),
) -> Dict:
    """Parse export options from query parameters."""
    return {
        "font_size": font_size,
        "paper_size": paper_size,
        "margins": margins,
        "include_toc": include_toc,
        "cover_image": cover_image,
    }

@router.get("/export/{urn}")
async def export_text(
    urn: str,
    format: str = Query("pdf", description="Export format: pdf, epub, mobi, markdown, docx, latex, html"),
    options: Dict = Depends(parse_export_options),
    export_service: ExportService = Depends(get_export_service)
):
    """Export text in specified format."""
    try:
        # Parse URN to validate format
        urn_obj = URN(urn)

        # Sanitize URN for filename
        safe_filename = urn.replace(":", "_").replace("/", "_")

        if format == "pdf":
            content = export_service.export_to_pdf(urn, options)
            media_type = "application/pdf"
            filename = f"{safe_filename}.pdf"
        elif format == "epub":
            content = export_service.export_to_epub(urn, options)
            media_type = "application/epub+zip"
            filename = f"{safe_filename}.epub"
        elif format == "mobi":
            content = export_service.export_to_mobi(urn, options)
            media_type = "application/x-mobipocket-ebook"
            filename = f"{safe_filename}.mobi"
        elif format == "markdown":
            content = export_service.export_to_markdown(urn, options)
            media_type = "text/markdown"
            filename = f"{safe_filename}.md"
            return PlainTextResponse(
                content=content,
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif format == "docx":
            content = export_service.export_to_docx(urn, options)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{safe_filename}.docx"
        elif format == "latex":
            # Check if PDF generation is requested
            if options.get("create_pdf", False):
                content = export_service.export_to_latex(urn, options)
                media_type = "application/pdf"
                filename = f"{safe_filename}.pdf"
            else:
                content = export_service.export_to_latex(urn, options)
                media_type = "application/x-latex"
                filename = f"{safe_filename}.tex"
                return PlainTextResponse(
                    content=content,
                    media_type=media_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
        elif format == "html":
            content = export_service.export_to_html(urn, options)
            media_type = "text/html"
            filename = f"{safe_filename}.html"
            return PlainTextResponse(
                content=content,
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. UI Integration (`app/templates/reader.html`)

Update the reader template to include export options:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ text.work_name }} - Eulogos</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script src="https://unpkg.com/htmx.org@1.9.4" crossorigin="anonymous"></script>
    <script src="https://unpkg.com/alpinejs@3.13.0" crossorigin="anonymous" defer></script>
    <style>
        /* Add custom styles for token highlighting */
        .token-highlighted {
            background-color: rgba(254, 240, 138, 1);
            border-radius: 2px;
        }

        .text-part {
            position: relative;
            display: flex;
            margin-bottom: 0.5rem;
            line-height: 1.5;
        }

        .text-part .section-num {
            min-width: 2.5rem;
            text-align: right;
            padding-right: 0.75rem;
            font-weight: bold;
            color: #6b7280;
        }

        .text-part .content {
            flex: 1;
        }

        .token {
            display: inline-block;
            padding: 0 1px;
        }

        .punct {
            display: inline-block;
            margin-left: -1px;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen flex flex-col">
        <!-- Header -->
        <header class="bg-blue-600 text-white shadow">
            <div class="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
                <h1 class="text-2xl font-bold">Eulogos</h1>
                <a href="/" class="px-4 py-2 bg-blue-700 hover:bg-blue-800 rounded text-white">Back to Browse</a>
            </div>
        </header>

        <!-- Main Content -->
        <main class="flex-grow">
            <div class="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
                <div class="bg-white shadow rounded-lg p-6">
                    <!-- Text info -->
                    <div class="mb-6">
                        <h2 class="text-2xl font-bold mb-2">{{ text.work_name }}</h2>
                        <div class="text-gray-600">
                            <p>Author: {{ text.group_name }}</p>
                            <p>Language: {{ text.language }}</p>
                            {% if text.wordcount %}
                            <p>Word count: {{ text.wordcount }}</p>
                            {% endif %}
                            <p class="text-xs text-gray-500 mt-2">URN: {{ text.urn }}</p>
                        </div>
                    </div>

                    <!-- Text controls -->
                    <div class="mb-6 flex justify-between">
                        <div class="flex space-x-2">
                            <button
                                hx-post="/api/texts/{{ text.urn }}/archive?archive={{ not text.archived }}"
                                hx-target="#reader-container"
                                class="px-2 py-1 {{ 'bg-green-600' if text.archived else 'bg-gray-600' }} text-white rounded text-sm"
                            >
                                {{ 'Unarchive' if text.archived else 'Archive' }}
                            </button>
                            <button
                                hx-post="/api/texts/{{ text.urn }}/favorite"
                                hx-target="#reader-container"
                                class="px-2 py-1 {{ 'bg-yellow-600' if text.favorite else 'bg-gray-600' }} text-white rounded text-sm"
                            >
                                {{ 'Unfavorite' if text.favorite else 'Favorite' }}
                            </button>
                        </div>

                        <!-- Export Options -->
                        <div x-data="{ showExportOptions: false }" class="relative">
                            <button
                                @click="showExportOptions = !showExportOptions"
                                class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded"
                            >
                                Export
                            </button>

                            <!-- Export Dropdown -->
                            <div
                                x-show="showExportOptions"
                                @click.away="showExportOptions = false"
                                class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg z-10"
                            >
                                <div class="p-2 border-b border-gray-200">
                                    <h4 class="text-sm font-medium text-gray-700">Download As:</h4>
                                </div>
                                <div class="p-2">
                                    <a href="/export/{{ text.urn }}?format=pdf" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded">PDF</a>
                                    <a href="/export/{{ text.urn }}?format=epub" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded">ePub</a>
                                    <a href="/export/{{ text.urn }}?format=mobi" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded">Kindle (MOBI)</a>
                                    <a href="/export/{{ text.urn }}?format=markdown" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded">Markdown</a>
                                    <a href="/export/{{ text.urn }}?format=docx" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded">Word (DOCX)</a>
                                    <a href="/export/{{ text.urn }}?format=latex" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded">LaTeX</a>
                                    <a href="/export/{{ text.urn }}?format=html" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded">HTML</a>
                                </div>
                                <div class="p-2 border-t border-gray-200">
                                    <h4 class="text-sm font-medium text-gray-700">Options:</h4>
                                    <div class="mt-1">
                                        <label class="flex items-center text-sm text-gray-700">
                                            <input type="checkbox" class="form-checkbox h-4 w-4 text-blue-600" checked>
                                            <span class="ml-2">Include Table of Contents</span>
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Reader Container -->
                    <div class="reader-container"
                         x-data="{
                           textMode: 'normal',
                           selectedToken: null,
                           toggleTextMode() {
                             this.textMode = this.textMode === 'normal' ? 'highlight' : 'normal';
                             this.selectedToken = null;
                           },
                           selectToken(token) {
                             if (this.textMode === 'highlight') {
                               this.selectedToken = token;
                             }
                           }
                         }">

                        <!-- Reader Controls -->
                        <div class="reader-controls mb-4">
                            <button @click="toggleTextMode()"
                                    x-text="textMode === 'normal' ? 'Normal Mode' : 'Highlight Mode'"
                                    class="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm"
                                    :class="textMode === 'normal' ? '' : 'bg-yellow-200 hover:bg-yellow-300'">
                            </button>
                        </div>

                        <!-- Reference navigation -->
                        <div class="reference-nav mb-4 flex justify-between bg-gray-100 p-2 rounded">
                            {% if prev_reference %}
                                <a href="/read/{{ urn_base }}:{{ prev_reference }}" class="text-blue-600 hover:underline">
                                    ← Previous
                                </a>
                            {% else %}
                                <span class="text-gray-400">← Previous</span>
                            {% endif %}

                            <span class="font-medium">{{ urn_obj.reference or 'Full Text' }}</span>

                            {% if next_reference %}
                                <a href="/read/{{ urn_base }}:{{ next_reference }}" class="text-blue-600 hover:underline">
                                    Next →
                                </a>
                            {% else %}
                                <span class="text-gray-400">Next →</span>
                            {% endif %}
                        </div>

                        <!-- Text content -->
                        <div id="reader-container"
                             class="prose max-w-none"
                             :class="{ 'mode-highlight': textMode === 'highlight' }">
                            {{ html_content|safe }}
                        </div>

                        <!-- Token information (when selected) -->
                        <div class="token-info mt-4 p-4 border-t border-gray-200" x-show="selectedToken" x-cloak>
                            <h4 class="text-lg font-medium text-gray-700 mb-2">Selected Word</h4>
                            <div x-text="selectedToken" class="text-xl mb-2 font-bold"></div>

                            <div hx-get="/api/word-info/"
                                 hx-trigger="selectedToken changed"
                                 hx-vals='{"word": selectedToken, "lang": "{{ language }}"}'
                                 hx-target="this">
                                Loading word information...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <!-- Footer -->
        <footer class="bg-white border-t border-gray-200">
            <div class="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
                <p class="text-center text-sm text-gray-500">
                    Eulogos &copy; 2025
                </p>
            </div>
        </footer>
    </div>

    <!-- Custom JavaScript to handle text interactions -->
    <script>
    document.addEventListener('alpine:init', () => {
        // Add event delegation for text parts
        document.querySelector('#reader-container').addEventListener('click', (e) => {
            const token = e.target.closest('.token');
            if (token) {
                const alpineScope = Alpine.closest(token);
                if (alpineScope && alpineScope.textMode === 'highlight') {
                    alpineScope.selectedToken = token.dataset.token;

                    // Remove previous highlights
                    document.querySelectorAll('.token-highlighted').forEach(el => {
                        el.classList.remove('token-highlighted');
                    });

                    // Add highlight to this token
                    token.classList.add('token-highlighted');

                    // Prevent default navigation if in highlight mode
                    e.preventDefault();
                }
            }
        });
    });
    </script>
</body>
</html>
```

### 5. App Integration

Update `app/main.py` to include the export router:

```python
# Add import
from app.routers import export

# Include export router
app.include_router(export.router)
```

## Dependencies

To implement this system, the following Python packages are required:

```
# core requirements
fastapi>=0.95.0
uvicorn>=0.22.0
pydantic>=2.0.0
lxml>=4.9.2
jinja2>=3.1.2
httpx>=0.24.0

# for export functionality
weasyprint>=59.0  # for PDF generation
ebooklib>=0.18.0  # for ePub generation
html2text>=2020.1.16  # for Markdown conversion
python-docx>=0.8.11  # for DOCX generation
beautifulsoup4>=4.11.1  # for HTML parsing

# for additional formats
# kindlegen - binary executable for MOBI conversion (not a Python package)
# alternatively: calibre - for ebook-convert utility
```

### External Dependencies

Some export formats require external tools:

1. **MOBI/KF8 (Kindle) format:**
   - **KindleGen:** Amazon's command-line tool for creating Kindle books
     - Download from Amazon or use package manager (e.g., `brew install kindlegen` on macOS)
   - **Alternative:** Calibre's `ebook-convert` utility
     - Install Calibre: https://calibre-ebook.com/download

2. **LaTeX to PDF conversion:**
   - **TeX Live distribution** with XeLaTeX
     - Linux: `apt-get install texlive-xetex texlive-lang-greek`
     - macOS: Install MacTeX
     - Windows: Install MiKTeX or TeX Live

These external dependencies should be documented in the project README to ensure proper setup.

## Implementation Timeline

1. **Phase 1: Core Reference Handling (3-4 weeks)**
   - Implement URN model
   - Enhance XMLProcessorService
   - Create reader endpoints with reference navigation
   - Implement text display with proper formatting

2. **Phase 2: Export Service (2-3 weeks)**
   - Implement ExportService
   - Create export endpoints
   - Add export UI components
   - Test with various formats and options

3. **Phase 3: Enhancement and Optimization (1-2 weeks)**
   - Add advanced options for exports
   - Optimize performance for large texts
   - Improve error handling and user feedback
   - Add comprehensive tests

## Testing Strategy

1. **Unit Tests**
   - Test URN parsing and manipulation
   - Test XML processing and transformation
   - Test export functions with sample data

2. **Integration Tests**
   - Test end-to-end export workflows
   - Test API endpoints
   - Test UI components

3. **Manual Testing**
   - Test with various text types (prose, poetry, etc.)
   - Test different export formats
   - Test large texts for performance

## Conclusion

This implementation plan provides a comprehensive approach to enhancing the Eulogos project with robust text display and export capabilities. The modular design allows for future enhancements and optimizations while providing immediate value through high-quality text access and export functionality.

By implementing the Reference Handling System and building the Export Service on top of it, the project will achieve the goal of making ancient Greek texts both readable in the browser and exportable in various formats for offline access.
