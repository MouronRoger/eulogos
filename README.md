# Eulogos

A web application for accessing, searching, and studying ancient Greek texts from the First 1000 Years Project.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/eulogos.git
cd eulogos

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Catalog Validation

To validate the catalog index against the data files, use the `validate_catalog.py` script:

```bash
# Run the validation with default paths
python app/scripts/validate_catalog.py

# Specify custom paths
python app/scripts/validate_catalog.py --catalog /path/to/catalog_index.json --authors /path/to/author_index.json --data /path/to/data

# Save the validation results to a file
python app/scripts/validate_catalog.py --output validation_results.json

# Only show missing files and authors
python app/scripts/validate_catalog.py --missing-only

# Set the log level
python app/scripts/validate_catalog.py --log-level debug
```

### Validation Options

- `--catalog`, `-c`: Path to catalog_index.json file (default: catalog_index.json)
- `--authors`, `-a`: Path to author_index.json file (default: author_index.json)
- `--data`, `-d`: Path to data directory containing XML files (default: data)
- `--output`, `-o`: Output file for validation results in JSON format
- `--log-level`, `-l`: Set the log level (choices: debug, info, warning, error, critical; default: info)
- `--missing-only`, `-m`: Only report missing files and authors

## Creating a Unified Catalog

To merge the author index and catalog index into a unified catalog file, use the `merge_catalog.py` script:

```bash
# Create a unified catalog with default paths
python app/scripts/merge_catalog.py

# Specify custom paths
python app/scripts/merge_catalog.py --catalog /path/to/catalog_index.json --authors /path/to/author_index.json --output /path/to/unified_catalog.json

# Format the output JSON with indentation for readability
python app/scripts/merge_catalog.py --pretty
```

### Merge Options

- `--catalog`, `-c`: Path to catalog_index.json file (default: catalog_index.json)
- `--authors`, `-a`: Path to author_index.json file (default: author_index.json)
- `--output`, `-o`: Output file for the unified catalog (default: unified_catalog.json)
- `--log-level`, `-l`: Set the log level (choices: debug, info, warning, error, critical; default: info)
- `--pretty`, `-p`: Format the output JSON with indentation for readability

## Development

### Running the Application (Not Yet Implemented)

```bash
# Run the development server
python -m uvicorn app.main:app --reload
```

### Project Structure

```
eulogos/
├── app/
│   ├── models/          # Pydantic models
│   ├── routers/         # FastAPI routers
│   ├── scripts/         # Utility scripts
│   ├── services/        # Business logic
│   ├── static/          # Static files
│   ├── templates/       # Jinja2 templates
│   ├── utils/           # Utility functions
│   └── main.py          # FastAPI application
├── data/                # Data files
├── docs/                # Documentation
│   ├── author_metadata_management.md  # Author metadata guide
│   └── catalog_maintenance.md         # Catalog maintenance guide
├── tests/               # Tests
├── .flake8             # Flake8 configuration
├── .pydocstyle         # Pydocstyle configuration
├── pyproject.toml      # Black configuration
├── requirements.txt    # Dependencies
├── regenerate_integrated_catalog.sh  # Script to regenerate the integrated catalog
└── README.md           # This file
```

## Catalog System

Eulogos maintains three important catalog files:

1. **catalog_index.json**: Contains information about texts, including URNs, languages, and word counts
2. **author_index.json**: Contains author metadata (name, century, type)
3. **integrated_catalog.json**: The comprehensive catalog that combines both sources

### Regenerating the Integrated Catalog

To regenerate the integrated catalog (combining author metadata with text data):

```bash
./regenerate_integrated_catalog.sh
```

This script:
- Backs up the existing integrated catalog
- Combines `catalog_index.json` and `author_index.json`
- Preserves author metadata while including all texts
- Outputs to `integrated_catalog.json`

For more detailed information about catalog maintenance, see:
- [Catalog Maintenance Guide](docs/catalog_maintenance.md)
- [Author Metadata Management](docs/author_metadata_management.md)

## Coding Standards

This project follows strict coding standards to ensure high-quality, maintainable code. All code must be written to pass linting checks on the first attempt. Please review and follow our [Coding Standards](docs/coding_standards.md) before contributing.

Key points:
- Follow Black formatting (120 character line length)
- Use Google-style docstrings
- All code must be type-hinted
- Write tests for all new code
- No linting errors allowed

## License

See the LICENSE file for details.
