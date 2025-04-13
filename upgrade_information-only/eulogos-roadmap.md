# Revised Eulogos Project Implementation Roadmap

## 1. Project Setup and Dependencies
```toml
# Python dependencies - pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "eulogos"
version = "0.1.0"
description = "Browser for First1KGreek Project"
requires-python = ">=3.9"
dependencies = [
    "fastapi>=0.68.0",
    "uvicorn>=0.15.0",
    "pydantic>=1.9.0",
    "jinja2>=3.0.0",
    "lxml>=4.6.0",
    "httpx>=0.21.0",
    "loguru>=0.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "pydocstyle>=6.0.0",
    "pre-commit>=2.20.0",
    "mypy>=1.0.0",
]
```

## 2. Project Structure
```
eulogos/
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
│   ├── config.py             # Configuration management
│   └── main.py               # FastAPI application entry point
├── static/                   # Static assets
│   ├── css/                  # Tailwind and custom CSS
│   ├── js/                   # Alpine.js and custom scripts
│   └── img/                  # Images and icons
├── templates/                # Jinja2 templates
├── tests/                    # Test suite
├── data/                     # Data directory (existing)
├── .pre-commit-config.yaml   # Pre-commit hooks configuration
├── .flake8                   # Flake8 configuration
├── pyproject.toml            # Project metadata and dependencies
├── Dockerfile                # Container definition
└── docker-compose.yml        # Development environment setup
```

## 3. Development Standards Configuration
### 3.1 Black Configuration (pyproject.toml)
```toml
[tool.black]
line-length = 88
target-version = ["py39"]
include = '\.pyi?$'
```

### 3.2 Flake8 Configuration (.flake8)
```ini
[flake8]
max-line-length = 88
extend-ignore = E203
per-file-ignores = __init__.py:F401
exclude = .git,__pycache__,build,dist
```

### 3.3 Pydocstyle Configuration (pyproject.toml)
```toml
[tool.pydocstyle]
convention = "google"
add-select = ["D100", "D101", "D102", "D103"]
```

### 3.4 Pre-commit Configuration (.pre-commit-config.yaml)
```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8

-   repo: https://github.com/pycqa/pydocstyle
    rev: 6.3.0
    hooks:
    -   id: pydocstyle
```

## 4. Revised Implementation Phases

### 4.1 Phase 1: Core Text Browser (Initial MVP)
- Set up project structure and environment
- Implement Pydantic models for Author, Work, and Edition
- Create CatalogService for accessing authors.json and existing file structure
- Implement XMLProcessorService for parsing TEI XML files
- Create API endpoints for browsing authors and viewing texts
- Develop basic UI templates with HTMX and Tailwind
- Implement text reader with basic navigation
- Add basic import functionality for new texts

### 4.2 Phase 2: Enhanced Features and Text Management
- Implement sorting, filtering, and basic text search capabilities
- Create improved text reader with customization options
- Add user preferences with client-side storage
- Enhance import functionality with metadata extraction
- Implement basic text editing and correction capabilities
- Add export functionality in multiple formats
- Improve UI with responsive design and accessibility

### 4.3 Phase 3: Relational Database Integration
- Design comprehensive PostgreSQL schema optimized for text retrieval and relationships
- Create SQLAlchemy ORM models with appropriate relationships and indexes
- Implement migration utilities to transfer from file-based to database storage
- Add database versioning and migration tools (Alembic)
- Refactor services to use database repositories
- Optimize database queries for performance
- Implement proper transaction handling and error recovery

### 4.4 Phase 4: Vector Embeddings Implementation
- Research and select appropriate embedding models for ancient Greek texts
- Implement text chunking strategy for optimal embedding generation
- Create embedding generation pipeline with proper caching
- Integrate vector database (e.g., FAISS, Qdrant, or Pinecone)
- Implement similarity search API endpoints
- Create UI components for exploring similar texts
- Add embedding visualization tools
- Build incremental embedding update mechanism

### 4.5 Phase 5: BERT Semantic Mapping
- Integrate or fine-tune BERT model variants for ancient Greek
- Implement semantic search functionality
- Create named entity recognition for people, places, and concepts
- Add semantic relationship visualization
- Implement cross-reference identification
- Create topic modeling and clustering capabilities
- Build semantic navigation interface
- Add contextual recommendations based on semantic similarity

## 5. Testing Strategy
```python
# Example test structure for catalog service
def test_get_all_authors():
    """Test retrieving all authors from catalog."""
    service = CatalogService()
    authors = service.get_all_authors()
    assert len(authors) > 0
    assert all(isinstance(author, Author) for author in authors)
```

```python
# Example API test
async def test_get_authors_endpoint():
    """Test GET /api/authors endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/authors")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "name" in data[0]
```

### 5.3 Test Configuration (pyproject.toml)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "--cov=app --cov-report=term --cov-report=html"
```

## 6. Logging Configuration
```python
# app/utils/logging.py
from loguru import logger
import sys
import os

def configure_logging():
    """Configure application logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    # Add file handler for non-development environments
    if os.getenv("ENVIRONMENT", "development") != "development":
        logger.add(
            "logs/eulogos.log",
            rotation="10 MB",
            retention="1 week",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        )
    
    return logger
```

## 7. Docker Configuration
### 7.1 Dockerfile
```dockerfile
# Build stage
FROM python:3.9-slim as builder

WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -e .

# Runtime stage
FROM python:3.9-slim

WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /app/wheels /app/wheels

# Install dependencies
RUN pip install --no-cache-dir /app/wheels/*

# Copy application code
COPY app/ /app/app/
COPY static/ /app/static/
COPY templates/ /app/templates/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 docker-compose.yml
```yaml
version: '3'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
      - ./static:/app/static
      - ./templates:/app/templates
      - ./data:/app/data
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 8. CI/CD Configuration (.github/workflows/ci.yml)
```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
        
    - name: Lint with flake8
      run: flake8 .
        
    - name: Check formatting with black
      run: black --check .
      
    - name: Run tests
      run: pytest
      
    - name: Upload coverage report
      uses: codecov/codecov-action@v3
```

## 9. Notes on Technical Challenges

### 9.1 Scholarly Reference Handling
Since scholarly references cannot be automatically extracted due to inconsistent application by various transcribers and editors, consider:

- Creating a standardized reference annotation interface in Phase 2
- Implementing a semi-automated reference detection system with manual verification
- Building a growing database of reference patterns to improve detection over time
- Adding collaborative editing features for community-sourced reference standardization

### 9.2 Vector Embedding Considerations
- Ancient Greek presents unique challenges for embeddings due to language structure
- Consider specialized preprocessing for Greek texts before embedding generation
- Evaluate multilingual models vs. custom-trained embeddings for ancient Greek
- Test performance with different chunking strategies (paragraph, sentence, semantic unit)
- Consider models with better support for inflected languages

### 9.3 Database Optimization
- Consider hybrid storage approach with PostgreSQL for structured data and specialized storage for vectors
- Implement appropriate indexing strategies for text search
- Plan for proper handling of text variants and editions
- Design schema to support future semantic relationships
- Ensure efficient querying for hierarchical text structures

## 10. Revised Next Steps and Priorities
1. Set up project structure and development environment
2. Implement core data models and catalog service
3. Create basic API endpoints for browsing authors and works
4. Develop simple UI with HTMX and Tailwind
5. Implement XML processing service with basic rendering
6. Add text reader with navigation controls
7. Implement basic search functionality
8. Create data editing interface
9. Plan and implement database migration
10. Research and prototype vector embeddings approach
