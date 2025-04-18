"""Tests for catalog models.

This module tests the catalog data models and ensures they function properly
with ID-based references instead of URN-based references.
"""

import pytest

from app.models.catalog import Author, Text, CatalogStatistics, UnifiedCatalog


def test_unified_catalog():
    """Test the UnifiedCatalog model with nested components using ID-based references."""
    # Create authors
    authors = {
        "author1": Author(id="author1", name="Homer", century=-8, type="Poet"),
        "author2": Author(id="author2", name="Plato", century=-4, type="Philosopher"),
    }
    
    # Create texts with IDs and paths (no URNs)
    texts = [
        Text(
            id="text1",
            group_name="Homer",
            work_name="Iliad",
            language="grc",
            wordcount=102000,
            author_id="author1",
            path="data/grc/homer/iliad.xml",
        ),
        Text(
            id="text2",
            group_name="Plato",
            work_name="Republic",
            language="grc",
            wordcount=85000,
            author_id="author2",
            path="data/grc/plato/republic.xml",
        ),
    ]
    
    # Create statistics
    stats = CatalogStatistics(
        text_count=2,
        author_count=2,
        work_count=2,
        greek_word_count=187000,
        latin_word_count=0,
        arabic_word_count=0,
    )
    
    # Create the unified catalog
    catalog = UnifiedCatalog(
        statistics=stats,
        authors=authors,
        catalog=texts,
    )
    
    # Check components
    assert catalog.statistics.author_count == 2
    assert catalog.statistics.text_count == 2
    assert catalog.statistics.greek_word_count == 187000
    
    assert len(catalog.authors) == 2
    assert catalog.authors["author1"].name == "Homer"
    assert catalog.authors["author2"].name == "Plato"
    
    assert len(catalog.catalog) == 2
    assert catalog.catalog[0].work_name == "Iliad"
    assert catalog.catalog[1].work_name == "Republic"
    assert catalog.catalog[0].id == "text1"
    assert catalog.catalog[1].id == "text2"
    assert catalog.catalog[0].path == "data/grc/homer/iliad.xml"
    assert catalog.catalog[1].path == "data/grc/plato/republic.xml"


def test_text_model():
    """Test the Text model with ID-based functionality."""
    # Create a text with ID and path
    text = Text(
        id="text-123",
        group_name="Homer",
        work_name="Iliad",
        language="grc",
        wordcount=102000,
        author_id="author-456",
        path="data/grc/homer/iliad.xml",
    )
    
    # Test properties
    assert text.id == "text-123"
    assert text.group_name == "Homer"
    assert text.work_name == "Iliad"
    assert text.language == "grc"
    assert text.wordcount == 102000
    assert text.author_id == "author-456"
    assert text.path == "data/grc/homer/iliad.xml"
    
    # Test dictionary conversion
    text_dict = text.to_dict()
    assert text_dict["id"] == "text-123"
    assert text_dict["group_name"] == "Homer"
    assert text_dict["work_name"] == "Iliad"
    assert text_dict["language"] == "grc"
    assert text_dict["wordcount"] == 102000
    assert text_dict["author_id"] == "author-456"
    assert text_dict["path"] == "data/grc/homer/iliad.xml"
    assert "urn" not in text_dict  # Ensure no URN
    
    # Test creation from dictionary
    new_text = Text.from_dict(text_dict)
    assert new_text.id == text.id
    assert new_text.group_name == text.group_name
    assert new_text.work_name == text.work_name
    assert new_text.language == text.language
    assert new_text.wordcount == text.wordcount
    assert new_text.author_id == text.author_id
    assert new_text.path == text.path
    
    # Test string representation
    assert str(text) == f"{text.group_name}: {text.work_name} ({text.language})"


def test_author_model():
    """Test the Author model."""
    author = Author(id="author-123", name="Homer", century=-8, type="Poet")
    
    assert author.id == "author-123"
    assert author.name == "Homer"
    assert author.century == -8
    assert author.type == "Poet"
    
    # Test string representation
    assert str(author) == "Homer (8th century BCE)" 