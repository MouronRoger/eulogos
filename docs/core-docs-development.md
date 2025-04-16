# Eulogos Developer Documentation

## 1. Development Environment Setup

### 1.1 Prerequisites

- Python 3.9+
- Git
- Docker (optional, for containerized development)
- Node.js (optional, for frontend tooling)

### 1.2 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/eulogos.git
   cd eulogos
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

5. Setup environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### 1.3 Starting the Development Server

1. Launch the development server:
   ```bash
   python run.py
   ```

2. Access the application at `http://localhost:8000`

## 2. Project Structure

```
app/
├── api/                # API endpoints
│   ├── v1/             # API version 1
├── core/               # Core functionality
├── db/                 # Database models and functions (future)
├── models/             # Pydantic models
├── services/           # Business logic services
├── templates/          # HTMX templates
├── static/             # Static files
├── utils/              # Utility functions
└── main.py             # FastAPI application entry point

data/                   # TEI XML files organized by author/work

docs/                   # Documentation

tests/                  # Test suite
```

## 3. Code Style and Conventions

### 3.1 Python Style Guidelines

- Follow PEP 8 with the following modifications:
  - Line length: 120 characters
  - Use Black for formatting
- Use Google-style docstrings
- Use type hints for all function parameters and return values
- Use f-strings for string formatting

### 3.2 Naming Conventions

- **Files**: snake_case (e.g., `catalog_service.py`)
- **Classes**: PascalCase (e.g., `CatalogService`)
- **Functions/Methods**: snake_case (e.g., `get_text_by_urn`)
- **Variables**: snake_case (e.g., `author_list`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_PAGE_SIZE`)

### 3.3 Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports
4. Use absolute imports in the codebase

Example:
```python
import os
import json
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.catalog import Author, Text
from app.services.catalog_service import CatalogService
```

## 4. Testing

### 4.1 Test Structure

- Tests are organized in the `tests/` directory mirroring the application structure
- Use pytest for running tests
- Name test files with `test_` prefix (e.g., `test_catalog_service.py`)
- Name test functions with `test_` prefix (e.g., `test_get_text_by_urn`)

### 4.2 Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app tests/
```

Run specific test file:
```bash
pytest tests/test_catalog_service.py
```

### 4.3 Test Guidelines

- Write unit tests for all services and utility functions
- Use fixtures for test setup
- Mock external dependencies
- Aim for at least 85% test coverage
- Test both happy paths and error cases
- Use parameterized tests for similar test cases

### 4.4 Example Test

```python
import pytest
from app.models.urn import URN

def test_urn_parsing():
    # Given
    urn_string = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10"

    # When
    urn = URN(value=urn_string)

    # Then
    assert urn.namespace == "greekLit"
    assert urn.text_group == "tlg0012"
    assert urn.work == "tlg001"
    assert urn.version == "perseus-grc2"
    assert urn.reference == "1.1-1.10"
```

## 5. Working with CTS URNs

### 5.1 URN Format

CTS URNs (Canonical Text Services Uniform Resource Names) are structured as:

```
urn:cts:NAMESPACE:TEXTGROUP.WORK.VERSION:REFERENCE
```

Example:
```
urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10
```

- `urn:cts`: Protocol
- `greekLit`: Namespace
- `tlg0012`: Text group (author)
- `tlg001`: Work
- `perseus-grc2`: Version
- `1.1-1.10`: Reference (optional)

### 5.2 Using the URN Model

```python
from app.models.urn import URN

# Parse URN
urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10")

# Access components
namespace = urn.namespace  # "greekLit"
text_group = urn.text_group  # "tlg0012"
work = urn.work  # "tlg001"
version = urn.version  # "perseus-grc2"
reference = urn.reference  # "1.1-1.10"

# Create file path
file_path = urn.get_file_path("data")  # "data/greekLit/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml"

# Create new URN with different reference
new_urn = urn.replace(reference="1.2")
```

## 6. Working with XML Processing

### 6.1 Loading XML

```python
from app.services.xml_processor_service import XMLProcessorService
from app.models.urn import URN

# Initialize service
xml_service = XMLProcessorService(data_path="data")

# Load XML using URN
urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
xml_root = xml_service.load_xml(urn)
```

### 6.2 Working with References

```python
# Extract all references from the document
references = xml_service.extract_references(xml_root)

# Get a specific passage by reference
passage = xml_service.get_passage_by_reference(xml_root, "1.1")

# Get adjacent references
adjacent = xml_service.get_adjacent_references(xml_root, "1.1")
prev_ref = adjacent["prev"]  # Previous reference or None
next_ref = adjacent["next"]  # Next reference or None

# Transform to HTML with reference highlighting
html = xml_service.transform_to_html(xml_root, target_ref="1.1")
```

### 6.3 Token Processing

```python
# Process text into tokens
text = "Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος"
tokens = xml_service.tokenize_text(text)

# Result example:
# [
#   {"type": "word", "text": "Μῆνιν", "index": 1},
#   {"type": "word", "text": "ἄειδε", "index": 2},
#   {"type": "word", "text": "θεὰ", "index": 3},
#   {"type": "word", "text": "Πηληϊάδεω", "index": 4},
#   {"type": "word", "text": "Ἀχιλῆος", "index": 5}
# ]
```

## 7. Working with the Catalog

### 7.1 Accessing Catalog Data

```python
from app.services.catalog_service import CatalogService

# Initialize service
catalog_service = CatalogService(catalog_path="data/unified-catalog.json")

# Get all authors
authors = catalog_service.get_all_authors()

# Get author by ID
author = catalog_service.get_author("tlg0012")

# Get texts by author
texts = catalog_service.get_texts_by_author("tlg0012")

# Get text by URN
text = catalog_service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

# Search texts
results = catalog_service.search_texts("Iliad")
```

### 7.2 Managing Texts

```python
# Archive/unarchive a text
catalog_service.archive_text("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2", archive=True)

# Toggle favorite status
catalog_service.toggle_text_favorite("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

# Delete a text
catalog_service.delete_text("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
```

## 8. Working with the Export Service

### 8.1 Basic Export

```python
from app.services.export_service import ExportService
from app.models.urn import URN

# Initialize services
export_service = ExportService(xml_processor, catalog_service)

# Export to PDF
urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
pdf_bytes = export_service.export_to_pdf(urn)

# Write to file
with open("output.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### 8.2 Export with Options

```python
# Export to PDF with options
pdf_options = {
    "font_size": 14,
    "page_size": "A4",
    "margins": 20,
    "include_toc": True,
    "include_line_numbers": True
}
pdf_bytes = export_service.export_to_pdf(urn, pdf_options)

# Export to ePub
epub_options = {
    "include_cover": True,
    "include_toc": True,
    "font": "New Athena Unicode"
}
epub_bytes = export_service.export_to_epub(urn, epub_options)
```

## 9. API Development

### 9.1 API Structure

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/v1/texts", tags=["texts"])

@router.get("/{urn}")
async def get_text(
    urn: str,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Get text by URN."""
    text = catalog_service.get_text_by_urn(urn)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text

@router.post("/{urn}/archive")
async def archive_text(
    urn: str,
    archive: bool = True,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Archive or unarchive a text."""
    success = catalog_service.archive_text(urn, archive)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"status": "success", "archived": archive}
```

### 9.2 API Documentation

All API endpoints should be documented with clear docstrings and type hints to enable automatic Swagger documentation.

Example:
```python
@router.get("/{urn}")
async def get_text(
    urn: str,
    catalog_service: CatalogService = Depends(get_catalog_service)
) -> Text:
    """
    Get text details by URN.

    Parameters:
    - **urn**: URN of the text to retrieve

    Returns:
    - Text object with all metadata

    Raises:
    - 404: Text not found
    """
    # Implementation...
```

## 10. HTMX and Alpine.js Integration

### 10.1 HTMX Basics

HTMX is used for dynamic content loading without much JavaScript:

```html
<!-- Button that loads content -->
<button
  hx-get="/api/browse?show=favorites"
  hx-target="#author-list"
>
  Show Favorites
</button>

<!-- Target element -->
<div id="author-list">
  <!-- Content will be loaded here -->
</div>
```

### 10.2 Alpine.js for Interactivity

Alpine.js is used for client-side interactivity:

```html
<!-- Dropdown with Alpine.js -->
<div x-data="{ open: false }">
  <button @click="open = !open">Options</button>

  <div x-show="open" @click.away="open = false">
    <!-- Dropdown content -->
    <a href="#">Option 1</a>
    <a href="#">Option 2</a>
  </div>
</div>
```

### 10.3 Combining HTMX and Alpine.js

```html
<div
  x-data="{ expanded: false }"
  hx-get="/api/author/works"
  hx-trigger="expanded"
  hx-target="#works-list"
>
  <button @click="expanded = !expanded">
    Show Works
  </button>

  <div id="works-list" x-show="expanded">
    <!-- Works will be loaded here -->
  </div>
</div>
```

## 11. Deployment Process

### 11.1 Flexible Deployment Workflow

The project uses a flexible deployment and rollback workflow that supports:

1. Deploying from any branch to staging or production
2. Tracking all deployments with detailed metadata
3. Verifying deployment success with automated tests
4. Rolling back to any previous successful deployment

### 11.2 Deployment Script

```bash
# Example deployment command
python .github/scripts/deploy.py --branch main --environment production
```

### 11.3 Rollback Process

```bash
# Rollback to a specific deployment
python .github/scripts/deploy.py --rollback --deployment-id branch_1_abc1234_20250415123456 --environment production

# Rollback to latest successful deployment
python .github/scripts/deploy.py --rollback --environment production
```

### 11.4 Deployment Verification

Deployments are automatically verified with a comprehensive verification script that checks:

- Health endpoint response
- Key API functionality
- Response times
- Content validation
- XML processing functionality

## 12. Helpful Resources

### 12.1 Libraries Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [HTMX Documentation](https://htmx.org/docs/)
- [Alpine.js Documentation](https://alpinejs.dev/start-here)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

### 12.2 CTS and TEI Resources

- [CTS URN Specification](http://www.homermultitext.org/hmt-docs/cite/cts-urn-overview.html)
- [TEI Guidelines](https://tei-c.org/guidelines/)
- [Perseus Digital Library](http://www.perseus.tufts.edu/)
- [Capitains Guidelines](https://capitains.org/pages/guidelines)

### 12.3 Export Libraries

- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/stable/)
- [EbookLib Documentation](https://docs.sourcefabric.org/projects/ebooklib/)
- [python-docx Documentation](https://python-docx.readthedocs.io/)

### 12.4 Greek Typography Resources

- [SBL Greek Font](https://www.sbl-site.org/educational/BiblicalFonts_SBLGreek.aspx)
- [New Athena Unicode](https://apagreekkeys.org/NAUdownload.html)
- [Gentium](https://software.sil.org/gentium/)
