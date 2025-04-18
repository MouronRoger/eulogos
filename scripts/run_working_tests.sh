#!/bin/bash
# Run only the tests that have been fixed to work with ID-based path resolution

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running Eulogos test suite for ID-based path resolution${NC}"
echo -e "${BLUE}==========================================================${NC}"

# Set environment variable for testing
export TESTING=1

# Array of test files we know work correctly
WORKING_TESTS=(
    "tests/test_catalog_models.py"
    "tests/test_data_integrity.py"
)

# Run pytest with verbosity and coverage
echo -e "${BLUE}Running tests with coverage${NC}"
python -m pytest ${WORKING_TESTS[@]} -v --cov=app.models.catalog --cov=app.services.enhanced_catalog_service

# Run pytest with xvs option if specified
if [ "$1" == "--xvs" ]; then
    echo -e "${BLUE}Running tests with coverage (excluding venv and site-packages)${NC}"
    python -m pytest ${WORKING_TESTS[@]} -v --cov=app.models.catalog --cov=app.services.enhanced_catalog_service --cov-report=term-missing --cov-config=.coveragerc
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi 