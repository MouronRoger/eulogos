#!/bin/bash
# Script to verify all aspects of the hierarchical implementation

# Exit on any error
set -e

echo "========================================"
echo "Eulogos Hierarchical Implementation Verification"
echo "========================================"

echo -e "\n[1] Checking import integrity..."
echo "Looking for catalog_service imports:"
grep -R "catalog_service" app | grep -v "services/catalog_service.py"

echo -e "\n[2] Verifying path consistency in templates..."
echo "Checking href attributes:"
grep -r "href=" app/templates/ | grep "read" | grep -v "text.path" || echo "✓ All href attributes use text.path"

echo "Checking hx-post attributes:"
grep -r "hx-post=" app/templates/ | grep -v "text.path" || echo "✓ All hx-post attributes use text.path"

echo -e "\n[3] Verifying Jinja2 templates directory structure..."
echo "Template structure:"
find app/templates -type f | sort

echo -e "\n[4] Checking for any legacy code or file paths..."
echo "Looking for flat/dual-mode implementations:"
grep -r "flat" app/ || echo "✓ No references to flat implementation"
grep -r "hierarchical.*=.*True" app/ || echo "✓ No feature flags found"

echo -e "\n[5] Verifying JavaScript functionality..."
echo "Checking for required functions:"
grep -r "function initAuthorExpandedState" app/static/js/main.js || echo "❌ Missing initAuthorExpandedState function!"
grep -r "function toggleFavoriteButton" app/static/js/main.js || echo "❌ Missing toggleFavoriteButton function!"
grep -r "function updateArchiveButton" app/static/js/main.js || echo "❌ Missing updateArchiveButton function!"

echo -e "\n[6] Testing catalog loading..."
echo "Attempting to load catalog:"
PYTHONPATH=. python -c "from app.services.catalog_service import get_catalog_service; service = get_catalog_service(); print(f'✓ Success! Loaded {len(service.get_all_authors())} authors')"

if [ $? -eq 0 ]; then
    echo "✓ Catalog loads successfully"
else
    echo "❌ Failed to load catalog!"
    exit 1
fi

echo -e "\n[7] Running tests..."
if [ -d "tests" ]; then
    pytest -v
else
    echo "❌ No tests directory found!"
fi

echo -e "\n[8] Verifying code quality..."
if command -v black &> /dev/null; then
    echo "Running black..."
    black --check --line-length 88 app tests || echo "❌ Black formatting issues found"
else
    echo "⚠️ Black not installed, skipping formatting check"
fi

if command -v flake8 &> /dev/null; then
    echo "Running flake8..."
    flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics || echo "❌ Flake8 issues found"
else
    echo "⚠️ Flake8 not installed, skipping linting check"
fi

if command -v pydocstyle &> /dev/null; then
    echo "Running pydocstyle..."
    pydocstyle app || echo "❌ Docstring issues found"
else
    echo "⚠️ Pydocstyle not installed, skipping docstring check"
fi

echo -e "\n========================================"
echo "Verification complete. Review any warnings or errors above."
echo "If all checks passed, the implementation is ready for deployment."
echo -e "========================================"

echo -e "\nHuman QA Checklist:"
echo "1. Home page renders with authors list"
echo "2. Expand/collapse persists across refresh"
echo "3. Clicking a text opens /read/{path}"
echo "4. Favorite toggle updates immediately"
echo "5. Archive hides text unless 'show archived' enabled"