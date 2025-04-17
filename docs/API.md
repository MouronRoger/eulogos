# Eulogos API Documentation

## Core Services

### EnhancedCatalogService

The `EnhancedCatalogService` provides access to the integrated catalog data. It uses the `integrated_catalog.json` file as the single source of truth for all text metadata.

#### Key Methods

- `load_catalog(force_reload=False)` - Load the catalog from file
- `get_text_by_urn(urn)` - Get a text by URN
- `get_path_by_urn(urn)` - Get the file path for a text by URN
- `resolve_file_path(urn)` - Resolve a URN to a full file path
- `get_authors(include_archived=False)` - Get all authors
- `get_texts_by_author(author_id, include_archived=False)` - Get all texts by an author
- `validate_path_consistency()` - Validate that all URNs have valid paths
- `archive_text(urn, archive=True)` - Archive or unarchive a text
- `toggle_favorite(urn)` - Toggle favorite status for a text

### EnhancedXMLService

The `EnhancedXMLService` handles XML document processing. It uses the `EnhancedCatalogService` for path resolution and implements caching for performance.

#### Key Methods

- `load_document(urn)` - Load an XML document by URN
- `get_passage(urn, reference=None)` - Get a passage from an XML document
- `transform_to_html(urn, reference=None)` - Transform a passage to HTML
- `get_adjacent_references(urn, current_ref)` - Get previous and next references

### EnhancedExportService

The `EnhancedExportService` provides export functionality for various formats. It uses the `EnhancedCatalogService` and `EnhancedXMLService` to access and process texts.

#### Key Methods

- `export_to_html(urn, options=None)` - Export text to HTML
- `export_to_markdown(urn, options=None)` - Export text to Markdown
- `export_to_latex(urn, options=None)` - Export text to LaTeX

## API Endpoints

### Export API

#### Get Available Export Formats

```http
GET /export/formats
```

Returns a list of available export formats.

Response:
```json
{
    "formats": [
        {
            "id": "html",
            "name": "HTML",
            "description": "Export as standalone HTML file",
            "mime_type": "text/html",
            "extension": ".html"
        },
        {
            "id": "markdown",
            "name": "Markdown",
            "description": "Export as Markdown file",
            "mime_type": "text/markdown",
            "extension": ".md"
        },
        {
            "id": "latex",
            "name": "LaTeX",
            "description": "Export as LaTeX document",
            "mime_type": "application/x-latex",
            "extension": ".tex"
        }
    ]
}
```

#### Export Text to HTML

```http
POST /export/{urn}/html
```

Export a text to HTML format.

Request Body:
```json
{
    "reference": "1.1",
    "filename": "custom_name.html",
    "include_metadata": true,
    "custom_css": "body { font-size: 14px; }"
}
```

Response: HTML file download

#### Export Text to Markdown

```http
POST /export/{urn}/markdown
```

Export a text to Markdown format.

Request Body:
```json
{
    "reference": "1.1",
    "filename": "custom_name.md",
    "include_metadata": true
}
```

Response: Markdown file download

#### Export Text to LaTeX

```http
POST /export/{urn}/latex
```

Export a text to LaTeX format.

Request Body:
```json
{
    "reference": "1.1",
    "filename": "custom_name.tex",
    "include_metadata": true
}
```

Response: LaTeX file download

## Models

### EnhancedURN

Enhanced Pydantic model for CTS URNs. It provides methods for parsing, validating, and manipulating URNs.

#### Key Methods

- `parse()` - Parse the URN string into components
- `is_valid_for_path()` - Check if the URN has all components needed for path resolution
- `get_file_path(base_dir="data")` - Derive file path from URN components

### Catalog Models

- `TextVersion` - Represents a version of a text (edition or translation)
- `Work` - Represents a work with editions and translations
- `Author` - Represents an author with works
- `Catalog` - Represents the entire catalog

### XML Document Models

- `XMLReference` - Represents a reference to a section in an XML document
- `XMLDocument` - Represents a parsed XML document with references

## Configuration

The `EulogosSettings` class provides configuration for the application. It supports environment variables with the `EULOGOS_` prefix and a `.env` file.

### Key Settings

- `catalog_path` - Path to the integrated catalog JSON file
- `data_dir` - Base directory for text data files
- `xml_cache_size` - Maximum number of XML documents to cache
- `enable_caching` - Enable caching for XML documents
- `compatibility_mode` - Enable compatibility with existing code

## Error Handling

All API endpoints use proper error handling and return appropriate HTTP status codes:

- 200: Success
- 400: Bad Request (e.g., invalid URN format)
- 404: Not Found (text not found)
- 500: Internal Server Error

Error responses include a detail message explaining the error:

```json
{
    "detail": "Error message here"
}
```

## Caching

The XML service implements caching for improved performance:

- XML documents are cached in memory
- Cache size is configurable via settings
- LRU (Least Recently Used) cache eviction policy
- Cache can be disabled if needed

## File Cleanup

Exported files are automatically cleaned up:

- Files are created in a temporary directory
- Files are deleted after being sent to the client
- Background tasks handle cleanup to avoid blocking
- Parent directories are also cleaned up

## Backward Compatibility

The system maintains backward compatibility through adapter classes:

- `CatalogServiceAdapter` - Adapts to old CatalogService interface
- `XMLProcessorServiceAdapter` - Adapts to old XMLProcessorService interface

This allows gradual migration from the old to the new architecture.
