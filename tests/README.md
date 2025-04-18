# Eulogos Test Suite

## Overview

This test suite is designed to verify the correctness and functionality of the Eulogos application, specifically focusing on the ID-based path resolution that has replaced the previous URN-based approach.

## Test Design Philosophy

The test suite is structured to ensure:

1. **Data Integrity**: Tests verify that the catalog structure is valid and that paths correctly map to files.
2. **Service Functionality**: All core services work correctly with ID-based access.
3. **API Correctness**: Endpoints properly handle ID-based requests.
4. **Error Handling**: Appropriate errors are returned for invalid inputs.

## Test Structure

The test suite is organized into several groups:

1. **Unit Tests**
   - `test_catalog_models.py`: Tests for data models
   - `test_catalog_service.py`: Tests for catalog service functions
   - `test_xml_processor_service.py`: Tests for XML processing
   - `test_export_service.py`: Tests for export functionality

2. **Integration Tests**
   - `test_integration.py`: End-to-end workflow tests

3. **Data Integrity Tests**
   - `test_data_integrity.py`: Tests catalog structure and path resolution

4. **API Tests**
   - `test_id_based_endpoints.py`: Tests for ID-based API endpoints

## Running Tests

Use the `run_tests.py` script to run the tests:

```bash
# Run all tests
python scripts/run_tests.py

# Run a specific test group
python scripts/run_tests.py --group unit
python scripts/run_tests.py --group integration
python scripts/run_tests.py --group data
python scripts/run_tests.py --group api

# Run with coverage reporting
python scripts/run_tests.py --coverage

# Run verbose
python scripts/run_tests.py -v
```

## Test Fixtures

Common test fixtures are defined in `conftest.py`:

- `sample_catalog_data`: A sample catalog structure
- `sample_catalog_file`: A temporary catalog file
- `sample_xml_file`: A sample XML file
- `test_settings`: Test configuration settings
- `temp_dir`: A temporary directory for test files
- `client`: A test client for API tests

## ID-Based Testing

All tests have been updated to use ID-based access instead of URN-based access:

- Text models use `id` and `path` fields 
- Path resolution happens through the catalog
- No URN parsing or construction occurs in the codebase

## Adding New Tests

When adding new tests:

1. Follow the established test structure.
2. Use pytest fixtures for setup and teardown.
3. Mock external dependencies.
4. Focus on behavior, not implementation details.
5. Ensure tests verify ID-based path resolution.
6. Verify error handling for edge cases.
7. Follow Black formatting and flake8 standards.

## Continuous Integration

Tests are run automatically on pull requests and commits to main branches.
Make sure all tests pass before submitting changes. 