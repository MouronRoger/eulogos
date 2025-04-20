# Eulogos Project Rebuild Plan

## Core Philosophy

This rebuild will strictly follow these principles:
- File paths are the canonical text IDs
- Direct filesystem access for XML processing
- No URN processing or complex abstraction layers
- Minimal, focused codebase
- Single source of truth (integrated_catalog.json)

## Phase 1: Foundation & Core Processing

### 1. Project Structure Setup

```
eulogos/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration settings
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   └── catalog.py             # Simple catalog models
│   ├── services/                  # Core services
│   │   ├── __init__.py
│   │   ├── catalog_service.py     # Catalog loading & lookup
│   │   └── xml_service.py         # XML processing
│   ├── routers/                   # API routes
│   │   ├── __init__.py
│   │   ├── browse.py              # Browse texts
│   │   └── reader.py              # Read texts
│   ├── templates/                 # Jinja2 templates
│   │   ├── base.html              # Base template
│   │   ├── browse.html            # Browse page
│   │   └── reader.html            # Reader page
│   └── static/                    # Static assets
├── data/                          # Text data (XML files)
├── scripts/                       # Utility scripts
│   └── catalog_builder.py         # Catalog generation tool
├── requirements.txt               # Dependencies
└── README.md                      # Documentation
```

### 2. Core Models Implementation

Create simple, direct models in `app/models/catalog.py`:

```python
from typing import Dict, List, Optional
from pydantic import BaseModel

class Text(BaseModel):
    """Simple text model with path as ID."""
    path: str  # This is both the ID and filesystem path
    title: str
    author: str
    language: str
    metadata: Dict = {}
    
class Catalog(BaseModel):
    """Simple catalog model."""
    texts: List[Text] = []
```

### 3. Catalog Builder Script

Create a script in `scripts/catalog_builder.py` that:
- Scans the data directory for XML files
- Extracts basic metadata from each file
- Generates a catalog using file paths as IDs
- Outputs to integrated_catalog.json

### 4. Catalog Service

Create a minimal `CatalogService` in `app/services/catalog_service.py`:

```python
import json
from typing import Dict, List, Optional
from pathlib import Path

from app.models.catalog import Text, Catalog

class CatalogService:
    """Service for accessing the catalog."""
    
    def __init__(self, catalog_path: str = "integrated_catalog.json"):
        """Initialize with catalog path."""
        self.catalog_path = Path(catalog_path)
        self._catalog: Optional[Catalog] = None
        self._texts_by_path: Dict[str, Text] = {}
        
        # Load catalog on initialization
        self.load_catalog()
        
    def load_catalog(self) -> Catalog:
        """Load the catalog from file."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog file not found: {self.catalog_path}")
            
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._catalog = Catalog.parse_obj(data)
            
        # Build lookup index
        self._texts_by_path = {text.path: text for text in self._catalog.texts}
        
        return self._catalog
    
    def get_all_texts(self) -> List[Text]:
        """Get all texts in the catalog."""
        if not self._catalog:
            self.load_catalog()
        return self._catalog.texts
    
    def get_text_by_path(self, path: str) -> Optional[Text]:
        """Get a text by its path."""
        return self._texts_by_path.get(path)
```

### 5. XML Service

Create a direct XML processor in `app/services/xml_service.py`:

```python
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any

class XMLService:
    """Service for processing XML files."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize with data directory path."""
        self.data_dir = Path(data_dir)
        
    def load_xml(self, path: str) -> Optional[ET.Element]:
        """Load XML file directly from path."""
        file_path = self.data_dir / path
        
        if not file_path.exists():
            return None
            
        try:
            tree = ET.parse(file_path)
            return tree.getroot()
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return None
    
    def extract_text(self, element: ET.Element) -> str:
        """Extract text content from XML element."""
        return "".join(element.itertext())
        
    def transform_to_html(self, element: ET.Element) -> str:
        """Transform XML to simple HTML."""
        # Simple implementation - enhance as needed
        html = []
        
        def process_element(el, depth=0):
            """Process element recursively."""
            tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            
            # Handle text nodes
            if el.text and el.text.strip():
                html.append(f"<p>{el.text}</p>")
                
            # Process children
            for child in el:
                process_element(child, depth + 1)
                
                # Handle tail text
                if child.tail and child.tail.strip():
                    html.append(f"<p>{child.tail}</p>")
        
        # Process the root element
        process_element(element)
        
        return "".join(html)
```

## Phase 2: API & Web Interface

### 6. FastAPI Application Setup

Create the main application in `app/main.py`:

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.services.catalog_service import CatalogService
from app.services.xml_service import XMLService
from app.routers import browse, reader

# Initialize FastAPI
app = FastAPI(title="Eulogos", description="Ancient Greek Text Repository")

# Setup static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(browse.router)
app.include_router(reader.router)

# Initialize services
catalog_service = CatalogService()
xml_service = XMLService()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to browse page."""
    return templates.TemplateResponse("browse.html", {"request": request})

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
```

### 7. Browse Router

Create a simple browse router in `app/routers/browse.py`:

```python
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/browse", tags=["browse"])
templates = Jinja2Templates(directory="app/templates")

def get_catalog_service():
    """Get catalog service instance."""
    return CatalogService()

@router.get("/", response_class=HTMLResponse)
async def browse_texts(
    request: Request,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Browse all texts."""
    texts = catalog_service.get_all_texts()
    return templates.TemplateResponse(
        "browse.html", 
        {"request": request, "texts": texts}
    )
```

### 8. Reader Router

Create a direct reader router in `app/routers/reader.py`:

```python
from fastapi import APIRouter, Request, Depends, HTTPException, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.catalog_service import CatalogService
from app.services.xml_service import XMLService

router = APIRouter(prefix="/read", tags=["reader"])
templates = Jinja2Templates(directory="app/templates")

def get_catalog_service():
    """Get catalog service instance."""
    return CatalogService()

def get_xml_service():
    """Get XML service instance."""
    return XMLService()

@router.get("/{path:path}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    path: str = Path(...),
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLService = Depends(get_xml_service)
):
    """Read a text by its path."""
    # Get text metadata from catalog
    text = catalog_service.get_text_by_path(path)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {path}")
    
    # Load XML content
    xml_root = xml_service.load_xml(path)
    if not xml_root:
        raise HTTPException(status_code=404, detail=f"Failed to load XML for: {path}")
    
    # Transform to HTML
    html_content = xml_service.transform_to_html(xml_root)
    
    # Render template
    return templates.TemplateResponse(
        "reader.html",
        {
            "request": request,
            "text": text,
            "content": html_content,
            "path": path
        }
    )
```

### 9. Basic Templates

Create minimal templates:

For `app/templates/base.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Eulogos{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script src="https://unpkg.com/htmx.org@1.9.4"></script>
    <script src="https://unpkg.com/alpinejs@3.13.0" defer></script>
    {% block head %}{% endblock %}
</head>
<body class="bg-gray-50">
    <header class="bg-blue-600 text-white p-4">
        <div class="container mx-auto">
            <h1 class="text-2xl font-bold">
                <a href="/" class="hover:text-blue-100">Eulogos</a>
            </h1>
        </div>
    </header>
    
    <main class="container mx-auto p-4">
        {% block content %}{% endblock %}
    </main>
    
    <footer class="bg-gray-100 p-4 mt-8">
        <div class="container mx-auto text-center text-gray-500">
            <p>Eulogos - Ancient Greek Text Repository</p>
        </div>
    </footer>
</body>
</html>
```

For `app/templates/browse.html`:
```html
{% extends "base.html" %}

{% block title %}Browse Texts - Eulogos{% endblock %}

{% block content %}
<h1 class="text-2xl font-bold mb-4">Browse Texts</h1>

<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    {% for text in texts %}
    <div class="bg-white p-4 rounded shadow">
        <h2 class="text-lg font-semibold">{{ text.title }}</h2>
        <p class="text-gray-600">{{ text.author }}</p>
        <p class="text-sm text-gray-500">Language: {{ text.language }}</p>
        <div class="mt-2">
            <a href="/read/{{ text.path }}" class="text-blue-600 hover:underline">Read</a>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

For `app/templates/reader.html`:
```html
{% extends "base.html" %}

{% block title %}{{ text.title }} - Eulogos{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-4">
    <h1 class="text-2xl font-bold">{{ text.title }}</h1>
    <a href="/browse" class="bg-blue-600 text-white px-4 py-2 rounded">Back to Browse</a>
</div>

<div class="bg-white p-6 rounded shadow">
    <div class="mb-4 text-gray-600">
        <p>Author: {{ text.author }}</p>
        <p>Language: {{ text.language }}</p>
        <p>Path: {{ path }}</p>
    </div>
    
    <div class="prose max-w-none">
        {{ content|safe }}
    </div>
</div>
{% endblock %}
```

## Phase 3: Enhanced XML Processing

### 10. Improved XML Processing

Enhance the XML service with better processing:

```python
def transform_to_html(self, element: ET.Element) -> str:
    """Transform XML to structured HTML with proper formatting."""
    html = []
    
    def process_element(el, parent_tag=None):
        """Process element recursively with context."""
        if el is None:
            return
            
        # Get clean tag name
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        attributes = el.attrib
        
        # Process based on tag type
        if tag in ["div", "body", "text"]:
            # Container elements
            html.append(f'<div class="{tag}">')
            
            # Handle text content
            if el.text and el.text.strip():
                html.append(f'<span class="text">{el.text}</span>')
                
            # Process children
            for child in el:
                process_element(child, tag)
                
                # Handle tail text
                if child.tail and child.tail.strip():
                    html.append(f'<span class="text">{child.tail}</span>')
                    
            html.append('</div>')
            
        elif tag in ["p", "l"]:
            # Paragraph elements
            html.append(f'<p class="{tag}">')
            
            if el.text and el.text.strip():
                html.append(el.text)
                
            # Process children
            for child in el:
                process_element(child, tag)
                
                # Handle tail text
                if child.tail and child.tail.strip():
                    html.append(child.tail)
                    
            html.append('</p>')
            
        elif tag in ["head", "title"]:
            # Heading elements
            html.append(f'<h3 class="{tag}">')
            
            if el.text and el.text.strip():
                html.append(el.text)
                
            # Process children
            for child in el:
                process_element(child, tag)
                
                # Handle tail text
                if child.tail and child.tail.strip():
                    html.append(child.tail)
                    
            html.append('</h3>')
            
        else:
            # Generic inline elements
            html.append(f'<span class="{tag}">')
            
            if el.text and el.text.strip():
                html.append(el.text)
                
            # Process children
            for child in el:
                process_element(child, tag)
                
                # Handle tail text
                if child.tail and child.tail.strip():
                    html.append(child.tail)
                    
            html.append('</span>')
    
    # Process the root element
    process_element(element)
    
    return "".join(html)
```

### 11. Reference Navigation Support

Add reference extraction and navigation to XML service:

```python
def extract_references(self, element: ET.Element) -> Dict[str, ET.Element]:
    """Extract references from XML."""
    references = {}
    
    def extract_recursive(el, parent_ref=""):
        # Get 'n' attribute if present
        n_value = el.get("n")
        if n_value:
            # Build reference
            ref = f"{parent_ref}.{n_value}" if parent_ref else n_value
            references[ref] = el
        else:
            ref = parent_ref
            
        # Process children
        for child in el:
            extract_recursive(child, ref)
    
    # Start extraction from root
    extract_recursive(element)
    
    return references

def get_passage_by_reference(self, element: ET.Element, reference: str) -> Optional[ET.Element]:
    """Get passage by reference."""
    if not reference:
        return None
        
    # Get all references
    references = self.extract_references(element)
    
    # Return the element for the reference
    return references.get(reference)

def get_adjacent_references(self, element: ET.Element, reference: str) -> Dict[str, Optional[str]]:
    """Get adjacent references for navigation."""
    # Get all references
    references = self.extract_references(element)
    
    # Sort references
    sorted_refs = sorted(references.keys())
    
    # Find current reference index
    try:
        current_idx = sorted_refs.index(reference)
    except ValueError:
        return {"prev": None, "next": None}
    
    # Get previous and next
    prev_ref = sorted_refs[current_idx - 1] if current_idx > 0 else None
    next_ref = sorted_refs[current_idx + 1] if current_idx < len(sorted_refs) - 1 else None
    
    return {"prev": prev_ref, "next": next_ref}
```

### 12. Update Reader Router

Enhance the reader router with reference support:

```python
@router.get("/{path:path}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    path: str = Path(...),
    reference: Optional[str] = None,
    catalog_service: CatalogService = Depends(get_catalog_service),
    xml_service: XMLService = Depends(get_xml_service)
):
    """Read a text by its path with optional reference."""
    # Get text metadata from catalog
    text = catalog_service.get_text_by_path(path)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {path}")
    
    # Load XML content
    xml_root = xml_service.load_xml(path)
    if not xml_root:
        raise HTTPException(status_code=404, detail=f"Failed to load XML for: {path}")
    
    # If reference is provided, get specific section
    if reference:
        element = xml_service.get_passage_by_reference(xml_root, reference)
        if not element:
            raise HTTPException(status_code=404, detail=f"Reference not found: {reference}")
            
        html_content = xml_service.transform_to_html(element)
        
        # Get adjacent references for navigation
        adjacent_refs = xml_service.get_adjacent_references(xml_root, reference)
    else:
        # Transform full document to HTML
        html_content = xml_service.transform_to_html(xml_root)
        adjacent_refs = {"prev": None, "next": None}
    
    # Render template
    return templates.TemplateResponse(
        "reader.html",
        {
            "request": request,
            "text": text,
            "content": html_content,
            "path": path,
            "reference": reference,
            "prev_ref": adjacent_refs["prev"],
            "next_ref": adjacent_refs["next"]
        }
    )

@router.get("/{path:path}/references", response_class=HTMLResponse)
async def get_references(
    request: Request,
    path: str = Path(...),
    xml_service: XMLService = Depends(get_xml_service)
):
    """Get references for a text."""
    # Load XML content
    xml_root = xml_service.load_xml(path)
    if not xml_root:
        raise HTTPException(status_code=404, detail=f"Failed to load XML for: {path}")
    
    # Extract references
    references = xml_service.extract_references(xml_root)
    
    # Sort references
    sorted_refs = sorted(references.keys())
    
    # Return as HTMX fragment for inclusion
    return templates.TemplateResponse(
        "partials/references.html",
        {
            "request": request,
            "references": sorted_refs,
            "path": path
        }
    )
```

## Phase 4: User Interface Enhancements

### 13. Improved Reader Template

Add support for reference navigation to `reader.html`:

```html
{% extends "base.html" %}

{% block title %}{{ text.title }} - Eulogos{% endblock %}

{% block head %}
<style>
    /* TEI XML styles */
    .div, .body, .text {
        margin: 1rem 0;
    }
    .p {
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    .l {
        display: block;
        margin-left: 2rem;
        text-indent: -2rem;
    }
    .head, .title {
        font-weight: bold;
        font-size: 1.2rem;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .reference-browser {
        max-height: 300px;
        overflow-y: auto;
    }
</style>
{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-4">
    <h1 class="text-2xl font-bold">{{ text.title }}</h1>
    <a href="/browse" class="bg-blue-600 text-white px-4 py-2 rounded">Back to Browse</a>
</div>

<div class="bg-white p-6 rounded shadow">
    <div class="mb-4 text-gray-600">
        <p>Author: {{ text.author }}</p>
        <p>Language: {{ text.language }}</p>
        <p>Path: {{ path }}</p>
        {% if reference %}
        <p>Current reference: {{ reference }}</p>
        {% endif %}
    </div>
    
    <!-- Reference navigation -->
    {% if reference %}
    <div class="flex justify-between mb-4">
        {% if prev_ref %}
        <a href="/read/{{ path }}?reference={{ prev_ref }}" class="bg-blue-600 text-white px-3 py-1 rounded">Previous Section</a>
        {% else %}
        <span class="bg-gray-300 text-gray-600 px-3 py-1 rounded">Previous Section</span>
        {% endif %}
        
        <a href="/read/{{ path }}" class="bg-blue-600 text-white px-3 py-1 rounded">Full Text</a>
        
        {% if next_ref %}
        <a href="/read/{{ path }}?reference={{ next_ref }}" class="bg-blue-600 text-white px-3 py-1 rounded">Next Section</a>
        {% else %}
        <span class="bg-gray-300 text-gray-600 px-3 py-1 rounded">Next Section</span>
        {% endif %}
    </div>
    {% endif %}
    
    <!-- Reference browser -->
    <div x-data="{ open: false }" class="mb-4">
        <button @click="open = !open" class="bg-gray-200 text-gray-800 px-4 py-2 rounded mb-2 w-full text-left flex justify-between items-center">
            <span>Browse References</span>
            <svg :class="open ? 'transform rotate-180' : ''" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
        </button>
        
        <div x-show="open" class="reference-browser bg-gray-50 p-4 rounded" hx-get="/read/{{ path }}/references" hx-trigger="load" hx-swap="innerHTML">
            Loading references...
        </div>
    </div>
    
    <div class="prose max-w-none">
        {{ content|safe }}
    </div>
</div>
{% endblock %}
```

### 14. Reference Partial Template

Create `app/templates/partials/references.html`:

```html
<div class="space-y-1">
    {% for ref in references %}
    <div>
        <a href="/read/{{ path }}?reference={{ ref }}" class="text-blue-600 hover:underline">{{ ref }}</a>
    </div>
    {% endfor %}
</div>
```

## Phase 5: Deployment & Refinement

### 15. Configuration

Create `app/config.py` for centralized configuration:

```python
from functools import lru_cache
from pathlib import Path
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    # Paths
    data_dir: Path = Path("data")
    catalog_path: Path = Path("integrated_catalog.json")
    
    # Application settings
    app_name: str = "Eulogos"
    debug: bool = False
    
    # Optional features
    enable_caching: bool = True
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    """Get cached settings."""
    return Settings()
```

### 16. Dependencies

Update `requirements.txt`:

```
fastapi>=0.95.0
uvicorn>=0.21.1
jinja2>=3.1.2
python-multipart>=0.0.6
pydantic>=1.10.7
aiofiles>=23.1.0
```

### 17. Final Application Startup

Create `run.py` in project root:

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

## Implementation Strategy

1. **Initial Cleanup**:
   - Delete all current code related to URN processing and XML handling
   - Keep only the data directory and README intact

2. **Staged Implementation**:
   - Implement Phase 1 (Foundation) fully before proceeding
   - Test basic functionality after each phase
   - Validate XML processing with actual texts from data directory

3. **Catalog Generation**:
   - Build and maintain the catalog structure early
   - Use the catalog for all path lookups consistently

4. **Testing Strategy**:
   - Test XML parsing with progressively complex documents
   - Ensure path-based lookups work correctly
   - Validate reference navigation functionality

## Advantages of This Approach

1. **Simplicity**: Direct path to XML approach eliminates abstraction layers
2. **Maintainability**: Small, focused codebase with clear responsibilities
3. **Performance**: Direct file access without complex lookups or processing
4. **Clarity**: Clear data flow from catalog to display
5. **Consistency**: Single method for text identification and lookup

This plan establishes a clean foundation that can be progressively enhanced with additional features (search, export, favorites) while maintaining the core principle of file path as canonical identifier.
