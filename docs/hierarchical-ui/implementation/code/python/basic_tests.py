"""Minimal test suite for Eulogos application.

These tests verify the core functionality of the application after migration.
"""

import pytest
from fastapi.testclient import TestClient

from app.services.catalog_service import get_catalog_service
from app.main import app


def test_catalog_load():
    """Verify that the catalog loads successfully and contains authors."""
    catalog_service = get_catalog_service()
    
    # Verify authors were loaded
    authors = catalog_service.get_all_authors()
    assert len(authors) > 0, "No authors found in catalog"
    
    # Verify hierarchical structure works
    hierarchical = catalog_service.get_hierarchical_texts()
    assert isinstance(hierarchical, dict), "Hierarchical texts should be a dictionary"
    assert len(hierarchical) > 0, "No authors found in hierarchical structure"


def test_root_endpoint():
    """Verify that the root endpoint returns a 200 status code."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200, "Root endpoint should return 200 status code"


def test_search_endpoint():
    """Verify that the search endpoint works with a basic query."""
    client = TestClient(app)
    response = client.get("/search?q=a")
    assert response.status_code == 200, "Search endpoint should return 200 status code"


def test_browse_endpoint():
    """Verify that the browse endpoint works with various filters."""
    client = TestClient(app)
    
    # Test basic browse
    response = client.get("/browse")
    assert response.status_code == 200, "Browse endpoint should return 200 status code"
    
    # Test with author filter (using a known author or pass if none specified)
    authors = get_catalog_service().get_all_authors()
    if authors:
        response = client.get(f"/browse?author={authors[0]}")
        assert response.status_code == 200, "Browse with author filter should return 200"
    
    # Test favorites
    response = client.get("/browse?show_favorites=true")
    assert response.status_code == 200, "Browse favorites should return 200 status code"