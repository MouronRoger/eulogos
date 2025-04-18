"""CTS URN data model and parser.

This simplified implementation provides basic URN parsing functionality.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class URN:
    """Model for a CTS URN.

    Attributes:
        value: The full URN string
        textgroup: The textgroup identifier (e.g., tlg0532)
        work: The work identifier (e.g., tlg001)
        version: The version identifier (e.g., perseus-grc2)
    """

    value: str
    textgroup: Optional[str] = None
    work: Optional[str] = None
    version: Optional[str] = None

    def __post_init__(self):
        """Process URN string into components.

        This is a simplified parser that extracts just the components we need.
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
