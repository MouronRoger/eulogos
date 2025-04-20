# Eulogos

A modern web interface for browsing and reading ancient texts.

## Description

Eulogos is a web application that provides an intuitive interface for browsing, searching, and reading ancient texts, particularly in Greek and Latin. It is built on top of a catalog of XML files in the TEI (Text Encoding Initiative) format.

Key features:

- Browse texts by author or language
- Search for specific texts or authors
- Read texts with clean, modern typesetting
- Navigate texts using reference markers
- Customize reading experience (font size, line height, dark mode)
- Mark texts as favorites for easy access

## Technology Stack

- **Backend**: FastAPI with Pydantic for data validation
- **Frontend**: Tailwind CSS, Alpine.js, and HTMX
- **Data**: XML files in TEI format, organized in a hierarchical catalog

## Getting Started

### Prerequisites

- Python 3.8+
- A collection of TEI XML files (or use the sample data)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/eulogos.git
   cd eulogos
   ```

2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python run.py
   ```

5. Open your browser and navigate to `http://localhost:8000`

### Running the Application

You can specify several options when running the application:

```
python run.py --host 0.0.0.0 --port 8080 --reload
```

Options:
- `--host`: Specify the host to bind to (default: 127.0.0.1)
- `--port`: Specify the port to listen on (default: 8000)
- `--reload`: Enable auto-reload for development

### Development

To run the application with auto-reload:
```
python run.py --reload
```

## Implementation Details

### Data Flow

1. The application loads text metadata from the hierarchical `integrated_catalog.json` file
2. This data is transformed into a flat list of `Text` objects for easier manipulation
3. When a user views a text, the XML file is loaded from the `data` directory and transformed into HTML

### Frontend Architecture

The frontend uses a combination of:
- **Tailwind CSS** for styling
- **Alpine.js** for reactivity and UI state management
- **HTMX** for dynamic content loading without full page refreshes

Key UI features include:
- Dark mode toggle with persistent preference via localStorage
- Font size and line height adjustments
- References sidebar for navigating structured texts

### Customization

To customize the application:
- Add custom CSS in `app/static/css/main.css`
- Add custom JavaScript in `app/static/js/main.js`
- Modify templates in `app/templates/`

## Project Structure

```
eulogos/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Application configuration
│   ├── models/                 # Pydantic models
│   ├── services/               # Business logic
│   ├── routers/                # API routes
│   ├── templates/              # Jinja2 templates
│   └── static/                 # Static assets
├── data/                       # Data directory for XML files
├── canonical_catalog_builder.py # Catalog generator
├── integrated_catalog.json     # Generated catalog
└── run.py                      # Application runner
```

## Test Suite

The Eulogos project includes a comprehensive test suite to ensure reliability and correctness.

### Test Structure

```
tests/
├── conftest.py                 # Shared pytest fixtures
├── unit/                       # Unit tests
│   ├── test_catalog_service.py # Tests for catalog service
│   ├── test_xml_service.py     # Tests for XML service
│   └── test_models.py          # Tests for Pydantic models
├── integration/                # Integration tests
│   ├── test_browse_endpoints.py # Tests for browse endpoints
│   └── test_read_endpoints.py  # Tests for read endpoints
└── fixtures/                   # Test fixtures
    ├── catalog/                # Sample catalog data
    └── xml/                    # Sample XML files
```

### Running Tests

To run the entire test suite:

```bash
pytest
```

To run specific test categories:

```bash
pytest tests/unit/            # Run all unit tests
pytest tests/integration/     # Run all integration tests
pytest -k "catalog"           # Run all tests with "catalog" in the name
```

To generate a coverage report:

```bash
pytest --cov=app tests/
```

### Key Test Principles

1. **Path-based identification**: All tests verify that text paths from the catalog are used as canonical identifiers.
2. **Single source of truth**: Tests validate that `integrated_catalog.json` is the sole source of truth for text metadata.
3. **Data integrity**: Tests ensure catalog data structure remains consistent throughout the application.
4. **Error handling**: Tests include both success and failure cases to ensure proper error handling.

### CI/CD Integration

GitHub Actions automatically runs the test suite for every push and pull request. The workflow configuration is in `.github/workflows/test.yml`.

## Catalog Structure

The application uses `integrated_catalog.json` as its source of truth for text metadata. This file is generated by `canonical_catalog_builder.py`, which scans the `data` directory for XML files and extracts metadata.

## License

See the LICENSE file for details.

## Acknowledgments

This project builds on the work of many open-source projects and digital humanities initiatives. 