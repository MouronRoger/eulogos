"""Integration tests for browse endpoints.

These tests verify that the browse endpoints correctly handle requests
and return appropriate responses, using paths as canonical identifiers.
"""

import pytest
from typing import Dict, Any

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.models.catalog import Text


def test_home_page(client: TestClient) -> None:
    """Test the home page."""
    with patch("app.routers.browse.get_catalog_service") as mock_get_service:
        # Mock the catalog service
        mock_service = mock_get_service.return_value
        mock_service.get_all_authors.return_value = ["Diogenes Laertius", "Herodotus"]
        mock_service.get_all_languages.return_value = ["Greek", "English"]
        mock_service.get_all_texts.return_value = [
            Text(
                path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
                title="Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
                author="Diogenes Laertius",
                language="Greek"
            ),
            Text(
                path="tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml",
                title="Ἱστορίαι",
                author="Herodotus",
                language="Greek"
            )
        ]
        
        # Make request to the home page
        response = client.get("/")
        
        # Check response status
        assert response.status_code == 200
        
        # Check content
        assert "Browse Texts" in response.text
        assert "Diogenes Laertius" in response.text
        assert "Herodotus" in response.text
        assert "Greek" in response.text
        assert "English" in response.text


def test_browse_by_author(client: TestClient) -> None:
    """Test browsing texts by author."""
    with patch("app.routers.browse.get_catalog_service") as mock_get_service:
        # Mock the catalog service
        mock_service = mock_get_service.return_value
        mock_service.get_texts_by_author.return_value = [
            Text(
                path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
                title="Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
                author="Diogenes Laertius",
                language="Greek"
            ),
            Text(
                path="tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
                title="Lives of Eminent Philosophers",
                author="Diogenes Laertius",
                language="English"
            )
        ]
        
        # Make request to browse by author
        response = client.get("/author/Diogenes%20Laertius")
        
        # Check response status
        assert response.status_code == 200
        
        # Check content
        assert "Diogenes Laertius" in response.text
        assert "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων" in response.text
        assert "Lives of Eminent Philosophers" in response.text
        
        # Check that paths are used as identifiers in links
        assert "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml" in response.text
        assert "tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml" in response.text


def test_browse_by_language(client: TestClient) -> None:
    """Test browsing texts by language."""
    with patch("app.routers.browse.get_catalog_service") as mock_get_service:
        # Mock the catalog service
        mock_service = mock_get_service.return_value
        mock_service.get_texts_by_language.return_value = [
            Text(
                path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
                title="Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
                author="Diogenes Laertius",
                language="Greek"
            ),
            Text(
                path="tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml",
                title="Ἱστορίαι",
                author="Herodotus",
                language="Greek"
            )
        ]
        
        # Make request to browse by language
        response = client.get("/language/Greek")
        
        # Check response status
        assert response.status_code == 200
        
        # Check content
        assert "Greek Texts" in response.text
        assert "Diogenes Laertius" in response.text
        assert "Herodotus" in response.text
        assert "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων" in response.text
        assert "Ἱστορίαι" in response.text
        
        # Check that paths are used as identifiers in links
        assert "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml" in response.text
        assert "tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml" in response.text


def test_search_texts(client: TestClient) -> None:
    """Test searching for texts."""
    with patch("app.routers.browse.get_catalog_service") as mock_get_service:
        # Mock the catalog service
        mock_service = mock_get_service.return_value
        mock_service.search_texts.return_value = [
            Text(
                path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
                title="Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
                author="Diogenes Laertius",
                language="Greek"
            )
        ]
        
        # Make request to search
        response = client.get("/search?q=Diogenes")
        
        # Check response status
        assert response.status_code == 200
        
        # Check content
        assert "Search Results" in response.text
        assert "Diogenes Laertius" in response.text
        assert "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων" in response.text
        
        # Check that paths are used as identifiers in links
        assert "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml" in response.text
        
        # Verify search with no results
        mock_service.search_texts.return_value = []
        response = client.get("/search?q=nonexistent")
        assert response.status_code == 200
        assert "No texts found" in response.text


def test_favorites(client: TestClient) -> None:
    """Test viewing and managing favorites."""
    with patch("app.routers.browse.get_catalog_service") as mock_get_service:
        # Mock the catalog service
        mock_service = mock_get_service.return_value
        mock_service.get_favorite_texts.return_value = [
            Text(
                path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
                title="Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων",
                author="Diogenes Laertius",
                language="Greek",
                favorite=True
            )
        ]
        
        # Make request to view favorites
        response = client.get("/favorites")
        
        # Check response status
        assert response.status_code == 200
        
        # Check content
        assert "Favorite Texts" in response.text
        assert "Diogenes Laertius" in response.text
        assert "Βίοι καὶ γνῶμαι τῶν ἐν φιλοσοφίᾳ εὐδοκιμησάντων" in response.text
        
        # Check that paths are used as identifiers in links
        assert "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml" in response.text
        
        # Test toggling favorite
        mock_service.toggle_favorite.return_value = True
        response = client.post(
            "/api/favorite",
            json={"path": "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify that the service was called with the correct path
        mock_service.toggle_favorite.assert_called_with(
            "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
        )


def test_api_authors(client: TestClient) -> None:
    """Test the API endpoint for authors."""
    with patch("app.routers.browse.get_catalog_service") as mock_get_service:
        # Mock the catalog service
        mock_service = mock_get_service.return_value
        mock_service.get_all_authors.return_value = ["Diogenes Laertius", "Herodotus"]
        
        # Make request to the API
        response = client.get("/api/authors")
        
        # Check response status
        assert response.status_code == 200
        
        # Check content
        data = response.json()
        assert isinstance(data, list)
        assert "Diogenes Laertius" in data
        assert "Herodotus" in data


def test_api_languages(client: TestClient) -> None:
    """Test the API endpoint for languages."""
    with patch("app.routers.browse.get_catalog_service") as mock_get_service:
        # Mock the catalog service
        mock_service = mock_get_service.return_value
        mock_service.get_all_languages.return_value = ["Greek", "English"]
        
        # Make request to the API
        response = client.get("/api/languages")
        
        # Check response status
        assert response.status_code == 200
        
        # Check content
        data = response.json()
        assert isinstance(data, list)
        assert "Greek" in data
        assert "English" in data 