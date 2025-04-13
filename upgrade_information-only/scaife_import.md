# Scaife Import System Redesign

This document outlines a redesigned Scaife import system for the First1KGreek Browser project, built from scratch with a modern FastAPI structure, HTMX integration, and using author_data.json as the canonical record.

## System Architecture

### 1. Core Components

```
first1k_browser/
├── app/                 # FastAPI application
│   ├── api/             # API endpoints
│   │   ├── v1/          # API version 1
│   │   │   ├── authors.py
│   │   │   ├── imports.py
│   │   │   ├── search.py
│   │   │   └── works.py
│   ├── core/            # Core functionality
│   │   ├── config.py    # Configuration settings
│   │   ├── security.py  # Authentication (if needed)
│   │   └── logging.py   # Logging configuration
│   ├── db/              # Database models and functions
│   │   ├── schemas.py   # Pydantic schemas
│   │   ├── models.py    # Data models
│   │   └── crud.py      # Database operations
│   ├── services/        # Business logic services
│   │   ├── author_service.py
│   │   ├── import_service.py
│   │   └── text_service.py
│   ├── templates/       # HTMX templates
│   │   ├── base.html
│   │   ├── components/  # Reusable HTMX components
│   │   ├── import/      # Import-specific templates
│   │   └── partials/    # Partial templates for HTMX updates
│   ├── static/          # Static files
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── utils/           # Utility functions
│   │   ├── xml_parser.py
│   │   ├── path_utils.py
│   │   └── cts_utils.py
│   └── main.py          # FastAPI application entry point
├── data/                # Data directory
│   ├── authors/         # Author data
│   │   └── author_data.json  # Canonical author data
│   └── texts/           # Imported text files
├── tests/               # Test suite
├── pyproject.toml       # Project dependencies
└── README.md            # Project documentation
```

### 2. Data Models

#### Author Schema

```python
class Author(BaseModel):
    id: str               # e.g., "tlg0007"
    name: str             # e.g., "Plutarch"
    century: int          # e.g., 1 (CE) or -4 (BCE)
    type: str             # e.g., "historian", "philosopher"
    works: List[str] = [] # List of work IDs

class AuthorCreate(BaseModel):
    id: str
    name: str
    century: int
    type: str

class AuthorUpdate(BaseModel):
    name: Optional[str] = None
    century: Optional[int] = None
    type: Optional[str] = None
```

#### Work Schema

```python
class Work(BaseModel):
    id: str                       # e.g., "tlg0007.tlg136"
    author_id: str                # e.g., "tlg0007"
    title: str                    # e.g., "De Stoicorum Repugnantiis"
    language: str = "grc"         # Default to Greek
    editions: List[Edition] = []  # Available editions

class Edition(BaseModel):
    id: str                       # e.g., "perseus-grc2"
    full_id: str                  # e.g., "tlg0007.tlg136.perseus-grc2"
    language: str                 # e.g., "grc", "eng" 
    source: str                   # e.g., "Perseus"
    file_path: str                # Path to XML file
```

#### Import Schema

```python
class ScaifeImport(BaseModel):
    url: str                      # Scaife URL
    author_name: Optional[str] = None
    work_title: Optional[str] = None
    
class BatchImport(BaseModel):
    urls: List[str]               # List of Scaife URLs
    default_author_name: Optional[str] = None
```

## 3. Core Services

### Author Service

```python
class AuthorService:
    def __init__(self, data_path: str = "data/authors/author_data.json"):
        self.data_path = data_path
        self._authors = self._load_authors()
        
    def _load_authors(self) -> Dict[str, Author]:
        # Load authors from author_data.json
        
    def get_author(self, author_id: str) -> Optional[Author]:
        # Get author by ID
    
    def get_all_authors(self) -> List[Author]:
        # Get all authors
        
    def create_author(self, author: AuthorCreate) -> Author:
        # Create a new author
        
    def update_author(self, author_id: str, author: AuthorUpdate) -> Optional[Author]:
        # Update an existing author
        
    def add_work_to_author(self, author_id: str, work_id: str) -> bool:
        # Add a work to an author's works list
        
    def save(self):
        # Save author data back to author_data.json
```

### Import Service

```python
class ImportService:
    def __init__(self, author_service: AuthorService, data_dir: str = "data/texts"):
        self.author_service = author_service
        self.data_dir = data_dir
        
    async def import_from_scaife(self, import_data: ScaifeImport) -> Dict[str, Any]:
        # Parse Scaife URL to extract URN components
        author_id, work_id, edition_id = self._parse_urn(import_data.url)
        
        # Create directory structure
        author_dir, work_dir = self._create_directories(author_id, work_id)
        
        # Fetch XML content
        xml_content = await self._fetch_xml(import_data.url)
        
        # Process author metadata
        author = self._process_author(author_id, import_data.author_name, xml_content)
        
        # Process work metadata
        work = self._process_work(author_id, work_id, import_data.work_title, xml_content)
        
        # Save XML content
        file_path = self._save_xml(author_id, work_id, edition_id, xml_content)
        
        # Update author_data.json
        self._update_author_data(author, work)
        
        return {
            "author": author,
            "work": work,
            "file_path": file_path,
            "success": True
        }
    
    async def batch_import(self, batch: BatchImport) -> List[Dict[str, Any]]:
        # Import multiple Scaife URLs
        results = []
        for url in batch.urls:
            import_data = ScaifeImport(
                url=url,
                author_name=batch.default_author_name
            )
            try:
                result = await self.import_from_scaife(import_data)
                results.append(result)
            except Exception as e:
                results.append({"url": url, "success": False, "error": str(e)})
        return results
    
    def _parse_urn(self, url: str) -> Tuple[str, str, str]:
        # Extract author_id, work_id, and edition_id from URL
        
    def _create_directories(self, author_id: str, work_id: str) -> Tuple[str, str]:
        # Create author and work directories
        
    async def _fetch_xml(self, url: str) -> str:
        # Fetch XML content from Scaife URL
        
    def _process_author(self, author_id: str, provided_name: Optional[str], 
                        xml_content: str) -> Author:
        # Get or create author
        
    def _process_work(self, author_id: str, work_id: str, provided_title: Optional[str], 
                      xml_content: str) -> Work:
        # Get or create work
        
    def _save_xml(self, author_id: str, work_id: str, edition_id: str, 
                  xml_content: str) -> str:
        # Save XML content to file
        
    def _update_author_data(self, author: Author, work: Work):
        # Update author_data.json with new author/work information
```

## 4. API Endpoints

### Imports API

```python
router = APIRouter(prefix="/api/v1/imports", tags=["imports"])

@router.post("/scaife", response_model=Dict[str, Any])
async def import_from_scaife(
    import_data: ScaifeImport,
    import_service: ImportService = Depends(get_import_service)
):
    """Import a text from Scaife URL"""
    return await import_service.import_from_scaife(import_data)

@router.post("/batch", response_model=List[Dict[str, Any]])
async def batch_import(
    batch: BatchImport,
    import_service: ImportService = Depends(get_import_service)
):
    """Import multiple texts from Scaife URLs"""
    return await import_service.batch_import(batch)
```

## 5. HTMX Integration

### Import Form Template

```html
<!-- templates/import/form.html -->
<div class="import-container">
    <h2>Import from Scaife</h2>
    
    <div class="tab-container">
        <div class="tabs">
            <button 
                class="tab active" 
                hx-get="/import/single-form" 
                hx-target="#tab-content">
                Single Import
            </button>
            <button 
                class="tab" 
                hx-get="/import/batch-form" 
                hx-target="#tab-content">
                Batch Import
            </button>
        </div>
        
        <div id="tab-content">
            <!-- Initial tab content (Single Import) -->
            <form hx-post="/api/v1/imports/scaife" 
                  hx-target="#import-results"
                  hx-indicator="#loading-indicator">
                
                <div class="form-group">
                    <label for="scaife-url">Scaife URL:</label>
                    <input type="text" 
                           id="scaife-url" 
                           name="url" 
                           placeholder="https://scaife.perseus.org/library/urn:cts:greekLit:tlg0007.tlg136.perseus-grc2:1-47/cts-api-xml/"
                           required>
                </div>
                
                <div class="form-group">
                    <label for="author-name">Author Name (optional):</label>
                    <input type="text" 
                           id="author-name" 
                           name="author_name"
                           placeholder="e.g., Plutarch">
                </div>
                
                <div class="form-group">
                    <label for="work-title">Work Title (optional):</label>
                    <input type="text" 
                           id="work-title" 
                           name="work_title"
                           placeholder="e.g., De Stoicorum Repugnantiis">
                </div>
                
                <button type="submit" class="btn btn-primary">
                    Import Text
                </button>
            </form>
        </div>
    </div>
    
    <div class="loading-indicator" id="loading-indicator">
        Importing text... <div class="spinner"></div>
    </div>
    
    <div id="import-results">
        <!-- Import results will be displayed here -->
    </div>
</div>
```

### Import Results Template

```html
<!-- templates/import/results.html -->
<div class="import-results">
    {% if success %}
    <div class="alert alert-success">
        <h3>Import Successful!</h3>
        <p>Imported <strong>{{ work.title }}</strong> by <strong>{{ author.name }}</strong></p>
        <p>File saved to: <code>{{ file_path }}</code></p>
        
        <div class="actions">
            <a href="/view?path={{ file_path }}" class="btn btn-secondary">
                View XML
            </a>
            <a href="/reader?path={{ file_path }}" class="btn btn-secondary">
                Open in Reader
            </a>
            <button hx-get="/import/form" hx-target="#import-container" class="btn btn-outline">
                Import Another
            </button>
        </div>
    </div>
    {% else %}
    <div class="alert alert-error">
        <h3>Import Failed</h3>
        <p>Error: {{ error }}</p>
        <button hx-get="/import/form" hx-target="#import-container" class="btn btn-primary">
            Try Again
        </button>
    </div>
    {% endif %}
</div>
```

### FastAPI HTMX Routes

```python
@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    """Render the import page"""
    return templates.TemplateResponse(
        "import/page.html", 
        {"request": request}
    )

@app.get("/import/single-form", response_class=HTMLResponse)
async def single_import_form(request: Request):
    """Render the single import form"""
    return templates.TemplateResponse(
        "import/partials/single_form.html",
        {"request": request}
    )

@app.get("/import/batch-form", response_class=HTMLResponse)
async def batch_import_form(request: Request):
    """Render the batch import form"""
    return templates.TemplateResponse(
        "import/partials/batch_form.html",
        {"request": request}
    )
```

## 6. XML Utilities

### XML Parser

```python
class XMLParser:
    @staticmethod
    def extract_title(xml_content: str) -> Optional[str]:
        """Extract title from XML content"""
        # Use regex to find title tags
        title_match = re.search(r'<title[^>]*>(.*?)</title>', xml_content)
        if title_match:
            return title_match.group(1).strip()
        return None
    
    @staticmethod
    def detect_language(xml_content: str) -> str:
        """Detect language from XML content"""
        # Look for xml:lang attribute
        lang_match = re.search(r'xml:lang="([^"]+)"', xml_content)
        if lang_match:
            return lang_match.group(1)
        # Default to Greek
        return "grc"
    
    @staticmethod
    def extract_author(xml_content: str) -> Optional[str]:
        """Extract author name from XML content"""
        # Look for author tags
        author_match = re.search(r'<author[^>]*>(.*?)</author>', xml_content)
        if author_match:
            return author_match.group(1).strip()
        return None
    
    @staticmethod
    def create_metadata_xml(author_id: str, author_name: str) -> str:
        """Create author metadata XML"""
        return f"""<ti:textgroup xmlns:ti="http://chs.harvard.edu/xmlns/cts" urn="urn:cts:greekLit:{author_id}">
    <ti:groupname xml:lang="eng">{author_name}</ti:groupname>
</ti:textgroup>"""
    
    @staticmethod
    def create_work_metadata_xml(author_id: str, work_id: str, work_title: str, 
                              language: str, full_id: str) -> str:
        """Create work metadata XML"""
        return f"""<ti:work xmlns:ti="http://chs.harvard.edu/xmlns/cts" groupUrn="urn:cts:greekLit:{author_id}" xml:lang="{language}" urn="urn:cts:greekLit:{author_id}.{work_id}">
    <ti:title xml:lang="eng">{work_title}</ti:title>
    <ti:edition urn="urn:cts:greekLit:{full_id}" workUrn="urn:cts:greekLit:{author_id}.{work_id}" xml:lang="{language}">
        <ti:label xml:lang="eng">{work_title}</ti:label>
        <ti:description xml:lang="eng">Imported from Scaife/Perseus</ti:description>
    </ti:edition>
</ti:work>"""
```

## 7. Main FastAPI Application

```python
# main.py
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.api.v1 import authors, imports, search, works
from app.core.config import settings
from app.services.author_service import AuthorService
from app.services.import_service import ImportService

app = FastAPI(
    title="First1KGreek Browser API",
    description="API for browsing and importing ancient Greek texts",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(authors.router)
app.include_router(imports.router)
app.include_router(search.router)
app.include_router(works.router)

# Service dependencies
def get_author_service():
    return AuthorService(data_path=settings.AUTHOR_DATA_PATH)

def get_import_service(author_service: AuthorService = Depends(get_author_service)):
    return ImportService(author_service=author_service, data_dir=settings.DATA_DIR)

# Root route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# Import route
@app.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    return templates.TemplateResponse("import/page.html", {"request": request})

# Start application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

## Key Improvements Over Original System

### 1. Modern API Architecture

- **Clear Separation of Concerns**: 
  - API endpoints handle request/response
  - Services contain business logic
  - Data models define structured data
  - Templates handle UI presentation

- **Type Safety**:
  - Pydantic models provide validation and type checking
  - Clearly defined schemas for all operations

### 2. Enhanced Data Management

- **author_data.json as Canonical Record**:
  - Central source of truth for author information
  - Structured updates ensure consistency
  - Automatic synchronization during imports

- **Improved Error Handling**:
  - Comprehensive error paths
  - Detailed error messages
  - Transaction-like behavior (no partial imports)

### 3. Modern Frontend with HTMX

- **Dynamic UI without JavaScript**:
  - HTMX handles AJAX, CSS transitions, WebSockets
  - Server-rendered HTML for all UI updates

- **Progressive Enhancement**:
  - Works without JavaScript
  - Enhanced experience with JS enabled

- **Real-time Feedback**:
  - Loading indicators during import
  - Partial page updates
  - Error reporting without full page reloads

### 4. Performance Improvements

- **Asynchronous Processing**:
  - FastAPI's async support for concurrent operations
  - Async HTTP requests for fetching XML
  - Non-blocking file operations

- **Optimized XML Handling**:
  - Efficient XML parsing with regular expressions
  - Cached metadata extraction
  - Stream processing for large files

### 5. Maintainability Improvements

- **Modular Design**:
  - Each component has a single responsibility
  - Clear interfaces between components
  - Easy to extend or replace individual parts

- **Testability**:
  - Dependency injection throughout
  - Pure functions where possible
  - Mocked external dependencies

## Future Enhancements

1. **Validation Improvements**:
   - XML schema validation
   - CTS URN validation
   - Duplicate detection

2. **Import Monitoring**:
   - Progress tracking for batch imports
   - Email notifications for large imports
   - Import history and logs

3. **Advanced Data Management**:
   - Versioning of imported texts
   - Change tracking and auditing
   - Conflict resolution for competing imports

4. **Integration Extensions**:
   - Support for additional text repositories
   - Export functionality to other formats
   - API integrations with other classical text platforms
