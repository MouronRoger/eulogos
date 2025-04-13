# First1KGreek Browser System Specification

## 1. System Overview

First1KGreek Browser is a web application for accessing, searching, and studying ancient Greek texts from the First 1000 Years Project. The system provides scholars, students, and enthusiasts with tools to browse texts by author or editor, read works with specialized viewing options, search across the corpus, and import new texts from external sources such as Scaife/Perseus.

### 1.1 Core Assets

- TEI XML files containing Greek texts and metadata
- Author catalog in JSON format
- Import functionality from Scaife Digital Library

### 1.2 Target Users

- Classical scholars and researchers
- Students of ancient Greek literature
- Digital humanities practitioners
- General readers interested in ancient texts

## 2. Technology Stack

### 2.1 Backend

- **Python 3.9+**
- **FastAPI** - Modern API framework with automatic documentation
- **Pydantic** - Data validation and settings management
- **lxml** - Efficient XML processing
- **Jinja2** - Template engine for HTML generation

### 2.2 Frontend

- **HTMX** - For dynamic interactions without complex JavaScript
- **Alpine.js** - Minimal JavaScript framework for more complex UI needs
- **Tailwind CSS** - Utility-first CSS framework for styling

### 2.3 Data Storage

#### Initial Phase
- File-based storage (XML files and JSON catalog)
- Local filesystem organization

#### Future Extensions
- PostgreSQL for relational data
- Vector database for embeddings (e.g., Pinecone or Qdrant)

## 3. Data Model

### 3.1 Core Entities

#### 3.1.1 Author
```python
class Author(BaseModel):
    id: str  # e.g., "tlg0001"
    name: str
    century: Optional[int] = None  # Negative for BCE, positive for CE
    type: Optional[str] = None  # e.g., "historian", "philosopher" 
```

#### 3.1.2 Work
```python
class Work(BaseModel):
    id: str  # e.g., "tlg001"
    title: str
    author_id: str  # Reference to author
    language: str = "grc"  # Default Greek, "eng" for English
    file_paths: List[str]  # Paths to XML files
```

#### 3.1.3 Edition
```python
class Edition(BaseModel):
    id: str  # e.g., "perseus-grc2"
    work_id: str  # Reference to work
    editor: Optional[str] = None
    date: Optional[str] = None
    language: str = "grc"
    file_path: str  # Path to XML file
```

#### 3.1.4 UserPreference (Client-side storage initially)
```python
class UserPreference(BaseModel):
    favorites: List[str] = []  # IDs of favorited items
    archived: List[str] = []  # IDs of archived items
    view_settings: Dict[str, Any] = {}  # UI preferences
```

### 3.2 File Structure

```
data/
├── authors.json                       # Author catalog
├── {author_id}/                       # e.g., tlg0001/
│   ├── __cts__.xml                    # Author metadata
│   ├── {work_id}/                     # e.g., tlg001/
│       ├── __cts__.xml                # Work metadata
│       ├── {full_id}.xml              # e.g., tlg0001.tlg001.perseus-grc2.xml
```

## 4. System Architecture

### 4.1 Component Diagram

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│  Web Browser      │◄───►│  FastAPI Backend  │◄───►│  XML/JSON Storage │
│  HTMX + Alpine.js │     │  Python Services  │     │  File-based       │
│                   │     │                   │     │                   │
└───────────────────┘     └───────────────────┘     └───────────────────┘
                                  ▲
                                  │
                                  ▼
                          ┌───────────────────┐
                          │                   │
                          │  External APIs    │
                          │  (Scaife/Perseus) │
                          │                   │
                          └───────────────────┘
```

### 4.2 API Structure

#### Authors API
- `GET /api/authors` - List all authors with optional filtering
- `GET /api/authors/{id}` - Get author details
- `GET /api/authors/{id}/works` - List works for author

#### Works API
- `GET /api/works/{id}` - Get work details
- `GET /api/works/{id}/editions` - List editions of work
- `GET /api/editions/{id}` - Get edition details

#### Content API
- `GET /api/content/{path}` - Get XML content with various rendering options
- `GET /api/content/{path}/raw` - Get raw XML
- `GET /api/content/{path}/reader` - Get reader-friendly HTML

#### Import API
- `POST /api/import/scaife` - Import text from Scaife URL

#### Search API
- `GET /api/search` - Search across corpus

### 4.3 UI Pages

- **Home Page** - Overview and navigation
- **Authors Browser** - List, sort, filter authors
- **Author Detail** - View author information and works
- **Work Reader** - View work content with various display options
- **Search Interface** - Search the corpus with filters
- **Import Interface** - Import new texts from Scaife/Perseus

## 5. Functional Requirements

### 5.1 Browsing and Navigation

1. Users shall be able to browse a complete list of authors
2. Users shall be able to sort authors by name, century, or type
3. Users shall be able to filter authors by century, type, or search term
4. Users shall be able to view an author's complete works
5. Users shall be able to navigate between authors, works, and editions

### 5.2 Reading and Viewing

1. Users shall be able to view original XML with syntax highlighting
2. Users shall be able to view texts in a reader-friendly format
3. Users shall be able to adjust display settings (font size, theme)
4. Users shall be able to see metadata about works and editions

### 5.3 Search Capabilities

1. Users shall be able to search across all texts in the corpus
2. Users shall be able to search by author, work, or content
3. Users shall be able to view search results with context
4. Users shall be able to navigate directly from search results to texts

### 5.4 Import Functionality

1. Users shall be able to import texts from Scaife/Perseus via URL
2. Users shall be able to provide additional metadata during import
3. System shall validate and process imported XML
4. System shall update catalog information after successful import

### 5.5 User Preferences

1. Users shall be able to mark authors and works as favorites
2. Users shall be able to archive authors and works
3. System shall store user preferences (initially client-side)
4. User preferences shall persist between sessions

## 6. Technical Implementation

### 6.1 Backend Services

#### 6.1.1 Catalog Service
- Manages author and work metadata
- Provides filtering and sorting capabilities
- Handles catalog updates during imports

#### 6.1.2 XML Processing Service
- Parses TEI XML files
- Extracts metadata and content
- Transforms XML to various output formats (HTML, plain text)

#### 6.1.3 Search Service
- Implements text search across corpus
- Builds and maintains search index
- Provides relevance-ranked results

#### 6.1.4 Import Service
- Handles communication with Scaife API
- Validates and processes imported XML
- Updates catalog and file structure

### 6.2 Frontend Implementation

#### 6.2.1 HTMX Integration
- Server-side rendering with dynamic updates
- Partial page updates for efficient interaction
- Progressive enhancement for robust functionality

#### 6.2.2 UI Components
- Author browsing table with sorting and filtering
- Work reader with display options
- Search interface with result highlighting
- Import form with validation

#### 6.2.3 Client-Side Features
- Local storage for user preferences
- Theme switching
- Reading position memory

### 6.3 Data Access Layer

#### 6.3.1 Initial File-Based Implementation
- JSON parsing for author catalog
- XML parsing for text content
- File system operations for storage

#### 6.3.2 Future Database Integration
- ORM models for database entities
- Repository pattern for data access
- Migration utilities from file-based to database storage

## 7. Project Structure

```
first1kgreek/
├── app/                      # Main application package
│   ├── api/                  # FastAPI routers
│   │   ├── authors.py
│   │   ├── works.py
│   │   ├── content.py
│   │   ├── search.py
│   │   └── import.py
│   ├── models/               # Pydantic models
│   │   ├── author.py
│   │   ├── work.py
│   │   └── preferences.py
│   ├── services/             # Business logic
│   │   ├── catalog.py        # Author/work catalog management
│   │   ├── xml_processor.py  # XML parsing and transformation
│   │   ├── search.py         # Text search implementation
│   │   └── importer.py       # Import functionality
│   ├── utils/                # Utility functions
│   │   ├── paths.py          # Path handling utilities
│   │   └── xml.py            # XML helper functions
│   └── main.py               # FastAPI application entry point
├── static/                   # Static assets
│   ├── css/                  # Tailwind and custom CSS
│   ├── js/                   # Alpine.js and custom scripts
│   └── img/                  # Images and icons
├── templates/                # Jinja2 templates
│   ├── base.html             # Base template
│   ├── partials/             # Reusable template parts
│   ├── authors/              # Author-related templates
│   ├── works/                # Work-related templates
│   ├── search.html           # Search interface
│   └── import.html           # Import interface
├── data/                     # Data directory
│   └── authors.json          # Author catalog
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── alembic/                  # Database migrations (future)
├── pyproject.toml            # Project metadata and dependencies
├── Dockerfile                # Container definition
└── docker-compose.yml        # Development environment setup
```

## 8. Development Roadmap

### 8.1 Phase 1: Minimum Viable Product

1. **Core Data Model** - Author and work models with file-based storage
2. **Basic API** - Endpoints for browsing authors and viewing texts
3. **Simple UI** - Author list, work list, and basic content viewer
4. **Import Capability** - Basic Scaife import functionality

### 8.2 Phase 2: Enhanced Features

1. **Advanced Browsing** - Sorting, filtering, and search capabilities
2. **Improved Reader** - Better text display with customization options
3. **User Preferences** - Favorites, archives, and view settings
4. **Better Import** - Enhanced import with metadata extraction

### 8.3 Phase 3: Database Integration

1. **Relational Schema** - PostgreSQL schema design
2. **ORM Models** - SQLAlchemy models for data entities
3. **Migration Utilities** - Tools to convert from files to database
4. **API Refactoring** - Update services to use database repositories

### 8.4 Phase 4: Vector Embeddings

1. **Text Processing** - Extract and clean text for embeddings
2. **Embedding Generation** - Create vector representations of texts
3. **Vector Store Integration** - Connect to vector database
4. **Semantic Search** - Implement similarity-based search

## 9. Deployment Considerations

### 9.1 Development Environment

- Docker-based development environment
- Hot-reloading for code changes
- Test data for development

### 9.2 Production Deployment

- Container-based deployment
- Environment-based configuration
- Static asset serving through CDN
- Rate limiting for API endpoints

### 9.3 Performance Optimization

- Response caching for frequent requests
- Pagination for large result sets
- Lazy loading of content
- XML processing optimization

## 10. Metrics and Monitoring

### 10.1 Performance Metrics

- API response times
- Page load times
- Search performance
- XML processing times

### 10.2 Usage Metrics

- Most viewed authors and works
- Search term frequency
- Import success rate
- User preference patterns

## 11. Future Extensions

### 11.1 Advanced Text Analysis

- Named entity recognition
- Topic modeling
- Cross-reference detection
- Parallel text alignment

### 11.2 Collaboration Features

- User accounts and authentication
- Shared annotations
- Export capabilities
- Reading groups

### 11.3 Integration Possibilities

- Integration with other classical text repositories
- Citation linking with standard reference systems
- Bibliography management
- Academic research tools
