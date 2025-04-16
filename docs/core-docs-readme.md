# Eulogos

Eulogos is a web application for accessing, viewing, and studying ancient Greek texts from the First 1000 Years Project. It provides scholars, students, and enthusiasts with tools to browse texts by author, read works with specialized viewing options, search across the corpus, and export texts in various formats.

![Eulogos Screenshot]()

## Features

- **Hierarchical Author-Works Browser**: Navigate through texts organized by author, era, and language
- **Advanced Text Reader**: Read texts with reference navigation and word analysis capabilities
- **Multi-Format Export**: Export texts to PDF, ePub, MOBI, Markdown, DOCX, LaTeX, and HTML
- **Text Management**: Archive, favorite, or delete texts as needed
- **Reference Navigation**: Navigate texts using hierarchical references (e.g., book.chapter.verse)
- **Word Analysis**: Analyze Greek words with morphological and lexical information
- **Search**: Find texts and passages with advanced search options

## Quick Start

### Prerequisites

- Python 3.9+
- Git

### Installation

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

4. Setup environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the application:
   ```bash
   python run.py
   ```

6. Access the application at http://localhost:8000

## Technology Stack

- **Backend**: Python 3.9+, FastAPI, Pydantic, lxml
- **Frontend**: HTMX, Alpine.js, Tailwind CSS
- **Data Storage**: File-based with JSON catalog and TEI XML texts (future: PostgreSQL, Vector database)

## Repository Structure

```
app/                  # FastAPI application
├── api/              # API endpoints
├── core/             # Core functionality
├── models/           # Pydantic models
├── services/         # Business logic services
├── templates/        # HTMX templates
├── static/           # Static files
├── utils/            # Utility functions
└── main.py           # Application entry point

data/                 # Text data files

docs/                 # Documentation
├── ARCHITECTURE.md   # System architecture
├── IMPLEMENTATION-PLAN.md  # Implementation roadmap
├── USER-GUIDE.md     # User documentation
├── DEVELOPMENT.md    # Developer documentation
└── API-REFERENCE.md  # API documentation

tests/                # Test suite

requirements.txt      # Python dependencies
run.py                # Entry point script
```

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md): Details about the system architecture and design
- [IMPLEMENTATION-PLAN.md](docs/IMPLEMENTATION-PLAN.md): Implementation roadmap and current status
- [USER-GUIDE.md](docs/USER-GUIDE.md): Guide for end users of the application
- [DEVELOPMENT.md](docs/DEVELOPMENT.md): Information for developers contributing to the project
- [API-REFERENCE.md](docs/API-REFERENCE.md): API documentation for programmatic access

## Implementation Status

As of April 2025, Eulogos is in active development:

- **Phase 1 (Core Text Browser)**: LARGELY COMPLETE
- **Phase 2 (Enhanced Features and Export)**: IN PROGRESS
- **Phase 3-5 (Database and Advanced Features)**: PLANNED

See [IMPLEMENTATION-PLAN.md](docs/IMPLEMENTATION-PLAN.md) for more details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to the project.

Before submitting a pull request:

1. Ensure that your code follows the project's style guidelines
2. Add tests for new functionality
3. Ensure all tests pass by running `pytest`
4. Update documentation as needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project uses texts and metadata from the Perseus Digital Library
- Special thanks to the entire First 1000 Years Project team
- The CITE Architecture and CTS URN system
