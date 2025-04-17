"""Tests for the EnhancedURN model."""

from pathlib import Path

import pytest

from app.models.enhanced_urn import EnhancedURN


def test_urn_parsing():
    """Test URN parsing."""
    # Basic URN
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert urn.namespace == "greekLit"
    assert urn.textgroup == "tlg0012"
    assert urn.work == "tlg001"
    assert urn.version == "perseus-grc1"
    assert urn.reference is None

    # URN with reference
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1:1.1-1.10")
    assert urn.namespace == "greekLit"
    assert urn.textgroup == "tlg0012"
    assert urn.work == "tlg001"
    assert urn.version == "perseus-grc1"
    assert urn.reference == "1.1-1.10"

    # URN with colon-separated reference
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1:1.1")
    assert urn.reference == "1.1"


def test_urn_validation():
    """Test URN validation."""
    # Valid URN
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert urn.is_valid_for_path()

    # Invalid URN (missing version)
    with pytest.raises(ValueError):
        EnhancedURN(value="not-a-urn")

    # Invalid for path (missing components)
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012")
    assert not urn.is_valid_for_path()


def test_get_file_path():
    """Test file path generation."""
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    path = urn.get_file_path("test_data")

    # Path should not include namespace
    expected_path = Path("test_data/tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml")
    assert path == expected_path

    # Invalid URN for path
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012")
    with pytest.raises(ValueError):
        urn.get_file_path()


def test_compatibility():
    """Test compatibility with original URN models."""

    class MockOriginalURN:
        def __init__(self, value):
            self.value = value

    # Test conversion from original
    original = MockOriginalURN("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    enhanced = EnhancedURN.from_original(original)
    assert enhanced.value == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test conversion to original
    converted = enhanced.to_original_urn(MockOriginalURN)
    assert isinstance(converted, MockOriginalURN)
    assert converted.value == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test with CtsUrn-like interface
    class MockCtsUrn:
        def __init__(self, urn_string):
            self.urn_string = urn_string

    original_cts = MockCtsUrn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    enhanced = EnhancedURN.from_original(original_cts)
    assert enhanced.value == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
