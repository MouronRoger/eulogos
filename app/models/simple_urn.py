"""Simple URN validation and parsing utility for Eulogos."""

from pathlib import Path
from typing import Dict, Optional


class SimpleURN:
    """Simple URN validator and parser without complex abstractions."""

    def __init__(self, value: str):
        """Initialize with a URN string and validate its format.

        Args:
            value: The URN string to validate and parse

        Raises:
            ValueError: If the URN format is invalid
        """
        self.value = value

        # Validate basic URN format
        if not value.startswith("urn:cts:"):
            raise ValueError(f"Invalid URN format: {value}. Must start with 'urn:cts:'")

        # Parse components
        self.namespace: Optional[str] = None
        self.textgroup: Optional[str] = None
        self.work: Optional[str] = None
        self.version: Optional[str] = None
        self.reference: Optional[str] = None

        self._parse()

    def _parse(self) -> None:
        """Parse the URN string into components."""
        # Remove reference part with # if present
        urn = self.value.split("#")[0]
        parts = urn.split(":")

        # Parse namespace
        if len(parts) >= 3:
            self.namespace = parts[2]

        # Parse textgroup, work, version
        if len(parts) >= 4:
            id_part = parts[3].split(":", 1)
            identifier = id_part[0]

            # Parse reference if present in this format
            if len(id_part) > 1:
                self.reference = id_part[1]

            # Parse textgroup.work.version
            id_parts = identifier.split(".")
            if len(id_parts) >= 1:
                self.textgroup = id_parts[0]
            if len(id_parts) >= 2:
                self.work = id_parts[1]
            if len(id_parts) >= 3:
                self.version = id_parts[2]

        # Parse reference if it's in the format urn:cts:namespace:id:reference
        if len(parts) >= 5:
            self.reference = parts[4]

    def get_components(self) -> Dict[str, Optional[str]]:
        """Get the URN components.

        Returns:
            Dictionary with URN components
        """
        return {
            "namespace": self.namespace,
            "textgroup": self.textgroup,
            "work": self.work,
            "version": self.version,
            "reference": self.reference,
        }

    def is_valid_for_path(self) -> bool:
        """Check if the URN has all components needed for path resolution.

        Returns:
            True if all required components are present
        """
        return bool(self.textgroup and self.work and self.version)

    def get_file_path(self, base_dir: str = "data") -> Path:
        """Derive file path from URN components.

        Args:
            base_dir: Base directory for the data files

        Returns:
            Path object for the file

        Raises:
            ValueError: If URN doesn't have required components
        """
        if not self.is_valid_for_path():
            raise ValueError(f"URN missing components needed for path: {self.value}")

        # Standard path format: data/textgroup/work/textgroup.work.version.xml
        return Path(base_dir) / self.textgroup / self.work / f"{self.textgroup}.{self.work}.{self.version}.xml"

    @classmethod
    def from_string(cls, urn: str) -> "SimpleURN":
        """Create a SimpleURN instance from a string.

        Args:
            urn: URN string

        Returns:
            SimpleURN instance
        """
        return cls(value=urn)

    def __str__(self) -> str:
        """Get string representation.

        Returns:
            The original URN string
        """
        return self.value
