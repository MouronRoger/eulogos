# Eulogos Text Export System Design Document

## 1. Introduction

### 1.1 Purpose

This document outlines the design for enhancing the Eulogos project with improved XML text formatting and multi-format export capabilities. The design focuses on creating a robust system that properly displays ancient Greek texts in the browser and allows users to export them in various formats (PDF, ePub, Markdown, DOCX) for offline reading and scholarly use.

### 1.2 Scope

The design covers:
- Enhanced XML processing with proper reference handling
- Export service for multiple document formats
- API endpoints for text export
- UI components for export functionality

### 1.3 Design Goals

- Maintain textual fidelity, including structure, formatting, and references
- Provide high-quality exports in multiple formats
- Create a modular, maintainable system that integrates with existing components
- Optimize for performance with large texts
- Ensure accessibility and compatibility

## 2. System Architecture

### 2.1 High-Level Architecture

The Eulogos Text Export System builds on the existing architecture with new and enhanced components:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  Web Interface  │────▶│  FastAPI Backend │────▶│  XML Processor  │
│  (HTMX+Alpine)  │◀────│  (API Endpoints) │◀────│  Service        │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                  ┌─────────────────┐
                                                  │                 │
                                                  │  Export Service │
                                                  │                 │
                                                  └─────────────────┘
```

### 2.2 Component Overview

1. **URN Model**: Pydantic model for parsing and manipulating CTS URNs
2. **XMLProcessorService**: Enhanced service for processing TEI XML with reference handling
3. **ExportService**: New service for converting XML content to various formats
4. **Export API Endpoints**: FastAPI endpoints for export functionality
5. **Export UI Components**: User interface elements for export options

### 2.3 Data Flow

1. User selects a text to view in the browser
2. XMLProcessorService loads and processes the TEI XML, extracting references
3. Transformed HTML is displayed in the browser with proper formatting
4. User selects export option and format
5. Export API is called with URN and format options
6. ExportService retrieves the XML content via XMLProcessorService
7. Content is converted to the requested format and returned to the user

## 3. Detailed Component Design

### 3.1 URN Model

The URN model provides structured parsing and manipulation of Canonical Text Services URNs.

#### 3.1.1 Class Definition

```python
class URN(BaseModel):
    value: str
    urn_namespace: Optional[str] = None
    cts_namespace: Optional[str] = None
    text_group: Optional[str] = None
    work: Optional[str] = None
    version: Optional[str] = None
    reference: Optional[str] = None

    # Methods: parse(), up_to(), replace(), __str__()
```

#### 3.1.2 Key Methods

- `parse()`: Extracts components from the URN string
- `up_to(segment)`: Returns the URN truncated at a specific segment
- `replace(**kwargs)`: Creates a new URN with replaced components
- `get_file_path()`: Gets file path from URN
- `get_adjacent_references()`: Gets previous/next references

### 3.2 XMLProcessorService

The XMLProcessorService provides advanced TEI XML processing with reference handling.

#### 3.2.1 Class Definition

```python
class XMLProcessorService:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}

    # Methods for XML processing and transformation
```

#### 3.2.2 Key Methods

- `resolve_urn_to_file_path(urn_obj)`: Maps a URN to a file path
- `load_xml(urn_obj)`: Loads XML content from a file
- `extract_references(element, parent_ref)`: Extracts hierarchical references
- `get_passage_by_reference(xml_root, reference)`: Retrieves a specific passage
- `get_adjacent_references(xml_root, current_ref)`: Gets previous and next references
- `tokenize_text(text)`: Splits text into words and punctuation
- `transform_to_html(xml_root, target_ref)`: Transforms XML to HTML with references

### 3.3 ExportService

The ExportService converts XML content to various document formats.

#### 3.3.1 Class Definition

```python
class ExportService:
    def __init__(self, xml_processor: XMLProcessorService, catalog_service: CatalogService):
        self.xml_processor = xml_processor
        self.catalog_service = catalog_service

    # Methods for exporting to different formats
```

#### 3.3.2 Key Methods

- `get_text_metadata(urn)`: Retrieves metadata for a text
- `export_to_pdf(urn, options)`: Exports text to PDF format
- `export_to_epub(urn, options)`: Exports text to ePub format
- `export_to_mobi(urn, options)`: Exports text to MOBI/KF8 format for Kindle
- `export_to_markdown(urn, options)`: Exports text to Markdown format
- `export_to_docx(urn, options)`: Exports text to DOCX (Word) format
- `export_to_latex(urn, options)`: Exports text to LaTeX format
- `export_to_html(urn, options)`: Exports text to standalone HTML format

#### 3.3.3 Format-Specific Implementation Details

**PDF Export**
- Uses WeasyPrint to convert HTML to PDF
- Applies custom CSS for proper typography
- Supports page size, margins, and font options
- Includes metadata and table of contents

**ePub Export**
- Uses ebooklib to create ePub packages
- Creates proper navigation structure
- Preserves text formatting with CSS
- Includes metadata and cover information

**MOBI/KF8 Export**
- Uses KindleGen or Calibre's ebook-convert
- Converts from ePub as intermediate format
- Ensures compatibility with Kindle devices
- Preserves navigation and formatting

**Markdown Export**
- Uses html2text to convert HTML to Markdown
- Preserves headings, lists, and basic formatting
- Adds metadata as frontmatter
- Maintains reference structure where possible

**DOCX Export**
- Uses python-docx to create Word documents
- Applies paragraph and character styles
- Preserves document structure
- Includes metadata and table of contents

**LaTeX Export**
- Generates LaTeX source code
- Optionally compiles to PDF using XeLaTeX
- Includes appropriate packages for Greek text
- Structures document with proper sectioning

**HTML Export**
- Creates standalone HTML file
- Includes embedded CSS styling
- Optionally adds JavaScript for interactivity
- Structures content for web accessibility

### 3.4 Export API Endpoints

The API endpoints provide access to export functionality.

#### 3.4.1 Endpoint Definitions

```python
@router.get("/export/{urn}")
async def export_text(
    urn: str,
    format: str = Query("pdf", description="Export format: pdf, epub, mobi, markdown, docx, latex, html"),
    options: Dict = Depends(parse_export_options),
    export_service: ExportService = Depends(get_export_service)
):
    """Export text in specified format."""
    # Implementation details...
```

#### 3.4.2 Option Parsing

```python
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
    # Implementation details...
```

### 3.5 UI Components

The user interface includes components for selecting export options.

#### 3.5.1 Export Button and Dropdown

```html
<!-- Export Options Dropdown -->
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
```

## 4. Text Processing and Transformation

### 4.1 XML Parsing Strategy

The system parses TEI XML using the following strategies:

1. **Hierarchical Structure Preservation**
   - Maintains the nested structure of elements
   - Preserves parent-child relationships
   - Preserves document divisions and sections

2. **Reference Extraction**
   - Extracts identifiers from `@n` attributes
   - Builds hierarchical references (e.g., "1.2.3" for book.chapter.section)
   - Associates references with corresponding elements

3. **Token Processing**
   - Splits text into individual tokens (words and punctuation)
   - Preserves token order and positioning
   - Enables word-level analysis and interaction

### 4.2 HTML Transformation

When transforming XML to HTML, the system applies these techniques:

1. **Element Mapping**
   - Maps TEI elements to appropriate HTML elements
   - Preserves semantic meaning where possible
   - Adds CSS classes for styling

2. **Reference Preservation**
   - Adds `data-reference` attributes to elements
   - Creates navigable section numbers
   - Enables linking to specific passages

3. **Text Processing**
   - Wraps words in `<span class="token">` elements
   - Preserves whitespace appropriately
   - Handles special characters and symbols

### 4.3 Export Transformation

For exports, the system follows these approaches:

1. **Format-Specific Optimization**
   - Applies appropriate strategies for each target format
   - Optimizes structure for best rendering in each format
   - Ensures proper handling of Greek characters

2. **Metadata Inclusion**
   - Adds title, author, and other metadata
   - Creates appropriate document structure
   - Includes references to source material

3. **Styling and Typography**
   - Applies appropriate typography for ancient texts
   - Ensures proper rendering of Greek characters and diacritics
   - Creates consistent styling across formats

## 5. External Dependencies

### 5.1 Required Python Packages

```
# Core dependencies
fastapi>=0.95.0
uvicorn>=0.22.0
pydantic>=2.0.0
lxml>=4.9.2
jinja2>=3.1.2
httpx>=0.24.0

# Export dependencies
weasyprint>=59.0        # PDF generation
ebooklib>=0.18.0        # ePub creation
html2text>=2020.1.16    # Markdown conversion
python-docx>=0.8.11     # DOCX generation
beautifulsoup4>=4.11.1  # HTML parsing
```

### 5.2 External Tools

1. **KindleGen or Calibre**
   - Required for MOBI/KF8 format generation
   - Command-line tools called via subprocess

2. **XeLaTeX**
   - Required for PDF generation from LaTeX
   - Part of TeX Live or MiKTeX distribution

### 5.3 Fonts and Resources

1. **Greek Fonts**
   - SBL Greek or New Athena Unicode for proper display of Greek characters
   - System must ensure these are available for PDF generation

2. **CSS Stylesheets**
   - Custom stylesheets for various formats
   - Typography settings for ancient Greek

## 6. Error Handling and Edge Cases

### 6.1 Error Handling Strategy

1. **XML Parsing Errors**
   - Graceful handling of malformed XML
   - Clear error messages for parsing failures
   - Fallback to simpler parsing if complex parsing fails

2. **Missing References**
   - Proper handling when references cannot be found
   - Default to full text display when specific references are unavailable
   - Clear user feedback when navigation fails

3. **Export Failures**
   - Comprehensive error handling during export
   - Detailed error messages for troubleshooting
   - Graceful degradation when external tools fail

### 6.2 Performance Considerations

1. **Large Document Handling**
   - Efficient processing for large XML files
   - Pagination or chunking for very large documents
   - Memory-efficient algorithms for export

2. **Export Process Management**
   - Asynchronous processing for long-running exports
   - Progress indication for users
   - Timeout handling and recovery

### 6.3 Accessibility and Compatibility

1. **Unicode Handling**
   - Proper handling of Greek Unicode characters
   - Support for various encoding schemes
   - Conversion between encodings when necessary

2. **Cross-Browser Compatibility**
   - Testing across major browsers
   - Progressive enhancement approach
   - Fallbacks for older browsers

## 7. Future Extensions

### 7.1 Bilingual Text Support

Future extensions could include support for bilingual text display and export:

1. **Reference-Based Alignment**
   - Use shared reference systems to align original and translation
   - Split view or interleaved display options
   - Export with side-by-side or parallel text

2. **Pre-Aligned Bilingual Editions**
   - Support for pre-aligned bilingual XML
   - Special export formats optimized for bilingual display
   - Enhanced navigation between languages

### 7.2 Advanced Search and Analysis

The reference handling system can enable advanced search and analysis:

1. **Reference-Based Search**
   - Search within specific reference ranges
   - Results displayed with reference context
   - Export of search results with references

2. **Text Analysis Tools**
   - Word frequency analysis
   - Concordance generation
   - Collocation analysis

### 7.3 Annotation and Commentary

The system could be extended to support annotations:

1. **User Annotations**
   - Attach notes to specific references
   - Export with annotations included
   - Sharing of annotations

2. **Commentary Integration**
   - Link external commentaries to references
   - Include commentary in exports
   - Multi-layered display of text and commentary

## 8. Implementation Strategy

### 8.1 Phased Approach

The implementation will follow this phased approach:

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

### 8.2 Testing Strategy

The testing approach will include:

1. **Unit Tests**
   - Test individual components in isolation
   - Ensure correct functionality of parsing and transformation
   - Verify proper handling of edge cases

2. **Integration Tests**
   - Test components working together
   - Verify end-to-end export workflows
   - Test with real XML data

3. **UI Tests**
   - Verify correct functioning of UI components
   - Test user interactions with export options
   - Test error handling and feedback

### 8.3 Documentation

The implementation will include comprehensive documentation:

1. **Code Documentation**
   - Detailed docstrings for all classes and methods
   - Clear explanation of algorithms and approaches
   - Inline comments for complex operations

2. **User Documentation**
   - Instructions for using export features
   - Explanation of available options
   - Troubleshooting guidance

3. **Developer Documentation**
   - Architecture overview
   - Extension points for future development
   - Dependency management instructions

## 9. Conclusion

This design document outlines a comprehensive approach to enhancing the Eulogos project with robust XML text formatting and multi-format export capabilities. The design prioritizes textual fidelity, user experience, and extensibility while building on the existing architecture.

By implementing the components and approaches described in this document, the Eulogos project will provide a high-quality reading experience for ancient Greek texts, both in the browser and through various export formats for offline use.
