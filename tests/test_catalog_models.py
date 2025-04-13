"""Tests for catalog models."""

import pytest

from app.models.catalog import Author, Text, CatalogStatistics, UnifiedCatalog


def test_author_model():
    """Test the Author model."""
    author = Author(name="Homer", century=-8, type="Poet")
    assert author.name == "Homer"
    assert author.century == -8
    assert author.type == "Poet"


def test_text_model():
    """Test the Text model with URN parsing."""
    text = Text(
        urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
        group_name="Homer",
        work_name="Iliad",
        language="grc",
        wordcount=102000,
        author_id="tlg0012",
    )
    
    assert text.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"
    assert text.group_name == "Homer"
    assert text.work_name == "Iliad"
    assert text.language == "grc"
    assert text.wordcount == 102000
    assert text.author_id == "tlg0012"
    
    # Check parsed URN components
    assert text.namespace == "greekLit"
    assert text.textgroup == "tlg0012"
    assert text.work_id == "tlg001"
    assert text.version == "perseus-grc2"
    assert text.passage is None


def test_text_model_with_passage():
    """Test the Text model with a passage reference in the URN."""
    text = Text(
        urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10",
        group_name="Homer",
        work_name="Iliad",
        language="grc",
        wordcount=102000,
        author_id="tlg0012",
    )
    
    # Check parsed URN components
    assert text.namespace == "greekLit"
    assert text.textgroup == "tlg0012"
    assert text.work_id == "tlg001"
    assert text.version == "perseus-grc2"
    assert text.passage == "1.1-1.10"


def test_catalog_statistics():
    """Test the CatalogStatistics model."""
    stats = CatalogStatistics(
        nodeCount=1000,
        greekWords=5000000,
        latinWords=1000000,
        arabicwords=10000,
        authorCount=500,
        textCount=2000,
    )
    
    assert stats.nodeCount == 1000
    assert stats.greekWords == 5000000
    assert stats.latinWords == 1000000
    assert stats.arabicwords == 10000
    assert stats.authorCount == 500
    assert stats.textCount == 2000


def test_unified_catalog():
    """Test the UnifiedCatalog model with nested components."""
    # Create authors
    authors = {
        "tlg0012": Author(name="Homer", century=-8, type="Poet"),
        "tlg0059": Author(name="Plato", century=-4, type="Philosopher"),
    }
    
    # Create texts
    texts = [
        Text(
            urn="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
            group_name="Homer",
            work_name="Iliad",
            language="grc",
            wordcount=102000,
            author_id="tlg0012",
        ),
        Text(
            urn="urn:cts:greekLit:tlg0059.tlg002.perseus-grc2",
            group_name="Plato",
            work_name="Republic",
            language="grc",
            wordcount=85000,
            author_id="tlg0059",
        ),
    ]
    
    # Create statistics
    stats = CatalogStatistics(
        nodeCount=1000,
        greekWords=187000,
        latinWords=0,
        arabicwords=0,
        authorCount=2,
        textCount=2,
    )
    
    # Create the unified catalog
    catalog = UnifiedCatalog(
        statistics=stats,
        authors=authors,
        catalog=texts,
    )
    
    # Check components
    assert catalog.statistics.authorCount == 2
    assert catalog.statistics.textCount == 2
    assert catalog.statistics.greekWords == 187000
    
    assert len(catalog.authors) == 2
    assert catalog.authors["tlg0012"].name == "Homer"
    assert catalog.authors["tlg0059"].name == "Plato"
    
    assert len(catalog.catalog) == 2
    assert catalog.catalog[0].work_name == "Iliad"
    assert catalog.catalog[1].work_name == "Republic" 