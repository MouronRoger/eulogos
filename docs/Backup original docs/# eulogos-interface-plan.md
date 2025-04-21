# Plan for Eulogos Interface

The existing documentation reveals a more sophisticated UI than initially proposed, using Tailwind CSS, Alpine.js, and HTMX. This plan incorporates these technologies while maintaining the core principles.

## 1. Revised Project Structure

```
eulogos/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Application configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── catalog.py          # Data models for catalog
│   ├── services/
│   │   ├── __init__.py
│   │   ├── catalog_service.py  # Catalog loading and management
│   │   └── xml_service.py      # XML processing service
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── browse.py           # Routes for browsing
│   │   └── read.py             # Routes for reading texts
│   ├── templates/
│   │   ├── base.html           # Base template with navigation
│   │   ├── browse.html         # Text browsing interface
│   │   ├── reader.html         # Text reading interface
│   │   ├── errors/             # Error templates
│   │   │   ├── 404.html
│   │   │   └── 500.html
│   │   └── partials/           # HTMX partial templates
│   │       ├── references.html
│   │       └── search_results.html
│   └── static/
│       ├── css/
│       │   └── main.css        # Custom styles beyond Tailwind
│       ├── js/
│       │   └── main.js         # Custom JavaScript
│       └── fonts/              # Greek fonts if needed
├── data/                       # Existing data directory (unchanged)
├── canonical_catalog_builder.py # Existing catalog generator
├── integrated_catalog.json     # Source of truth for text metadata
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## 2. Key Components

### 2.1. Models (app/models/catalog.py)
* Pydantic models that represent texts, authors, and catalog structure
* File paths serve as canonical identifiers for texts
* Models include user-specific features like favorites

### 2.2. Services
* Catalog Service (app/services/catalog_service.py)
  * Loads and parses integrated_catalog.json
  * Provides methods to filter, search, and manipulate the catalog
  * Handles user-specific actions like favorites
* XML Service (app/services/xml_service.py)
  * Loads and parses XML files from the data directory
  * Renders XML content to HTML with appropriate styling
  * Extracts references and metadata from XML

### 2.3. Web Interface
* Modern UI using Tailwind CSS
* Interactive elements with Alpine.js
* Dynamic content loading with HTMX
* Responsive design for all devices

## 3. Implementation Sequence

### 3.1. Set up project structure and dependencies
* Create directory structure
* Install required packages
* Configure FastAPI application

### 3.2. Implement catalog models and service
* Create data models for texts and catalog
* Implement catalog loading and manipulation service
* Implement text filtering and search

### 3.3. Implement XML processing service
* Create XML loading and parsing functions
* Implement HTML rendering with TEI-specific styling
* Extract references for navigation

### 3.4. Create API routes
* Implement browse routes
* Implement reader routes
* Implement search and favorite functionality

### 3.5. Develop web interface
* Implement base template with navigation
* Create browse interface with filtering
* Create reader interface with navigation
* Implement partial templates for HTMX

### 3.6. Add advanced features
* Text search functionality
* Reference navigation
* Reading preferences (dark mode, font size)
* Favorites system

## 4. Key Features

### 4.1. Browse Interface
* List texts with filtering by author, language
* Support for favoriting texts
* Search functionality
* Responsive grid layout

### 4.2. Reading Interface
* Clean, readable presentation of texts
* Text navigation by references/sections
* Reading preferences (dark mode, font size, line spacing)
* Special handling for Greek text with appropriate fonts

### 4.3. Technical Features
* HTMX for dynamic content loading
  * Partial page updates for search and reference navigation
  * No need for custom JavaScript for most interactive elements
* Alpine.js for UI state management
  * Reader preferences
  * Collapsible sections
  * Toggle functionality
* Tailwind CSS for styling
  * Consistent design system
  * Responsive layout
  * Dark mode support

## 5. Specific Implementation Details

### 5.1. Catalog Model

```python
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Text(BaseModel):
    """Model for a text entry in the catalog."""
    
    path: str = Field(..., description="Relative path to the XML file (canonical ID)")
    title: str = Field(..., description="Title of the text")
    author: str = Field(..., description="Author of the text")
    language: str = Field(default="unknown", description="Language of the text")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")
    favorite: bool = Field(default=False, description="Whether the text is favorited")
    archived: bool = Field(default=False, description="Whether the text is archived")

class Catalog(BaseModel):
    """Main catalog model containing all texts."""
    
    texts: List[Text] = Field(default_factory=list, description="List of all texts")
    
    def get_text_by_path(self, path: str) -> Optional[Text]:
        """Get a text by its path."""
        for text in self.texts:
            if text.path == path:
                return text
        return None
        
    def toggle_favorite(self, path: str) -> bool:
        """Toggle the favorite status of a text."""
        text = self.get_text_by_path(path)
        if text:
            text.favorite = not text.favorite
            return True
        return False
```

### 5.2. Catalog Builder Integration
We should adapt the existing canonical_catalog_builder.py to output a catalog compatible with our new model. This means:
1. Preserving the existing data structure but transforming it to our flat list of texts
2. Using file paths as canonical identifiers
3. Adding user preference fields (favorites, archived)

### 5.3. Main FastAPI Application

```python
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional

from app.services.catalog_service import CatalogService, get_catalog_service
from app.services.xml_service import XMLService
from app.config import Settings, get_settings

# Initialize FastAPI
app = FastAPI(title="Eulogos", description="Ancient Text Browser")

# Settings
settings = get_settings()

# Setup static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Service dependencies
def get_xml_service() -> XMLService:
    """Get XML service dependency."""
    return XMLService(data_dir=settings.data_dir)

@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Render home page (redirects to browse)."""
    return templates.TemplateResponse(
        "browse.html", 
        {
            "request": request,
            "texts": catalog_service.get_all_texts(),
            "authors": catalog_service.get_all_authors(),
            "languages": catalog_service.get_all_languages(),
        }
    )
```

## 6. Implementation Timeline

### 6.1. Week 1: Setup and Core Models
* Project setup and dependency installation
* Implement catalog models and service
* Initial FastAPI application setup

### 6.2. Week 2: XML Processing and Core Routes
* Implement XML service
* Create browse and read routes
* Basic template implementation

### 6.3. Week 3: User Interface and Features
* Implement full UI with Tailwind CSS
* Add Alpine.js interactive components
* Implement HTMX dynamic loading

### 6.4. Week 4: Testing and Refinement
* Test with various text types
* Optimize performance
* Add final polish and documentation

This updated plan leverages the advanced UI patterns shown in the templates while maintaining a clean architecture focused around the canonical catalog and data structure.
