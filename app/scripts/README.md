# Eulogos Scripts

This directory contains scripts for maintaining and operating the Eulogos repository.

## Canonical Catalog Builder

The `canonical_catalog_builder.py` script is the definitive and authoritative catalog generator for the Eulogos project. It is the heart of the repository, responsible for generating the `integrated_catalog.json` file that powers the entire application.

### Features

- Scans the data directory for `__cts__.xml` files
- Extracts author/work/edition/translation metadata
- Merges with author metadata from `author_index.json`
- Ensures all fields are present and paths are correct
- Adds missing authors with blank metadata
- Sorts output alphabetically at each level

### Usage

The script can be used directly:

```bash
python app/scripts/canonical_catalog_builder.py --data-dir=data --output=integrated_catalog.json --author-index=author_index.json --verbose
```

Or through the convenience wrapper script in the repository root:

```bash
./rebuild_catalog.sh
```

### Parameters

- `--data-dir`: Path to the data directory (default: "data")
- `--output`: Path for the output catalog file (default: "integrated_catalog.json")
- `--author-index`: Path to the author index file (default: "author_index.json")
- `--verbose`: Enable verbose output

### Integration

The catalog builder is integrated with the admin interface of the application, allowing administrators to rebuild the catalog through the web UI. This is handled by the `CatalogGeneratorService` class.

### Testing

The script can be tested using the `test_integrated_catalog.py` script in the repository root, which validates that the catalog builder is functioning correctly.
