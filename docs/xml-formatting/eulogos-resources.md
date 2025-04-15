# Useful Resources for Implementation

This document provides a collection of resources that will be helpful when implementing the Eulogos Text Export System.

## Libraries and Tools

### XML Processing

- **lxml**: Fast XML processing library
  - Documentation: https://lxml.de/
  - GitHub: https://github.com/lxml/lxml
  - Installation: `pip install lxml>=4.9.2`

- **BeautifulSoup**: HTML/XML parsing library
  - Documentation: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
  - GitHub: https://github.com/wention/BeautifulSoup4
  - Installation: `pip install beautifulsoup4>=4.11.1`

### PDF Generation

- **WeasyPrint**: HTML to PDF converter
  - Documentation: https://doc.courtbouillon.org/weasyprint/stable/
  - GitHub: https://github.com/Kozea/WeasyPrint
  - Installation: `pip install weasyprint>=59.0`
  - Dependencies: Cairo, Pango, and GDK-PixBuf (see documentation for OS-specific setup)

- **ReportLab**: PDF generation library (alternative to WeasyPrint)
  - Documentation: https://www.reportlab.com/docs/reportlab-userguide.pdf
  - GitHub: https://github.com/Distrotech/reportlab
  - Installation: `pip install reportlab`

### Ebook Formats

- **EbookLib**: Library for handling EPUB2/EPUB3 formats
  - Documentation: https://docs.sourcefabric.org/projects/ebooklib/
  - GitHub: https://github.com/aerkalov/ebooklib
  - Installation: `pip install ebooklib>=0.18.0`

- **KindleGen**: Amazon's tool for creating Kindle books
  - Download: https://archive.org/details/kindlegen-2.9
  - Note: Amazon has deprecated KindleGen, but archived versions are available
  - Installation: Download binary and add to system PATH

- **Calibre**: Comprehensive e-book library manager with conversion tools
  - Documentation: https://manual.calibre-ebook.com/
  - Website: https://calibre-ebook.com/
  - Command line: `ebook-convert` for format conversion
  - Installation: System-specific (see website)

### Document Formats

- **python-docx**: Library for creating and updating Microsoft Word (.docx) files
  - Documentation: https://python-docx.readthedocs.io/
  - GitHub: https://github.com/python-openxml/python-docx
  - Installation: `pip install python-docx>=0.8.11`

- **html2text**: HTML to Markdown converter
  - GitHub: https://github.com/Alir3z4/html2text/
  - Installation: `pip install html2text>=2020.1.16`

- **PyLaTeX**: Python library for creating LaTeX files
  - Documentation: https://jeltef.github.io/PyLaTeX/
  - GitHub: https://github.com/JelteF/PyLaTeX
  - Installation: `pip install pylatex`

## TEI XML Resources

- **TEI Guidelines**: Comprehensive documentation for Text Encoding Initiative XML
  - Documentation: https://tei-c.org/guidelines/
  - TEI for ancient texts: https://tei-c.org/Vault/GL/P5/Guidelines-en/html/AI.html

- **Perseus Digital Library**: Examples of TEI XML used for ancient Greek texts
  - Website: http://www.perseus.tufts.edu/
  - GitHub: https://github.com/PerseusDL/canonical-greekLit

- **Capitains Guidelines**: Best practices for CTS and TEI
  - Documentation: https://capitains.org/pages/guidelines
  - GitHub: https://github.com/Capitains

## CTS URN Resources

- **CITE Architecture**: Specifications for CTS URNs
  - Documentation: http://cite-architecture.org/
  - GitHub: https://github.com/cite-architecture

- **CTS URN Specification**: Detailed information about CTS URN format
  - Documentation: http://www.homermultitext.org/hmt-docs/cite/cts-urn-overview.html

- **CTS API**: Implementation of the CTS protocol
  - Documentation: https://capitains.org/pages/endpoints
  - Specification: https://github.com/cite-architecture/cts_spec

## Ancient Greek Typography and Fonts

- **SBL Greek Font**: Free font for ancient Greek with proper rendering of diacritics
  - Download: https://www.sbl-site.org/educational/BiblicalFonts_SBLGreek.aspx

- **New Athena Unicode**: Comprehensive polytonic Greek font
  - Download: https://apagreekkeys.org/NAUdownload.html

- **Gentium**: Unicode font with excellent support for ancient Greek
  - Download: https://software.sil.org/gentium/

- **Greek Typography**: Guidelines for proper typography of ancient Greek texts
  - Article: http://journals.openedition.org/jtei/1440

## FastAPI and Web Development

- **FastAPI**: Modern API framework for Python
  - Documentation: https://fastapi.tiangolo.com/
  - GitHub: https://github.com/tiangolo/fastapi
  - Installation: `pip install fastapi>=0.95.0`

- **HTMX**: HTML extension for dynamic content
  - Documentation: https://htmx.org/docs/
  - GitHub: https://github.com/bigskysoftware/htmx
  - CDN: `<script src="https://unpkg.com/htmx.org@1.9.4"></script>`

- **Alpine.js**: Lightweight JavaScript framework
  - Documentation: https://alpinejs.dev/start-here
  - GitHub: https://github.com/alpinejs/alpine
  - CDN: `<script src="https://unpkg.com/alpinejs@3.13.0" defer></script>`

- **Tailwind CSS**: Utility-first CSS framework
  - Documentation: https://tailwindcss.com/docs
  - GitHub: https://github.com/tailwindlabs/tailwindcss
  - CDN: `<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">`

## Testing Tools

- **pytest**: Testing framework for Python
  - Documentation: https://docs.pytest.org/
  - GitHub: https://github.com/pytest-dev/pytest
  - Installation: `pip install pytest>=7.3.1`

- **pytest-cov**: Coverage plugin for pytest
  - GitHub: https://github.com/pytest-dev/pytest-cov
  - Installation: `pip install pytest-cov>=4.1.0`

- **hypothesis**: Property-based testing
  - Documentation: https://hypothesis.readthedocs.io/
  - GitHub: https://github.com/HypothesisWorks/hypothesis
  - Installation: `pip install hypothesis`

- **Playwright**: Browser automation for UI testing
  - Documentation: https://playwright.dev/python/
  - GitHub: https://github.com/microsoft/playwright-python
  - Installation: `pip install playwright`

## Example Projects

- **Perseus Scaife Viewer**: Digital reading environment for classical texts
  - Website: https://scaife.perseus.org/
  - GitHub: https://github.com/scaife-viewer/

- **Classical Text Editor**: Desktop application for editing classical texts
  - Website: https://cte.oeaw.ac.at/

- **Hypothesis Sparrow**: Web-based annotation for ancient texts
  - Website: https://hypothes.is/
  - GitHub: https://github.com/hypothesis/h

## Tutorials and Examples

### XML Processing and Reference Handling

```python
from lxml import etree
from pathlib import Path

# Parse XML file
xml_file = Path("data/greekLit/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml")
tree = etree.parse(str(xml_file))
root = tree.getroot()

# Define namespaces
namespaces = {
    "tei": "http://www.tei-c.org/ns/1.0",
    "xml": "http://www.w3.org/XML/1998/namespace"
}

# Extract references from TEI XML
def extract_references(element, parent_ref=""):
    references = {}
    n_attr = element.get("n")

    if n_attr:
        ref = f"{parent_ref}.{n_attr}" if parent_ref else n_attr
        references[ref] = element
    else:
        ref = parent_ref

    # Process child elements
    for child in element.xpath(".//tei:div[@type='textpart']", namespaces=namespaces):
        child_refs = extract_references(child, ref)
        references.update(child_refs)

    return references

# Example usage
references = extract_references(root)
print(f"Found {len(references)} references in the document.")
```

### PDF Generation with WeasyPrint

```python
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import tempfile

def create_pdf(html_content, css_content=None):
    # Set up font configuration
    font_config = FontConfiguration()

    # Create a temporary file for the HTML
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        html_file = f.name
        f.write(html_content.encode('utf-8'))

    # Generate PDF
    html = HTML(filename=html_file)

    # Add CSS if provided
    stylesheets = []
    if css_content:
        stylesheets.append(CSS(string=css_content, font_config=font_config))

    # Generate PDF
    pdf_bytes = html.write_pdf(font_config=font_config, stylesheets=stylesheets)

    # Clean up temporary file
    import os
    os.unlink(html_file)

    return pdf_bytes

# Example usage
html = """
<!DOCTYPE html>
<html>
<head>
    <title>Sample PDF</title>
</head>
<body>
    <h1>Sample Document</h1>
    <p>This is a sample document with Greek text: Θησεύς καὶ Πειρίθοος</p>
</body>
</html>
"""

css = """
body {
    font-family: "SBL Greek", serif;
    font-size: 12pt;
    line-height: 1.5;
}
h1 {
    color: #333;
}
"""

pdf_content = create_pdf(html, css)
with open("sample.pdf", "wb") as f:
    f.write(pdf_content)
```

### EPUB Creation with ebooklib

```python
import ebooklib
from ebooklib import epub

def create_epub(title, author, content, language="en"):
    # Create a new EPUB book
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(f"{title.lower().replace(' ', '_')}")
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    # Create a chapter
    chapter = epub.EpubHtml(title=title, file_name='text.xhtml')
    chapter.content = content
    book.add_item(chapter)

    # Add CSS
    style = '''
        body { font-family: serif; }
        h1 { text-align: center; }
    '''
    css = epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=style
    )
    book.add_item(css)

    # Add chapter to the book and table of contents
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav', chapter]
    book.toc = [epub.Link('text.xhtml', title, title)]

    # Create epub file
    epub_file = f"{title.lower().replace(' ', '_')}.epub"
    epub.write_epub(epub_file, book, {})

    return epub_file

# Example usage
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Sample Book</title>
    <link rel="stylesheet" href="style.css" type="text/css" />
</head>
<body>
    <h1>Greek Literature</h1>
    <p>This is a sample chapter with Greek text: Θησεύς καὶ Πειρίθοος</p>
</body>
</html>
"""

epub_file = create_epub("Greek Literature", "Homer", html_content, "grc")
print(f"Created EPUB file: {epub_file}")
```

These resources and examples should provide a solid foundation for implementing the Eulogos Text Export System as outlined in the requirements and design documents.
