# Catalog Maintenance Guide

This guide explains how to maintain the catalog system in the Eulogos project, particularly focusing on the integrated catalog generation.

## Catalog File Structure

The Eulogos project uses three key catalog files:

1. **catalog_index.json**: Contains information about texts, including URNs, languages, and word counts
2. **author_index.json**: Contains author metadata (name, century, type)
3. **integrated_catalog.json**: The comprehensive catalog that combines both sources

## Regenerating the Integrated Catalog

The integrated catalog should be regenerated when:
- New texts have been added to the system
- Author metadata has been updated in `author_index.json`
- The catalog files become out of sync

### Using the Regeneration Script

```bash
./regenerate_integrated_catalog.sh
```

This script:
- Backs up the existing integrated catalog
- Combines `catalog_index.json` and `author_index.json`
- Preserves author metadata while including all texts
- Outputs to `integrated_catalog.json`

## Adding New Authors

When new texts with previously unknown authors are added to the system:

1. The text will be included in `catalog_index.json`
2. When you regenerate the integrated catalog, the new author will be included with null metadata
3. To add proper metadata, update `author_index.json` with the author information
4. Regenerate the integrated catalog to include the updated metadata

## Author Metadata Format

The `author_index.json` file contains entries in this format:

```json
{
  "tlg0001": {
    "name": "Author Name",
    "century": 2,  // positive for CE, negative for BCE
    "type": "Author Type"  // e.g., "Historian", "Poet", etc.
  }
}
```

For more details on author metadata management, see [Author Metadata Management](author_metadata_management.md).

## Common Issues and Solutions

### Missing Author Metadata

If an author appears in the integrated catalog with null metadata:
1. Add the author to `author_index.json` with appropriate metadata
2. Run the regeneration script

### Incorrect Author Information

If author information is incorrect:
1. Update the author entry in `author_index.json`
2. Run the regeneration script

### Missing Texts in Integrated Catalog

If texts from the catalog index don't appear in the integrated catalog:
1. Verify that the text has a valid URN structure
2. Check if the catalog regeneration script was run with the `--lenient` flag (required for non-standard URNs)

## Best Practices

1. Always maintain author metadata in `author_index.json`, not in the integrated catalog
2. Run the regeneration script after any changes to the catalog sources
3. Validate the integrated catalog regularly to ensure all texts are properly included

## Git and Large Catalog Files

The integrated catalog files can become quite large (>500KB), which exceeds GitHub's recommended file size limit. To handle these large files:

### Files Excluded from Git

The following files are excluded from Git tracking via .gitignore:
- `integrated_catalog.json`
- `integrated_catalog.json.bak`
- `new_integrated_catalog.json`
- Other `.bak` files

### Working with the Repository

When cloning or pulling the repository:
1. The source files (`catalog_index.json` and `author_index.json`) are included in Git
2. You'll need to generate the integrated catalog locally using:
   ```bash
   ./regenerate_integrated_catalog.sh
   ```

### When Making Changes

1. Make changes to the source files (`catalog_index.json` or `author_index.json`)
2. Regenerate the integrated catalog
3. Commit and push only the source files, not the generated files

This approach keeps the repository size manageable while ensuring everyone can generate the complete integrated catalog when needed.
