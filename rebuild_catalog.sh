#!/bin/bash
# This is the canonical script to rebuild the integrated catalog for Eulogos
# It uses the definitive catalog builder located at app/scripts/canonical_catalog_builder.py

set -e  # Exit immediately if a command exits with a non-zero status

# Default parameters
DATA_DIR="data"
OUTPUT="integrated_catalog.json"
AUTHOR_INDEX="author_index.json"
VERBOSE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --data-dir|-d)
      DATA_DIR="$2"
      shift 2
      ;;
    --output|-o)
      OUTPUT="$2"
      shift 2
      ;;
    --author-index|-a)
      AUTHOR_INDEX="$2"
      shift 2
      ;;
    --verbose|-v)
      VERBOSE="--verbose"
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "  --data-dir, -d       Specify data directory (default: data)"
      echo "  --output, -o         Specify output file (default: integrated_catalog.json)"
      echo "  --author-index, -a   Specify author index file (default: author_index.json)"
      echo "  --verbose, -v        Enable verbose output"
      echo "  --help, -h           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help to see available options"
      exit 1
      ;;
  esac
done

# Check if files exist
if [[ ! -f "$AUTHOR_INDEX" ]]; then
    echo "ERROR: Author index file not found: $AUTHOR_INDEX"
    exit 1
fi

if [[ ! -d "$DATA_DIR" ]]; then
    echo "ERROR: Data directory not found: $DATA_DIR"
    exit 1
fi

# Create backup of existing integrated catalog if it exists
if [[ -f "$OUTPUT" ]]; then
    BACKUP="${OUTPUT}.bak"
    echo "Creating backup of existing integrated catalog to $BACKUP"
    cp "$OUTPUT" "$BACKUP"
fi

# Run the canonical catalog builder
echo "Generating integrated catalog..."
echo "Using data directory: $DATA_DIR"
echo "Using author index: $AUTHOR_INDEX"
echo "Output file: $OUTPUT"

python3 app/scripts/canonical_catalog_builder.py \
    --data-dir="$DATA_DIR" \
    --output="$OUTPUT" \
    --author-index="$AUTHOR_INDEX" \
    $VERBOSE

# Check if generation was successful
if [ $? -eq 0 ]; then
    echo "SUCCESS: Integrated catalog regenerated successfully!"

    # Display statistics if jq is available
    if command -v jq >/dev/null 2>&1; then
        echo "Catalog statistics:"
        jq -r 'to_entries |
               "Authors: \(length)\n" +
               "Works: \(reduce .[] as $item (0; . + ($item.value.works | length)))\n" +
               "Editions: \(reduce .[] as $item (0; . + (reduce ($item.value.works | .[]) as $work (0; . + ($work.editions | length)))))\n" +
               "Translations: \(reduce .[] as $item (0; . + (reduce ($item.value.works | .[]) as $work (0; . + ($work.translations | length)))))"' "$OUTPUT"
    fi

    echo ""
    echo "NOTE: The integrated catalog is now up to date."
    echo "This catalog contains all author metadata from $AUTHOR_INDEX"
else
    echo "ERROR: Failed to generate integrated catalog"
    exit 1
fi
