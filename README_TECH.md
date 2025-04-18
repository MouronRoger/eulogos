# Eulogos Tech Stack - Simplified Canonical Approach

## Core Principles

The Eulogos project has been significantly refactored to address bloat and inconsistency. The new approach is founded on these **strict canonical principles**:

1. **ONE Canonical Data Source**
   - `integrated_catalog.json` is the ONLY source of truth for all file paths
   - All text metadata must come from this single catalog file

2. **ONE Canonical Method**
   - Direct path access via `/data/{path}` is the ONLY acceptable method
   - No URN processing or path reconstruction is permitted

3. **ONE Canonical Catalog Builder**
   - `canonical_catalog_builder.py` is the only authorized tool for catalog generation
   - Run manually only when adding new texts or updating metadata

## Simplified Tech Stack

### Core Components

- **Python 3.9+**: Primary programming language
- **FastAPI**: Web framework and API
- **HTMX + Alpine.js + Tailwind CSS**: Frontend technologies
- **Jinja2**: Template rendering

### Data Flow Architecture

```
canonical_catalog_builder.py  →  integrated_catalog.json  →  Application Services
                                        ↓
                                    data/ directory
                                (Direct file access)
```

### Data Access Pattern

```python
# CORRECT APPROACH
def get_text_content(text_id):
    # 1. Get path from the canonical catalog
    text = catalog_service.get_text(text_id)
    file_path = text.path

    # 2. Access file directly using the path
    with open(f"data/{file_path}", "r") as f:
        return f.read()
```

```python
# INCORRECT APPROACH - DO NOT USE
def get_text_content(urn):
    # ❌ Reconstructing paths from URN components
    namespace, group, work, version = parse_urn(urn)
    file_path = f"data/{group}/{work}/{group}.{work}.{version}.xml"

    # ❌ Using reconstructed path
    with open(file_path, "r") as f:
        return f.read()
```

## Service Architecture

- **CatalogService**: Loads the integrated catalog, provides lookup methods
- **XMLProcessorService**: Processes XML using paths from catalog
- **ExportService**: Creates exports in various formats
- **API Routers**: Expose functionality through FastAPI endpoints

## Development Requirements

- **Linting**: Black (88 char), Flake8, Pydocstyle D100s
- **Type Safety**: Type annotations required for all functions
- **Documentation**: Clear, concise docstrings following Google style
- **Code Quality**: No unused imports, variables, uncaught exceptions
- **Clean Code**: No commented-out code or TODOs without plans

## Implementation Guidelines

1. **Always use the catalog as the source of truth**
   - Never reconstruct paths from URNs or other identifiers
   - Always get file paths directly from the catalog

2. **Keep it simple**
   - Direct file access is preferred
   - Avoid complex abstractions or middleware layers
   - Minimize dependencies between components

3. **Progressive enhancement**
   - Focus on core functionality first
   - Add features incrementally on a stable foundation
   - Maintain backward compatibility

## Workflow Pattern

1. User requests a text by ID
2. Application looks up the text in `integrated_catalog.json`
3. Application retrieves the file path from the catalog entry
4. Application opens and processes the file directly using the path
5. Application returns the processed content to the user

## Testing Strategy

- Unit tests for service components
- Integration tests for API endpoints
- Validation tests to ensure catalog integrity
- No mocking of file system access - use real catalog and test data

## Deployment

- Docker containerization
- GitHub Actions workflow for CI/CD
- Automated linting and testing

## Migration Note

All existing code that attempts to reconstruct file paths through URN processing or other means MUST be replaced with direct path access from the integrated catalog. This is a fundamental architectural principle of the repository.
