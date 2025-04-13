# Eulogos Browser System Specification (Revised)

## 1. System Overview

Eulogos Browser is a web application for accessing, viewing, and managing ancient Greek texts from the First 1000 Years Project. The system provides scholars, students, and enthusiasts with tools to browse texts by author, read works with specialized viewing options, and manage their collection through archiving and filtering capabilities.

### 1.1 Core Assets

- TEI XML files containing Greek texts and metadata
- Author catalog in JSON format
- CTS URN-based reference system

### 1.2 Target Users

- Classical scholars and researchers
- Students of ancient Greek literature
- Digital humanities practitioners
- General readers interested in ancient Greek texts

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

#### Phase 1 (Current)
- Unified JSON catalog combining author and text metadata
- TEI XML files organized by CTS URN structure
- File-based storage and organization

#### Future Phases (For Reference)
- Phase 2: PostgreSQL for relational data
- Phase 3: Vector database for embeddings

## 3. Data Model

### 3.1 Unified Catalog Structure

```json
{
  "statistics": {
    "nodeCount": 275030,
    "greekWords": 25580179,
    "authorCount": 1024,
    "textCount": 9876
  },
  "authors": {
    "tlg0007": {
      "name": "Plutarch",
      "century": 1,
      "type": "Platonist"
    },
    "tlg0012": {
      "name": "Homer", 
      "century": -8,
      "type": "Poet"
    }
    // more authors...
  },
  "catalog": [
    {
      "urn": "urn:cts:greekLit:tlg0007.tlg136.perseus-grc2",
      "group_name": "Plutarch",
      "work_name": "De Stoicorum Repugnantiis",
      "language": "grc",
      "wordcount": 8750,
      "scaife": "https://scaife.perseus.org/...",
      "author_id": "tlg0007",
      "archived": false
    }
    // more catalog entries...
  ]
}
```

### 3.2 Core Pydantic Models

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
    
    # Derived fields
    namespace: Optional[str] = Field(None, exclude=True)
    textgroup: Optional[str] = Field(None, exclude=True)
    work_id: Optional[str] = Field(None, exclude=True)
    version: Optional[str] = Field(None, exclude=True)
```

### 3.3 File Structure

```
data/
├── unified-catalog.json            # Combined author and catalog data
├── greekLit/                       # Namespace directory
│   ├── tlg0007/                    # Author directory (textgroup)
│   │   ├── tlg136/                 # Work directory
│   │   │   ├── tlg0007.tlg136.perseus-grc2.xml  # Text file
```

## 4. Phase 1 Core Features

### 4.1 Author-Works Tree Browser

A hierarchical browser that serves as the main navigation interface:

1. Authors listed alphabetically or by filter criteria
2. Each author expandable to show all works in a vertical tree structure
3. Works organized by title or identifier
4. Visual indicators for archived items
5. Quick access to view, archive, or delete functionality

### 4.2 Filtering and Sorting

1. **Author Filtering**:
   - By century (dropdown or range selector)
   - By type (dropdown for poet, historian, etc.)
   - By name (text search)

2. **Work Filtering**:
   - By language (primarily Greek)
   - By word count (range selector)
   - By title (text search)

3. **Sorting Options**:
   - Authors: alphabetical, chronological, by type
   - Works: alphabetical, by size, by identifier

### 4.3 Archive Management

1. **Archiving Functionality**:
   - Toggle to archive/unarchive authors
   - Toggle to archive/unarchive individual works
   - Batch archive/unarchive operations
   - Archived items remain in the system but are hidden by default

2. **Archive View**:
   - Dedicated view for browsing archived content
   - Option to restore items from archive
   - Filter and sort capabilities within archive view

### 4.4 XML Record Management

1. **Deletion Functionality**:
   - Option to permanently delete XML records
   - Confirmation dialog with impact assessment
   - Catalog update upon deletion

2. **XML Viewer**:
   - Basic viewer for TEI XML files
   - Syntax highlighting for better readability
   - Optional simplified reading view

### 4.5 Basic Search

1. Simple full-text search across author names and work titles
2. Basic filtering of search results
3. Direct navigation from search results to texts

## 5. System Architecture

### 5.1 Component Diagram

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│  Web Browser      │◄───►│  FastAPI Backend  │◄───►│  Unified Catalog  │
│  HTMX + Alpine.js │     │  Python Services  │     │  & XML Files      │
│                   │     │                   │     │                   │
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

### 5.2 API Endpoints

#### Catalog API
- `GET /api/catalog/authors` - List all authors with filtering options
- `GET /api/catalog/authors/{id}` - Get author details
- `GET /api/catalog/authors/{id}/works` - List works for author
- `GET /api/catalog/texts/{urn}` - Get text details
- `GET /api/catalog/texts` - List texts with filtering options

#### Content API
- `GET /api/content/{urn}` - Get XML content with viewing options
- `GET /api/content/{urn}/raw` - Get raw XML
- `GET /api/content/{urn}/reader` - Get reader-friendly HTML

#### Archive API
- `POST /api/archive/author/{id}` - Archive/unarchive author
- `POST /api/archive/text/{urn}` - Archive/unarchive text
- `GET /api/archive/authors` - List archived authors
- `GET /api/archive/texts` - List archived texts

#### Management API
- `DELETE /api/manage/author/{id}` - Delete author record
- `DELETE /api/manage/text/{urn}` - Delete text record

### 5.3 Core Services

#### CatalogService
```python
class CatalogService:
    """Service for accessing and managing the unified catalog."""
    
    def __init__(self, catalog_path: str = "data/unified-catalog.json"):
        # Initialize and load catalog
        
    def get_author(self, author_id: str) -> Optional[Author]:
        """Get author by ID."""
        
    def get_all_authors(self, archived: bool = False) -> List[Author]:
        """Get all authors, optionally including archived ones."""
        
    def get_text(self, urn: str) -> Optional[Text]:
        """Get text by URN."""
        
    def get_texts_by_author(self, author_id: str, archived: bool = False) -> List[Text]:
        """Get all texts by author ID, optionally including archived ones."""
        
    def archive_author(self, author_id: str, archive: bool = True) -> bool:
        """Archive or unarchive an author."""
        
    def archive_text(self, urn: str, archive: bool = True) -> bool:
        """Archive or unarchive a text."""
        
    def delete_author(self, author_id: str) -> bool:
        """Delete an author and optionally their works."""
        
    def delete_text(self, urn: str) -> bool:
        """Delete a text record and its file."""
        
    def search_catalog(self, query: str, include_archived: bool = False) -> Dict[str, List]:
        """Search the catalog for authors and texts."""
```

#### XMLProcessorService
```python
class XMLProcessorService:
    """Service for processing TEI XML files."""
    
    def __init__(self, base_path: str = "data"):
        # Initialize with base path
        
    def get_file_path(self, urn: str) -> Path:
        """Get file path from URN."""
        
    def load_xml(self, urn: str) -> Optional[ET._Element]:
        """Load XML content for a text."""
        
    def transform_to_html(self, xml_root: ET._Element, options: Dict = None) -> str:
        """Transform XML to HTML for viewing."""
        
    def delete_xml_file(self, urn: str) -> bool:
        """Delete XML file from filesystem."""
```

## 6. UI Pages and Components

### 6.1 Home/Browse Page
- Author-works tree as main navigation element
- Filtering and sorting controls
- Archive toggle buttons
- Search bar

### 6.2 Text Viewer Page
- XML/HTML display of text content
- Metadata panel
- Navigation controls
- Archive/delete options

### 6.3 Archive Management Page
- List of archived authors and works
- Restore functionality
- Permanent deletion options

### 6.4 Search Results Page
- Matching authors and works
- Quick filters
- Direct links to view content

## 7. Implementation Priorities for Phase 1

1. **Unified Catalog**:
   - Implement data validation for existing files
   - Create merger utility to generate unified catalog
   - Build efficient indexing and query capabilities

2. **Core UI**:
   - Author-works tree navigation
   - Basic filtering and sorting
   - XML viewer with syntax highlighting

3. **Archive Functionality**:
   - Implement archive/unarchive toggle
   - Create archive view
   - Ensure proper filtering to hide/show archived items

4. **Management Functions**:
   - Delete functionality with proper safeguards
   - Catalog update mechanisms
   - File system operations

5. **Basic Search**:
   - Simple catalog search implementation
   - Result display and navigation

## 8. Future Phase Considerations

### 8.1 Phase 2: Database Integration
- Design PostgreSQL schema based on the unified catalog structure
- Create migration path from file-based to database storage
- Maintain compatibility with Phase 1 functionality

### 8.2 Phase 3: Vectorization
- Prepare data model for vector embeddings
- Plan for text chunking and preprocessing
- Consider integration points for semantic search

## 9. Development Approach

- Modular service-based architecture
- Separation of data access, business logic, and presentation
- Extensive use of HTMX for dynamic UI without complex JavaScript
- Mobile-responsive design with Tailwind CSS
- Comprehensive logging for operations affecting the catalog
- Unit tests for core services and functionality
