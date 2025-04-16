# Eulogos System Architecture

## 1. System Overview

Eulogos is a web application for accessing, viewing, and studying ancient Greek texts from the First 1000 Years Project. The system provides scholars, students, and enthusiasts with robust tools to browse texts by author, read works with specialized viewing options, search across the corpus, and export texts in various formats.

### 1.1 Core Assets

- TEI XML files containing Greek texts and metadata
- Author catalog in JSON format
- CTS URN-based reference system
- Unified catalog combining author and text metadata

### 1.2 Target Users

- Classical scholars and researchers
- Students of ancient Greek literature
- Digital humanities practitioners
- General readers interested in ancient Greek texts

## 2. Technology Stack

### 2.1 Backend

- **Python 3.9+**
- **FastAPI**: Modern API framework with automatic documentation
- **Pydantic**: Data validation and settings management
- **lxml**: Efficient XML processing
- **Jinja2**: Template engine for HTML generation

### 2.2 Frontend

- **HTMX**: For dynamic interactions without complex JavaScript
- **Alpine.js**: Lightweight JavaScript framework for reactive components
- **Tailwind CSS**: Utility-first CSS framework for styling

### 2.3 Data Storage

#### Phase 1 (Current)
- Unified JSON catalog combining author and text metadata
- TEI XML files organized by CTS URN structure
- File-based storage and organization

#### Future Phases
- Phase 2: PostgreSQL for relational data
- Phase 3: Vector database for embeddings (e.g., Pinecone or Qdrant)

## 3. System Architecture

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

## 4. Core Components

### 4.1 Data Models

#### 4.1.1 Unified Catalog Model

```python
class Author(BaseModel):
    """Author model."""
    name: str
    century: int  # Negative for BCE, positive for CE
    type: str
    archived: bool = False

class Text(BaseModel):
    """Text model with author reference."""
    urn: str
    group_name: str
    work_name: str
    language: str
    wordcount: int
    scaife: Optional[str] = None
    author_id: Optional[str] = None
    archived: bool = False
    favorite: bool = False

    # Derived fields (not stored in JSON)
    namespace: Optional[str] = Field(None, exclude=True)
    textgroup: Optional[str] = Field(None, exclude=True)
    work_id: Optional[str] = Field(None, exclude=True)
    version: Optional[str] = Field(None, exclude=True)
```

#### 4.1.2 URN Model

```python
class URN(BaseModel):
    """Model for Canonical Text Services URNs."""
    value: str
    urn_namespace: Optional[str] = None
    namespace: Optional[str] = None
    text_group: Optional[str] = None
    work: Optional[str] = None
    version: Optional[str] = None
    reference: Optional[str] = None

    # Methods: parse(), up_to(), replace(), get_file_path(), etc.
```

### 4.2 Core Services

#### 4.2.1 CatalogService

Responsible for accessing and managing the unified catalog:

- Loading and parsing catalog data
- Providing filtered access to authors and texts
- Managing text favorites and archive status
- Supporting search and filtering operations

#### 4.2.2 XMLProcessorService

Handles XML processing with reference management:

- Loading and parsing TEI XML files
- Extracting hierarchical references
- Transforming XML to HTML for display
- Providing reference navigation
- Supporting token-level text processing

#### 4.2.3 ExportService

Manages export operations for various formats:

- Converting XML content to multiple formats (PDF, ePub, etc.)
- Handling format-specific options and customization
- Managing external dependencies for specific formats
- Providing proper error handling and feedback

### 4.3 API Endpoints

The system provides these main API groups:

- **Browse API**: For browsing the catalog and text collection
- **Reader API**: For reading texts with reference navigation
- **Export API**: For exporting texts in various formats
- **Text Management API**: For archiving, favoriting, and deleting texts
- **Search API**: For searching text content and metadata

### 4.4 Frontend Components

The UI is built around these main components:

- **Author-Works Tree**: Hierarchical navigation of the text collection
- **Text Reader**: Display of texts with reference navigation
- **Export Interface**: Selection of export formats and options
- **Text Management**: Controls for archiving, favoriting, and deleting
- **Search Interface**: Text and metadata search capabilities

## 5. Reference Handling System

A key architectural feature is the reference handling system:

### 5.1 Reference Structure

- Hierarchical references based on the TEI XML structure
- References follow patterns like "1.2.3" (book.chapter.section)
- References directly map to elements in the XML document

### 5.2 Reference Navigation

- Navigation between adjacent references
- Table of contents based on reference hierarchy
- Direct linking to specific text passages

### 5.3 Token-Level Processing

- Texts processed at word/token level
- Each token has attributes for analysis and interaction
- Support for Greek-specific language features

## 6. Export Architecture

The export system follows a format-specific transformation approach:

### 6.1 Export Formats

- **PDF**: Generated using WeasyPrint with proper typesetting
- **ePub**: Created with ebooklib for e-readers
- **MOBI/Kindle**: Converted from ePub for Kindle devices
- **Markdown**: Simple text format for editing
- **DOCX**: Microsoft Word format for academic use
- **LaTeX**: Scholarly publication format
- **HTML**: Standalone web format

### 6.2 Export Process

1. Load XML content from URN
2. Apply format-specific transformations
3. Add metadata and formatting
4. Generate output file
5. Return formatted content to user

## 7. File Structure

```
app/
├── api/                # API endpoints
│   ├── v1/             # API version 1
│   │   ├── authors.py
│   │   ├── imports.py
│   │   ├── search.py
│   │   └── works.py
├── core/               # Core functionality
│   ├── config.py       # Configuration settings
│   └── logging.py      # Logging configuration
├── db/                 # Database models and functions (future)
├── models/             # Pydantic models
│   ├── catalog.py
│   ├── urn.py
│   └── export_options.py
├── services/           # Business logic services
│   ├── catalog_service.py
│   ├── xml_processor_service.py
│   └── export_service.py
├── templates/          # HTMX templates
│   ├── base.html
│   ├── browse.html
│   ├── reader.html
│   └── partials/
├── static/             # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── utils/              # Utility functions
│   ├── xml_parser.py
│   ├── path_utils.py
│   └── cts_utils.py
└── main.py             # FastAPI application entry point
```

## 8. Key Architectural Principles

### 8.1 Separation of Concerns

- Clear distinction between data models, services, and API endpoints
- Separation of business logic from presentation
- Modular components with well-defined interfaces

### 8.2 Progressive Enhancement

- Core functionality works without JavaScript
- Enhanced experience with HTMX and Alpine.js
- Mobile-responsive design with Tailwind CSS

### 8.3 Reference-Oriented Design

- CTS URN as the central reference mechanism
- Reference-based navigation and linking
- Citation and text reference capabilities

### 8.4 Extensibility

- Designed for future integration with database systems
- Groundwork for vector embeddings and semantic search
- Support for expanding to additional text corpora

## 9. Future Architectural Extensions

### 9.1 Database Integration

- PostgreSQL schema based on the unified catalog structure
- SQLAlchemy ORM models with appropriate relationships
- Proper indexing for efficient querying

### 9.2 Vector Embeddings

- Embedding models for ancient Greek texts
- Text chunking strategy for optimal retrieval
- Integration with vector database (FAISS, Qdrant, or Pinecone)

### 9.3 Advanced Search

- Full-text search capabilities
- Semantic search with vector embeddings
- Faceted search with filtering
