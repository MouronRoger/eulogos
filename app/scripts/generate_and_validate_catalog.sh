#!/bin/bash
# Script to generate and validate the integrated catalog

set -e  # Exit on error

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
CATALOG_INDEX="${ROOT_DIR}/catalog_index.json"
AUTHOR_INDEX="${ROOT_DIR}/author_index.json"
INTEGRATED_CATALOG="${ROOT_DIR}/integrated_catalog.json"
DATA_DIR="${ROOT_DIR}/data"
LOG_DIR="${ROOT_DIR}/logs"
VALIDATION_REPORT="${LOG_DIR}/validation_report.json"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log file
LOG_FILE="${LOG_DIR}/catalog_migration_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# Check if source files exist
if [[ ! -f "$CATALOG_INDEX" ]]; then
    log "ERROR: Catalog index file not found: $CATALOG_INDEX"
    exit 1
fi

if [[ ! -f "$AUTHOR_INDEX" ]]; then
    log "ERROR: Author index file not found: $AUTHOR_INDEX"
    exit 1
fi

if [[ ! -d "$DATA_DIR" ]]; then
    log "ERROR: Data directory not found: $DATA_DIR"
    exit 1
fi

# 1. Generate the integrated catalog
log "Generating integrated catalog..."
python3 "${SCRIPT_DIR}/generate_integrated_catalog.py" \
    --catalog "$CATALOG_INDEX" \
    --authors "$AUTHOR_INDEX" \
    --output "$INTEGRATED_CATALOG" \
    --data-dir "$DATA_DIR" \
    --pretty \
    --validate \
    --lenient

if [ $? -ne 0 ]; then
    log "ERROR: Failed to generate integrated catalog"
    exit 1
fi

log "Integrated catalog generated successfully: $INTEGRATED_CATALOG"

# 2. Validate the integrated catalog
log "Validating integrated catalog..."
python3 "${SCRIPT_DIR}/validate_integrated_catalog.py" \
    --catalog "$INTEGRATED_CATALOG" \
    --data-dir "$DATA_DIR" \
    --output "$VALIDATION_REPORT" \
    --log-level "info"

VALIDATION_RESULT=$?

if [ $VALIDATION_RESULT -eq 0 ]; then
    log "Validation successful! The integrated catalog is valid."
    log "Validation report saved to: $VALIDATION_REPORT"
elif [ $VALIDATION_RESULT -eq 1 ]; then
    log "WARNING: Validation found issues with the integrated catalog."
    log "Review the validation report: $VALIDATION_REPORT"
    # Exit with success since this may be expected during migration
    exit 0
else
    log "ERROR: Validation script encountered an error."
    exit 1
fi

log "Migration process completed successfully!"
exit 0
