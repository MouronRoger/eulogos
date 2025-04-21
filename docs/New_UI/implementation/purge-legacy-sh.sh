#!/bin/bash
# Script to purge legacy files before clean migration to hierarchical implementation

# Exit on any error
set -e

echo "Creating backups directory..."
mkdir -p backups/services backups/routers backups/templates backups/static/js

echo "Backing up files before removal..."
[ -f app/services/catalog_service.py ] && cp app/services/catalog_service.py backups/services/
[ -f app/routers/browse.py ] && cp app/routers/browse.py backups/routers/
[ -f app/templates/browse.html ] && cp app/templates/browse.html backups/templates/
[ -f app/static/js/main.js ] && cp app/static/js/main.js backups/static/js/

echo "Removing legacy files..."
rm -f app/services/catalog_service.py
rm -f app/routers/browse.py
rm -f app/templates/browse.html
rm -f app/templates/partials/author_list.html
rm -f app/static/js/main.js

echo "Removing legacy tests..."
rm -rf tests/

echo "Creating necessary directories..."
mkdir -p app/templates/partials

echo "Legacy files purged successfully."
echo "Next steps:"
echo "1. Commit this change: git add -A && git commit -m \"Remove legacy files for clean migration\""
echo "2. Proceed with implementing the new files"