#!/bin/bash
# Script to regenerate the integrated catalog from author_index.json and catalog_index.json

set -e  # Exit immediately if a command exits with a non-zero status

# Define paths
CATALOG_INDEX="catalog_index.json"
AUTHOR_INDEX="author_index.json"
OUTPUT="integrated_catalog.json"
DATA_DIR="data"

# Check if files exist
if [[ ! -f "$CATALOG_INDEX" ]]; then
    echo "ERROR: Catalog index file not found: $CATALOG_INDEX"
    exit 1
fi

if [[ ! -f "$AUTHOR_INDEX" ]]; then
    echo "ERROR: Author index file not found: $AUTHOR_INDEX"
    exit 1
fi

# Create backup of existing integrated catalog if it exists
if [[ -f "$OUTPUT" ]]; then
    BACKUP="${OUTPUT}.bak"
    echo "Creating backup of existing integrated catalog to $BACKUP"
    cp "$OUTPUT" "$BACKUP"
fi

# Run the integrated catalog generator using the Python module
echo "Generating integrated catalog..."
PYTHONPATH=. python app/scripts/generate_integrated_catalog.py \
    --catalog "$CATALOG_INDEX" \
    --authors "$AUTHOR_INDEX" \
    --output "$OUTPUT" \
    --data-dir "$DATA_DIR" \
    --pretty \
    --lenient

# Check if generation was successful
if [ $? -eq 0 ]; then
    echo "SUCCESS: Integrated catalog regenerated successfully!"
    echo "The integrated catalog now contains all author metadata from $AUTHOR_INDEX"

    # Confirm the number of authors
    NUM_AUTHORS=$(cat "$OUTPUT" | grep -o '"author_count": [0-9]*' | cut -d' ' -f2)
    echo "Total authors in integrated catalog: $NUM_AUTHORS"

    echo ""
    echo "NOTE: When new authors are added to the data:"
    echo "1. They will be automatically included in the integrated catalog"
    echo "2. You should manually update their metadata in $AUTHOR_INDEX"
    echo "3. Run this script again to update the integrated catalog with the metadata"
else
    echo "ERROR: Failed to generate integrated catalog"
    exit 1
fi
