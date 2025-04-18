# Eulogos - Ancient Greek Text Repository

## Overview

Eulogos is a web application for exploring, reading, and analyzing ancient Greek texts. It provides a simple, direct interface for accessing a comprehensive collection of texts from the First 1000 Years Project.

## ⚠️ IMPORTANT: Coding Standards and Linting ⚠️

**ALL contributions MUST adhere to strict linting standards:**

- **Black formatting** is mandatory with 88 character line limit
- **Flake8** linting must pass with zero errors or warnings
- **Pydocstyle D100s** docstring conventions must be followed
- **Type annotations** are required for all functions
- **Consistent 4-space indentation** throughout
- **No unused imports** or variables
- **No uncaught exceptions** or bare except blocks
- **Clean code only** - no commented-out code or TODOs without specific plan

**PRs that fail linting checks will be automatically rejected.** Test your code with linters before submitting any changes. The time spent fixing linting issues significantly exceeds development time.

## ⚠️ IMPORTANT: Canonical Data Access ⚠️

**This repository follows a strict canonical approach to data access:**

- **One Canonical Data Source**: `integrated_catalog.json` is the ONLY source of truth for all file paths
- **One Canonical Method**: Direct path access via `/data/{path}` is the ONLY acceptable method
- **No Path Reconstruction**: Any code attempting to reconstruct file paths through URN processing or other means MUST be replaced with direct path access
- **No Duplicate Methods**: Alternative ways to access files are not allowed to prevent confusion and inconsistency

**If you find ANY code that attempts to reconstruct data paths by any means, it MUST be replaced with direct path access.** This is a fundamental architectural principle of this repository.

## System Architecture

### Data Flow
```
Actual files in filesystem
        ↓
canonical_catalog_builder.py
        ↓
integrated_catalog.json
        ↓
All other system operations
```

### Core Architectural Principle

The `canonical_catalog_builder.py` is the **only** component that should ever:
- Scan the filesystem for files
- Generate path mappings
- Create catalog structures
- Build the relationship between paths and metadata

Everything else in the system should:
- Read from `integrated_catalog.json`
- Never try to construct or derive paths
- Never try to build alternative catalogs
- Use the catalog as the authoritative source for all lookups

This is a fundamental architectural principle of the system. The catalog builder creates the single source of truth (`integrated_catalog.json`) from which all other operations must derive their data. No other part of the system should attempt to replicate these responsibilities.

## Core Architecture

The repository is built around three essential components:

1. **`canonical_catalog_builder.py`** - The authoritative tool for catalog generation
   - **Run manually only** when adding new texts or updating metadata
   - Scans the data directory for XML files and metadata
   - Creates a comprehensive hierarchical catalog
   - Single source of truth for catalog generation

2. **`integrated_catalog.json`** - The static catalog file
   - Contains complete metadata for all texts
   - Includes direct file paths to XML documents
   - Loaded directly by the application without additional processing
   - Central data source for the application

3. **`data/` directory** - Contains all text files
   - Organized by author/work hierarchy
   - XML files with the actual text content
   - Referenced directly via paths in the catalog

## Development Philosophy

Eulogos follows these key principles:

- **Simplicity Over Complexity**
  - Direct file access using paths from the catalog
  - No unnecessary URN processing or complex abstractions
  - Minimal, focused codebase

- **Progressive Enhancement**
  - Core functionality first, then additional features
  - UI formatting and export functions are added to a stable core
  - Modular structure for easy maintenance

- **Data-Centric Approach**
  - The catalog is the central organizing principle
  - Simple, direct mapping from catalog entries to XML files
  - Straightforward data flow throughout the application

## Getting Started

### Installation

1. Clone the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python run.py`

### Using the Application

- Browse texts by author and work
- View formatted XML content
- Export texts in various formats (HTML, plain text)
- Access the API for programmatic usage

## Development Roadmap

The application is being progressively enhanced with these priorities:

1. **Core Functionality** (✓ Complete)
   - Basic catalog browsing
   - Direct XML file access
   - Simple text display

2. **Interface Improvements** (In Progress)
   - Enhanced text formatting
   - Improved navigation
   - Better search capabilities

3. **Export Capabilities** (Planned)
   - Multiple export formats
   - Batch export functionality
   - Customization options

## Technical Notes

- **No URN Processing**: The application works directly with file paths from the catalog
- **Catalog Generation**: Only the `canonical_catalog_builder.py` script should be used
- **Simplicity**: Avoiding unnecessary abstractions and complexity
- **Direct Path Access**: Always use paths directly from the catalog without reconstruction

## Contributing

Contributions are welcome! Please follow these guidelines:

- Maintain the simple, direct approach to file access
- Avoid adding complex abstractions or URN processing
- Focus on enhancing core functionality and user experience
- Follow coding standards (Black formatting, flake8, pydocstyle)
- **Run linters locally before submitting code changes**
- Verify that your code passes `black`, `flake8`, and `mypy` checks
- **Use only direct path access from the integrated_catalog.json**

## Linting Commands

```bash
# Format code with Black
black .

# Check with Flake8
flake8 .

# Check type annotations
mypy .

# Run all linting checks
./scripts/run_linting.sh
```
