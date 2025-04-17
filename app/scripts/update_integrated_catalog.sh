#!/bin/bash

# Script to update the integrated catalog and validate the result
# Usage: ./update_integrated_catalog.sh [options]

set -e  # Exit immediately if a command exits with a non-zero status

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Set default paths
DATA_DIR="$ROOT_DIR/data"
CATALOG_FILE="$ROOT_DIR/integrated_catalog.json"
AUTHOR_INDEX="$ROOT_DIR/author_index.json"
VALIDATOR_SCRIPT="$SCRIPT_DIR/validate_catalog.py"

# Parse command line arguments
BACKUP=false
FORCE=false
PRETTY=false
LOG_LEVEL="info"

while [[ $# -gt 0 ]]; do
  case $1 in
    --no-validate)
      NO_VALIDATE=true
      shift
      ;;
    --data-dir)
      DATA_DIR="$2"
      shift 2
      ;;
    --catalog)
      CATALOG_FILE="$2"
      shift 2
      ;;
    --author-index)
      AUTHOR_INDEX="$2"
      shift 2
      ;;
    --backup|-b)
      BACKUP=true
      shift
      ;;
    --force|-f)
      FORCE=true
      shift
      ;;
    --pretty|-p)
      PRETTY=true
      shift
      ;;
    --log-level|-l)
      LOG_LEVEL="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --no-validate           Skip validation after update"
      echo "  --data-dir DIR          Data directory (default: $DATA_DIR)"
      echo "  --catalog FILE          Catalog file (default: $CATALOG_FILE)"
      echo "  --author-index FILE     Author index file (default: $AUTHOR_INDEX)"
      echo "  --backup, -b            Create a backup of the existing catalog"
      echo "  --force, -f             Force update even if no changes are detected"
      echo "  --pretty, -p            Format the output JSON with indentation"
      echo "  --log-level, -l LEVEL   Set the log level (debug, info, warning, error, critical)"
      echo "  --help, -h              Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help to see available options"
      exit 1
      ;;
  esac
done

echo "Starting catalog update process..."
echo "Data directory: $DATA_DIR"
echo "Catalog file: $CATALOG_FILE"
echo "Author index: $AUTHOR_INDEX"

# Create command with options
CMD="python $SCRIPT_DIR/update_integrated_catalog.py --data-dir '$DATA_DIR' --catalog '$CATALOG_FILE' --author-index '$AUTHOR_INDEX' --log-level $LOG_LEVEL"

if [ "$BACKUP" = true ]; then
  CMD="$CMD --backup"
fi

if [ "$FORCE" = true ]; then
  CMD="$CMD --force"
fi

if [ "$PRETTY" = true ]; then
  CMD="$CMD --pretty"
fi

# Run the update script
echo "Running catalog update..."
eval $CMD

# Check if update was successful
if [ $? -ne 0 ]; then
  echo "Catalog update failed. See logs for details."
  exit 1
fi

# Validate the catalog if requested
if [ "$NO_VALIDATE" != true ] && [ -f "$VALIDATOR_SCRIPT" ]; then
  echo "Validating updated catalog..."
  python "$VALIDATOR_SCRIPT" "$CATALOG_FILE"

  if [ $? -ne 0 ]; then
    echo "Catalog validation failed. The updated catalog may contain errors."
    exit 1
  else
    echo "Catalog validation successful."
  fi
else
  echo "Catalog validation skipped."
fi

echo "Catalog update process completed successfully."
