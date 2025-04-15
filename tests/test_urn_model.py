"""Tests for URN Pydantic model."""

from pathlib import Path
from typing import Dict, Optional

import pytest

from app.models.urn import URN


class MockXMLProcessor:
    """Mock XMLProcessor for testing."""

    def load_xml(self, urn: URN) -> str:
        """Mock loading XML."""
        return "<root/>"

    def get_adjacent_references(self, xml_root: str, reference: Optional[str]) -> Dict[str, Optional[str]]:
        """Mock getting adjacent references."""
        if reference == "1.1":
            return {"prev": None, "next": "1.2"}
        elif reference == "1.2":
            return {"prev": "1.1", "next": "1.3"}
        else:
            return {"prev": None, "next": None}


def test_urn_parsing():
    """Test parsing a CTS URN."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

    assert urn.urn_namespace == "urn"
    assert urn.cts_namespace == "greekLit"
    assert urn.text_group == "tlg0012"
    assert urn.work == "tlg001"
    assert urn.version == "perseus-grc2"
    assert urn.reference is None

    assert urn.value == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2"


def test_urn_with_reference():
    """Test parsing a CTS URN with a passage reference."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10")

    assert urn.urn_namespace == "urn"
    assert urn.cts_namespace == "greekLit"
    assert urn.text_group == "tlg0012"
    assert urn.work == "tlg001"
    assert urn.version == "perseus-grc2"
    assert urn.reference == "1.1-1.10"


def test_invalid_urn_format():
    """Test handling an invalid URN format."""
    with pytest.raises(ValueError) as excinfo:
        URN(value="invalid:cts:greekLit:tlg0012.tlg001.perseus-grc2")

    assert "Invalid CTS URN format" in str(excinfo.value)


def test_urn_up_to_method():
    """Test the up_to method."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10")

    assert urn.up_to("urn_namespace") == "urn:urn"
    assert urn.up_to("cts_namespace") == "urn:urn:greekLit"
    assert urn.up_to("text_group") == "urn:urn:greekLit:tlg0012"
    assert urn.up_to("work") == "urn:urn:greekLit:tlg0012.tlg001"
    assert urn.up_to("version") == "urn:urn:greekLit:tlg0012.tlg001.perseus-grc2"
    assert urn.up_to("reference") == "urn:urn:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10"

    with pytest.raises(ValueError) as excinfo:
        urn.up_to("invalid_level")

    assert "Invalid URN level" in str(excinfo.value)


def test_replace_method():
    """Test the replace method."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.10")

    # Replace reference
    new_urn = urn.replace(reference="1.2")
    assert new_urn.reference == "1.2"
    assert new_urn.value.endswith(":1.2")

    # Replace version
    new_urn = urn.replace(version="perseus-eng1")
    assert new_urn.version == "perseus-eng1"
    assert "perseus-eng1" in new_urn.value

    # Replace multiple components
    new_urn = urn.replace(work="tlg002", version="perseus-eng1", reference="2.1-2.10")
    assert new_urn.work == "tlg002"
    assert new_urn.version == "perseus-eng1"
    assert new_urn.reference == "2.1-2.10"
    assert "tlg002.perseus-eng1:2.1-2.10" in new_urn.value


def test_get_file_path():
    """Test the get_file_path method."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")
    path = urn.get_file_path("data")

    expected_path = Path("data/greekLit/tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml")
    assert path == expected_path


def test_get_file_path_missing_components():
    """Test get_file_path with missing components."""
    # Missing version
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001")

    with pytest.raises(ValueError) as excinfo:
        urn.get_file_path()

    assert "URN missing components needed for file path" in str(excinfo.value)


def test_get_adjacent_references():
    """Test the get_adjacent_references method."""
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1")
    xml_processor = MockXMLProcessor()

    adjacent_refs = urn.get_adjacent_references(xml_processor)
    assert adjacent_refs == {"prev": None, "next": "1.2"}

    # Test with different reference
    urn = URN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.2")
    adjacent_refs = urn.get_adjacent_references(xml_processor)
    assert adjacent_refs == {"prev": "1.1", "next": "1.3"}
