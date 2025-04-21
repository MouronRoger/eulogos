# Contributing to Eulogos

This document outlines the guidelines for contributing to the Eulogos project.

## Core Principles

- **Single Source of Truth**: `integrated_catalog.json` is the ONLY source for text paths
- **Canonical References**: ALL text identification uses direct file paths ONLY
- **No Path Manipulation**: No string manipulation or alternate path construction is allowed
- **One Implementation**: No dual-mode or legacy code patterns are permitted

## Coding Standards

- **Formatting**: Black with 88-character line limit
- **Linting**: Flake8 compliance required
- **Docstrings**: pydocstyle D100s conventions for all modules, classes, and functions
- **Type Annotations**: Required for all function parameters and return values
- **Error Handling**: Comprehensive error handling with proper logging

## Directory Structure

```
app/
├── models/         # Pydantic data models
├── routers/        # FastAPI route handlers
├── services/       # Business logic services
├── static/         # Static assets (CSS, JS)
├── templates/      # Jinja2 templates
│   └── partials/   # Template partials
├── config.py       # Configuration settings
├── main.py         # Application entry point
└── settings.py     # Environment settings
```

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/eulogos.git
   cd eulogos
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Install development dependencies
   ```bash
   pip install black==23.3.0 flake8==6.0.0 pydocstyle==6.3.0 pytest==7.3.1 pytest-cov==4.1.0
   ```

4. Run the application
   ```bash
   uvicorn app.main:app --reload
   ```

## Working with the Catalog

- Always access texts using their canonical path from `integrated_catalog.json`
- Use the `CatalogService.get_text_by_path()` method to look up texts
- Never construct paths manually or use string manipulation on paths
- All API endpoints must consistently use path-based identifiers

## Hierarchical Structure

The application uses a hierarchical organization of texts:

```
Author
├── Metadata (century, era, type)
├── Work 1
│   ├── Text 1 (edition, translation)
│   └── Text 2 (edition, translation)
└── Work 2
    ├── Text 3 (edition, translation)
    └── Text 4 (edition, translation)
```

When working with this structure:
- Use `get_hierarchical_texts()` to get the complete structure
- Use `get_filtered_hierarchical_texts()` for filtered views
- Access individual texts via their canonical path

## Templates and JavaScript

- All templates must use `text.path` for links and actions
- JavaScript must use canonical paths for all AJAX requests
- Maintain robust error handling in JavaScript, especially for localStorage operations
- Preserve state for author expansion/collapse across page reloads

## Testing

Before submitting any changes:

1. Run formatting and linting:
   ```bash
   black --line-length 88 app tests
   flake8 app tests
   pydocstyle app
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Manually verify:
   - Home page renders with author list
   - Expand/collapse persists across refresh
   - Clicking a text opens /read/{path}
   - Favorite toggle updates immediately
   - Archive hides text unless 'show archived' enabled

## Pull Request Process

1. Create a feature branch (`git checkout -b feature/your-feature`)
2. Make your changes with appropriate tests
3. Ensure all tests pass and code is formatted correctly
4. Commit your changes (`git commit -am 'Add feature'`)
5. Push to the branch (`git push origin feature/your-feature`)
6. Submit a Pull Request

## Documentation

- Update README.md for any user-facing changes
- Update this CONTRIBUTING.md document for development workflow changes
- Keep docstrings up-to-date with code changes