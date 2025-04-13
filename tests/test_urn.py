"""Tests for CTS URN utility."""

import pytest
from pathlib import Path

from app.utils.urn import CtsUrn


def test_cts_urn_parsing():
    """Test parsing a CTS URN."""
    urn = CtsUrn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
    
    assert urn.namespace == "greekLit"
    assert urn.textgroup == "tlg0012"
    assert urn.work == "tlg001"
    assert urn.version == "perseus-grc2"
    assert urn.passage is None
    
    assert str(urn) == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"


def test_cts_urn_with_passage():
    """Test parsing a CTS URN with a passage reference."""
    urn = CtsUrn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10")
    
    assert urn.namespace == "greekLit"
    assert urn.textgroup == "tlg0012"
    assert urn.work == "tlg001"
    assert urn.version == "perseus-grc2"
    assert urn.passage == "1.1-1.10"


def test_invalid_urn_prefix():
    """Test handling an invalid URN prefix."""
    with pytest.raises(ValueError) as excinfo:
        CtsUrn("invalid:cts:greekLit:tlg0012.tlg001.perseus-grc2")
    
    assert "Invalid CTS URN" in str(excinfo.value)


def test_incomplete_urn():
    """Test handling an incomplete URN."""
    with pytest.raises(ValueError) as excinfo:
        CtsUrn("urn:cts:greekLit")
    
    assert "Incomplete CTS URN" in str(excinfo.value)


def test_invalid_identifier():
    """Test handling an invalid text identifier."""
    with pytest.raises(ValueError) as excinfo:
        CtsUrn("urn:cts:greekLit:tlg0012")
    
    assert "Invalid text identifier" in str(excinfo.value)


def test_file_path():
    """Test deriving a file path from a URN."""
    urn = CtsUrn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
    path = urn.get_file_path("data")
    
    expected_path = Path("data/greekLit/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml")
    assert path == expected_path


def test_file_path_without_version():
    """Test handling a URN without version information."""
    urn = CtsUrn("urn:cts:greekLit:tlg0012.tlg001")
    
    with pytest.raises(ValueError) as excinfo:
        urn.get_file_path()
    
    assert "Cannot derive file path without version information" in str(excinfo.value)


def test_get_textgroup_urn():
    """Test getting a textgroup-level URN."""
    urn = CtsUrn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
    textgroup_urn = urn.get_textgroup_urn()
    
    assert textgroup_urn == "urn:cts:greekLit:tlg0012"


def test_get_work_urn():
    """Test getting a work-level URN."""
    urn = CtsUrn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
    work_urn = urn.get_work_urn()
    
    assert work_urn == "urn:cts:greekLit:tlg0012.tlg001"


def test_get_version_urn():
    """Test getting a version-level URN without passage."""
    urn = CtsUrn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10")
    version_urn = urn.get_version_urn()
    
    assert version_urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2" 