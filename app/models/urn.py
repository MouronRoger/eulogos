"""Pydantic model for Canonical Text Services URNs.

Provides enhanced functionality for parsing, manipulating and navigating CTS URNs.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, validator


class URN(BaseModel):
    """
    Model for Canonical Text Services URNs.

    Example: urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7
    """

    value: str
    urn_namespace: Optional[str] = None
    cts_namespace: Optional[str] = None
    text_group: Optional[str] = None
    work: Optional[str] = None
    version: Optional[str] = None
    reference: Optional[str] = None

    class Config:
        """Configure model behavior."""

        validate_assignment = True

    @validator("value")
    def validate_urn(cls, v: str) -> str:
        """Validate the URN string format."""
        if not v.startswith("urn:cts:"):
            raise ValueError(f"Invalid CTS URN format: {v}")
        return v

    def __init__(self, **data: Any) -> None:
        """Initialize and parse the URN components."""
        super().__init__(**data)
        self.parse()

    def parse(self) -> None:
        """Parse the URN string into components."""
        urn = self.value.split("#")[0]
        parts = urn.split(":")

        if len(parts) >= 3:
            self.urn_namespace = parts[0]
            self.cts_namespace = parts[1]

        if len(parts) >= 4:
            self.cts_namespace = parts[2]

            # Handle possible reference part
            id_ref = parts[3].split(":")
            identifier = id_ref[0]

            if len(id_ref) > 1:
                self.reference = id_ref[1]

            # Parse identifier
            id_parts = identifier.split(".")
            if len(id_parts) >= 1:
                self.text_group = id_parts[0]
            if len(id_parts) >= 2:
                self.work = id_parts[1]
            if len(id_parts) >= 3:
                self.version = id_parts[2]

    def up_to(self, level: str) -> str:
        """
        Return URN up to specified level.

        Args:
            level: One of 'urn_namespace', 'cts_namespace', 'text_group',
                  'work', 'version', 'reference'

        Returns:
            String URN truncated at specified level
        """
        if level not in ["urn_namespace", "cts_namespace", "text_group", "work", "version", "reference"]:
            raise ValueError(f"Invalid URN level: {level}")

        parts = ["urn"]

        if (
            level in ["urn_namespace", "cts_namespace", "text_group", "work", "version", "reference"]
            and self.urn_namespace
        ):
            parts.append(self.urn_namespace)

        if level in ["cts_namespace", "text_group", "work", "version", "reference"] and self.cts_namespace:
            parts.append(self.cts_namespace)

        if level in ["text_group", "work", "version", "reference"] and self.text_group:
            parts.append(self.text_group)

        if level in ["work", "version", "reference"] and self.work:
            parts.append(f"{self.text_group}.{self.work}")

        if level in ["version", "reference"] and self.version:
            parts.append(f"{self.text_group}.{self.work}.{self.version}")

        if level == "reference" and self.reference:
            parts.append(self.reference)

        return ":".join(parts)

    def replace(self, **kwargs: Dict[str, Any]) -> "URN":
        """
        Create a new URN with replaced components.

        Args:
            **kwargs: Components to replace, e.g., reference='1.1'

        Returns:
            New URN instance with replaced components
        """
        data = self.dict()
        data.update(kwargs)

        # Keep the original value, will be reconstructed in new instance
        new_urn = URN(value=self.value)

        for key, val in kwargs.items():
            setattr(new_urn, key, val)

        # Reconstruct the URN string from components
        parts = ["urn"]

        if new_urn.urn_namespace:
            parts.append(new_urn.urn_namespace)

        if new_urn.cts_namespace:
            parts.append(new_urn.cts_namespace)

        # Build identifier part
        id_parts = []
        if new_urn.text_group:
            id_parts.append(new_urn.text_group)
        if new_urn.work:
            id_parts.append(new_urn.work)
        if new_urn.version:
            id_parts.append(new_urn.version)

        if id_parts:
            parts.append(".".join(id_parts))

        if new_urn.reference:
            parts.append(new_urn.reference)

        new_urn.value = ":".join(parts)
        return new_urn

    def get_file_path(self, base_dir: str = "data") -> Path:
        """
        Get file path corresponding to this URN.

        Args:
            base_dir: Base directory for data files

        Returns:
            Path object for the XML file

        Raises:
            ValueError: If URN has insufficient components for path
        """
        if not self.text_group or not self.work or not self.version:
            raise ValueError(f"URN missing components needed for file path: {self.value}")

        return (
            Path(base_dir)
            / self.cts_namespace
            / self.text_group
            / self.work
            / f"{self.text_group}.{self.work}.{self.version}.xml"
        )

    def get_adjacent_references(self, xml_processor: Any) -> Dict[str, Optional[str]]:
        """
        Get previous and next references relative to current.

        Args:
            xml_processor: XMLProcessorService to use for reference lookup

        Returns:
            Dictionary with 'prev' and 'next' references
        """
        xml_root = xml_processor.load_xml(self)
        return xml_processor.get_adjacent_references(xml_root, self.reference)
