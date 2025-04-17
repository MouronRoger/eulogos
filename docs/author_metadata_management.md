# Author Metadata Management

This document outlines how to manage author metadata in the Eulogos project, especially when new authors are added to the collection.

## Overview

The Eulogos project uses three key files to manage catalog data:

1. **catalog_index.json**: Contains information about individual texts, including URNs, languages, and word counts
2. **author_index.json**: Contains metadata about authors, such as their name, century, and type
3. **integrated_catalog.json**: A comprehensive catalog combining data from both sources

## Workflow for Managing New Authors

### When New Texts Are Added

When new texts are added to the system and scanned:

1. The `catalog_index.json` will be automatically updated with new text entries
2. New authors will appear in the `integrated_catalog.json` with minimal information
3. These new authors will have `null` values for `century` and `type` fields

### Adding Author Metadata

To properly document new authors:

1. Identify new authors in the integrated catalog with null metadata
2. Add them to `author_index.json` with the following structure:

```json
{
    "author_id": {
        "name": "Author's Full Name",
        "century": 2,  // Century number (negative for BCE)
        "type": "Type of Author"  // e.g., "Historian", "Poet", "Christian", etc.
    }
}
```

### Author Types

Common author types include:
- "Historian"
- "Poet"
- "Rhetorician"
- "Philosopher"
- "Christian"
- "Physician"
- "Mathematician"
- "Grammarian"
- "Platonist"
- "Peripatetic"
- "Stoic"
- "Epicurean"

### Century Format

Use integer values for centuries:
- Positive integers for CE (e.g., `2` for 2nd century CE)
- Negative integers for BCE (e.g., `-5` for 5th century BCE)

## Regenerating the Integrated Catalog

After updating the author metadata:

1. Run the regeneration script:
```bash
bash regenerate_integrated_catalog.sh
```

2. This will:
   - Create a backup of the existing integrated catalog
   - Generate a new integrated catalog with updated author metadata
   - Preserve all text information from the catalog index

## Important Notes

- The `author_index.json` is the canonical source for author metadata
- Never edit author metadata directly in the `integrated_catalog.json`
- If author metadata changes, update `author_index.json` and regenerate the catalog

This workflow ensures that all author metadata is properly maintained while allowing new texts to be automatically included in the system.
