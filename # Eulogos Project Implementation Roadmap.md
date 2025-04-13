# # Eulogos Project Implementation Roadmap
## 1. Project Setup and Dependencies


bash




Apply to mcp.json
Run


































































*# Python dependencies - pyproject.toml*
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "eulogos"
version = "0.1.0"
description = "Browser for First1KGreek Project"
requires-python = ">=3.9"
dependencies = [
    "fastapi>=0.68.0",
    "uvicorn>=0.15.0",
    "pydantic>=1.9.0",
    "jinja2>=3.0.0",
    "lxml>=4.6.0",
    "httpx>=0.21.0",
    "loguru>=0.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "pydocstyle>=6.0.0",
    "pre-commit>=2.20.0",
    "mypy>=1.0.0",
]





## 2. Project Structure


text




Apply to mcp.json










































































eulogos/
├── app/                      # Main application package
│   ├── api/                  # FastAPI routers
│   │   ├── authors.py
│   │   ├── works.py
│   │   ├── content.py
│   │   ├── search.py
│   │   └── import.py
│   ├── models/               # Pydantic models
│   │   ├── author.py
│   │   ├── work.py
│   │   └── preferences.py
│   ├── services/             # Business logic
│   │   ├── catalog.py        # Author/work catalog management
│   │   ├── xml_processor.py  # XML parsing and transformation
│   │   ├── search.py         # Text search implementation
│   │   └── importer.py       # Import functionality
│   ├── utils/                # Utility functions
│   │   ├── paths.py          # Path handling utilities
│   │   └── xml.py            # XML helper functions
│   ├── config.py             # Configuration management
│   └── main.py               # FastAPI application entry point
├── static/                   # Static assets
│   ├── css/                  # Tailwind and custom CSS
│   ├── js/                   # Alpine.js and custom scripts
│   └── img/                  # Images and icons
├── templates/                # Jinja2 templates
├── tests/                    # Test suite
├── data/                     # Data directory (existing)
├── .pre-commit-config.yaml   # Pre-commit hooks configuration
├── .flake8                   # Flake8 configuration
├── pyproject.toml            # Project metadata and dependencies
├── Dockerfile                # Container definition
└── docker-compose.yml        # Development environment setup





## 3. Development Standards Configuration
### 3.1 Black Configuration (pyproject.toml)
**toml**




**Apply to mcp.json**














[tool.black]
line-length = 88
target-version = ["py39"]
include = '\.pyi?$'



### 3.2 Flake8 Configuration (.flake8)
**ini**




**Apply to mcp.json**
















[flake8]
max-line-length = 88
extend-ignore = E203
per-file-ignores = __init__.py:F401
exclude = .git,__pycache__,build,dist



### 3.3 Pydocstyle Configuration (pyproject.toml)
**toml**




**Apply to mcp.json**












[tool.pydocstyle]
convention = "google"
add-select = ["D100", "D101", "D102", "D103"]



### 3.4 Pre-commit Configuration (.pre-commit-config.yaml)
**yaml**




**Apply to mcp.json**




















































repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8

-   repo: https://github.com/pycqa/pydocstyle
    rev: 6.3.0
    hooks:
    -   id: pydocstyle





## 4. Implementation Phases
### 4.1 Phase 1: Core Data Model and Basic API
### 1 Set up project structure and dependencies
1 Implement Pydantic models for Author, Work, and Edition
1 Create CatalogService for accessing authors.json and file structure
1 Implement XMLProcessorService for parsing TEI XML files
1 Create API endpoints for browsing authors and viewing texts
1 Develop basic UI templates with HTMX and Tailwind
1 Implement basic Scaife import functionality

⠀4.2 Phase 2: Enhanced Features
### 1 Implement sorting, filtering, and search capabilities
1 Create improved text reader with customization options
1 Add user preferences with client-side storage
1 Enhance import functionality with metadata extraction
1 Improve UI with responsive design and accessibility

⠀4.3 Phase 3: Database Integration
### 1 Design PostgreSQL schema
1 Create SQLAlchemy ORM models
1 Implement migration utilities from file-based to database storage
1 Refactor services to use database repositories

⠀5. Testing Strategy
### 5.1 Unit Tests
**python**




**Apply to mcp.json**




















*# Example test structure for catalog service*
def test_get_all_authors():
    """Test retrieving all authors from catalog."""
    service = CatalogService()
    authors = service.get_all_authors()
    *assert* len(authors) > 0
    *assert* all(isinstance(author, Author) *for* author *in* authors)



### 5.2 Integration Tests
**python**




**Apply to mcp.json**
























*# Example API test*
async def test_get_authors_endpoint():
    """Test GET /api/authors endpoint."""
    *async* *with* AsyncClient(*app*=app, *base_url*="http://test") *as* client:
        response = *await* client.get("/api/authors")
        *assert* response.status_code == 200
        data = response.json()
        *assert* len(data) > 0
        *assert* "name" in data[0]



### 5.3 Test Configuration (pyproject.toml)
**toml**




**Apply to mcp.json**














[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "--cov=app --cov-report=term --cov-report=html"





## 6. Logging Configuration


python




Apply to mcp.json


































































*# app/utils/logging.py*
*from* loguru *import* logger
*import* sys
*import* os

def configure_logging():
    """Configure application logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    *# Remove default handler*
    logger.remove()
    
    *# Add console handler*
    logger.add(
        sys.stderr,
        *level*=log_level,
        *format*="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    *# Add file handler for non-development environments*
    *if* os.getenv("ENVIRONMENT", "development") != "development":
        logger.add(
            "logs/eulogos.log",
            *rotation*="10 MB",
            *retention*="1 week",
            *level*=log_level,
            *format*="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        )
    
    *return* logger





## 7. Docker Configuration
### 7.1 Dockerfile
**dockerfile**




**Apply to mcp.json**












































































*# Build stage*
FROM python:3.9-slim as builder

WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir build && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -e .

*# Runtime stage*
FROM python:3.9-slim

WORKDIR /app

*# Copy wheels from builder stage*
COPY --from=builder /app/wheels /app/wheels

*# Install dependencies*
RUN pip install --no-cache-dir /app/wheels/*

*# Copy application code*
COPY app/ /app/app/
COPY static/ /app/static/
COPY templates/ /app/templates/

*# Set environment variables*
ENV PYTHONPATH=/app
ENV PORT=8000

*# Expose port*
EXPOSE 8000

*# Run the application*
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]



### 7.2 docker-compose.yml
**yaml**




**Apply to mcp.json**






































version: '3'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
      - ./static:/app/static
      - ./templates:/app/templates
      - ./data:/app/data
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload





## 8. CI/CD Configuration (.github/workflows/ci.yml)


yaml




Apply to mcp.json














































































name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
        
    - name: Lint with flake8
      run: flake8 .
        
    - name: Check formatting with black
      run: black --check .
      
    - name: Run tests
      run: pytest
      
    - name: Upload coverage report
      uses: codecov/codecov-action@v3





## 9. Next Steps and Priorities
### 1 Set up project structure and development environment
1 Implement core data models and catalog service
1 Create basic API endpoints for browsing authors and works
1 Develop simple UI with HTMX and Tailwind
1 Set up testing and CI/CD pipeline
1 Implement XML processing service
1 Add basic text viewer
1 Implement search functionality
1 Add import capability
1 Enhance UI with advanced features

⠀This roadmap provides a comprehensive path to implementing the Eulogos system as specified, with careful attention to code quality, testing, and deployment considerations.
