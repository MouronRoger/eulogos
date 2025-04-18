"""CTS URN data model and parser for textual references only.

This simplified implementation provides basic URN parsing for textual references.
URNs in Eulogos are only used as textual references, not for path resolution.
All path resolution must use the integrated_catalog.json as the single source of truth.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class URN:
    """Model for a CTS URN textual reference.

    This class is for parsing URNs as textual references only. It does not provide
    any path resolution functionality. All path resolution must go through the catalog.

    Attributes:
        value: The full URN string
        textgroup: The textgroup identifier (e.g., tlg0532)
        work: The work identifier (e.g., tlg001)
        version: The version identifier (e.g., perseus-grc2)
        passage: Optional passage reference
    """

    value: str
    textgroup: Optional[str] = None
    work: Optional[str] = None
    version: Optional[str] = None
    passage: Optional[str] = None

    def __post_init__(self):
        """Process URN string into components.

        This is a simplified parser that extracts just the components we need
        for textual references. It does not provide path resolution.
        """
        try:
            # Parse basic URN structure
            if not self.value.startswith("urn:cts:"):
                return

            parts = self.value.split(":")
            if len(parts) < 4:
                return

            # Parse the identifier portion
            identifier = parts[3]

            # Check for passage reference
            if ":" in identifier:
                identifier, self.passage = identifier.split(":", 1)
            elif len(parts) > 4:
                self.passage = parts[4]

            # Parse the identifier components
            id_parts = identifier.split(".")

            if len(id_parts) >= 1:
                self.textgroup = id_parts[0]
            if len(id_parts) >= 2:
                self.work = id_parts[1]
            if len(id_parts) >= 3:
                self.version = id_parts[2]
        except Exception:
            # Fail silently and leave components as None
            pass

    def __str__(self) -> str:
        """Return the original URN value.

        Returns:
            str: The original URN value
        """
        return self.value
