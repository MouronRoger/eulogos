"""Unit tests for the Pydantic models.

These tests verify that the models correctly validate and process data,
using paths as canonical identifiers.
"""

import pytest
from typing import List

from app.models.catalog import Text, Catalog


def test_text_model_creation() -> None:
    """Test creating a Text model with valid data."""
    # Create with required fields
    text = Text(
        path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
        title="Sample Title",
        author="Sample Author"
    )
    
    # Verify the created text
    assert text.path == "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    assert text.title == "Sample Title"
    assert text.author == "Sample Author"
    assert text.language == "unknown"  # Default value
    assert text.metadata == {}  # Default value
    assert text.favorite is False  # Default value
    assert text.archived is False  # Default value
    
    # Create with all fields
    text = Text(
        path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
        title="Sample Title",
        author="Sample Author",
        language="Greek",
        metadata={"urn": "urn:sample", "edition_id": "edition1"},
        favorite=True,
        archived=False
    )
    
    # Verify the created text
    assert text.path == "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    assert text.title == "Sample Title"
    assert text.author == "Sample Author"
    assert text.language == "Greek"
    assert text.metadata == {"urn": "urn:sample", "edition_id": "edition1"}
    assert text.favorite is True
    assert text.archived is False
    
    # Test string representation
    assert str(text) == "Sample Title by Sample Author (Greek)"


def test_catalog_model_creation() -> None:
    """Test creating a Catalog model with valid data."""
    # Create an empty catalog
    catalog = Catalog()
    assert catalog.texts == []
    
    # Create a catalog with texts
    texts = [
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
            title="Title 1",
            author="Author 1",
            language="Greek"
        ),
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
            title="Title 2",
            author="Author 1",
            language="English"
        ),
        Text(
            path="tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml",
            title="Title 3",
            author="Author 2",
            language="Greek"
        )
    ]
    
    catalog = Catalog(texts=texts)
    
    # Verify the created catalog
    assert len(catalog.texts) == 3
    assert catalog.texts[0].path == "tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml"
    assert catalog.texts[1].path == "tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml"
    assert catalog.texts[2].path == "tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml"
    
    # Test string representation
    assert str(catalog) == "Catalog with 3 texts"


def test_catalog_get_text_by_path() -> None:
    """Test getting a text by path from the catalog."""
    # Create a catalog with texts
    texts = [
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
            title="Title 1",
            author="Author 1",
            language="Greek"
        ),
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
            title="Title 2",
            author="Author 1",
            language="English"
        )
    ]
    
    catalog = Catalog(texts=texts)
    
    # Get an existing text
    text = catalog.get_text_by_path("tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml")
    assert text is not None
    assert text.title == "Title 1"
    
    # Get a non-existent text
    text = catalog.get_text_by_path("nonexistent/path.xml")
    assert text is None


def test_catalog_get_texts_by_author() -> None:
    """Test getting texts by author from the catalog."""
    # Create a catalog with texts
    texts = [
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
            title="Title 1",
            author="Author 1",
            language="Greek"
        ),
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
            title="Title 2",
            author="Author 1",
            language="English"
        ),
        Text(
            path="tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml",
            title="Title 3",
            author="Author 2",
            language="Greek"
        )
    ]
    
    catalog = Catalog(texts=texts)
    
    # Get texts for an existing author
    author_texts = catalog.get_texts_by_author("Author 1")
    assert len(author_texts) == 2
    assert author_texts[0].title == "Title 1"
    assert author_texts[1].title == "Title 2"
    
    # Get texts for another existing author
    author_texts = catalog.get_texts_by_author("Author 2")
    assert len(author_texts) == 1
    assert author_texts[0].title == "Title 3"
    
    # Get texts for a non-existent author
    author_texts = catalog.get_texts_by_author("Nonexistent Author")
    assert len(author_texts) == 0


def test_catalog_get_texts_by_language() -> None:
    """Test getting texts by language from the catalog."""
    # Create a catalog with texts
    texts = [
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
            title="Title 1",
            author="Author 1",
            language="Greek"
        ),
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
            title="Title 2",
            author="Author 1",
            language="English"
        ),
        Text(
            path="tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml",
            title="Title 3",
            author="Author 2",
            language="Greek"
        )
    ]
    
    catalog = Catalog(texts=texts)
    
    # Get texts for an existing language
    language_texts = catalog.get_texts_by_language("Greek")
    assert len(language_texts) == 2
    assert language_texts[0].title == "Title 1"
    assert language_texts[1].title == "Title 3"
    
    # Get texts for another existing language
    language_texts = catalog.get_texts_by_language("English")
    assert len(language_texts) == 1
    assert language_texts[0].title == "Title 2"
    
    # Get texts for a non-existent language
    language_texts = catalog.get_texts_by_language("Nonexistent Language")
    assert len(language_texts) == 0


def test_catalog_get_unique_authors() -> None:
    """Test getting unique authors from the catalog."""
    # Create a catalog with texts
    texts = [
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
            title="Title 1",
            author="Author 1",
            language="Greek"
        ),
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
            title="Title 2",
            author="Author 1",
            language="English"
        ),
        Text(
            path="tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml",
            title="Title 3",
            author="Author 2",
            language="Greek"
        )
    ]
    
    catalog = Catalog(texts=texts)
    
    # Get unique authors
    authors = catalog.get_unique_authors()
    assert len(authors) == 2
    assert "Author 1" in authors
    assert "Author 2" in authors


def test_catalog_get_unique_languages() -> None:
    """Test getting unique languages from the catalog."""
    # Create a catalog with texts
    texts = [
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
            title="Title 1",
            author="Author 1",
            language="Greek"
        ),
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-eng2.xml",
            title="Title 2",
            author="Author 1",
            language="English"
        ),
        Text(
            path="tlg0085/tlg001/tlg0085.tlg001.perseus-grc2.xml",
            title="Title 3",
            author="Author 2",
            language="Greek"
        )
    ]
    
    catalog = Catalog(texts=texts)
    
    # Get unique languages
    languages = catalog.get_unique_languages()
    assert len(languages) == 2
    assert "Greek" in languages
    assert "English" in languages


def test_catalog_toggle_favorite() -> None:
    """Test toggling favorite status on a text."""
    # Create a catalog with texts
    texts = [
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
            title="Title 1",
            author="Author 1",
            language="Greek"
        )
    ]
    
    catalog = Catalog(texts=texts)
    
    # Toggle favorite for an existing text
    success = catalog.toggle_favorite("tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml")
    assert success is True
    
    # Verify favorite was toggled
    text = catalog.get_text_by_path("tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml")
    assert text is not None
    assert text.favorite is True
    
    # Toggle favorite for a non-existent text
    success = catalog.toggle_favorite("nonexistent/path.xml")
    assert success is False


def test_catalog_set_archived() -> None:
    """Test setting archived status on a text."""
    # Create a catalog with texts
    texts = [
        Text(
            path="tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml",
            title="Title 1",
            author="Author 1",
            language="Greek"
        )
    ]
    
    catalog = Catalog(texts=texts)
    
    # Set archived for an existing text
    success = catalog.set_archived("tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml", True)
    assert success is True
    
    # Verify archived was set
    text = catalog.get_text_by_path("tlg0004/tlg001/tlg0004.tlg001.perseus-grc2.xml")
    assert text is not None
    assert text.archived is True
    
    # Set archived for a non-existent text
    success = catalog.set_archived("nonexistent/path.xml", True)
    assert success is False 