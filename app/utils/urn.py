"""Utility functions for working with CTS URNs."""

import warnings
from pathlib import Path
from typing import Optional, Tuple


class CtsUrn:
    """Utility class for CTS URN parsing and manipulation.

    Note:
        This class is deprecated. Use the URN model from app.models.urn instead.
    """

    def __init__(self, urn_string: str):
        """Initialize a CtsUrn object.

        Args:
            urn_string: The CTS URN string

        Raises:
            ValueError: If the URN is invalid
        """
        warnings.warn(
            "CtsUrn is deprecated. Use the URN model from app.models.urn instead.", DeprecationWarning, stacklevel=2
        )
        self.urn_string = urn_string
        self.namespace, self.textgroup, self.work, self.version, self.passage = self._parse()

    def _parse(self) -> Tuple[str, str, str, str, Optional[str]]:
        """Parse URN into components.

        Returns:
            Tuple containing namespace, textgroup, work, version, and passage

        Raises:
            ValueError: If the URN is invalid
        """
        if not self.urn_string.startswith("urn:cts:"):
            raise ValueError(f"Invalid CTS URN: {self.urn_string}")

        parts = self.urn_string.split(":")
        if len(parts) < 4:
            raise ValueError(f"Incomplete CTS URN: {self.urn_string}")

        namespace = parts[2]

        # Handle passage reference if present
        work_parts = parts[3].split(":")
        identifier = work_parts[0]
        passage = work_parts[1] if len(work_parts) > 1 else None

        # Parse text identifier
        id_parts = identifier.split(".")
        if len(id_parts) < 2:
            raise ValueError(f"Invalid text identifier in URN: {identifier}")

        textgroup = id_parts[0]
        work = id_parts[1] if len(id_parts) > 1 else ""
        version = id_parts[2] if len(id_parts) > 2 else ""

        return namespace, textgroup, work, version, passage

    def get_file_path(self, base_dir: str = "data") -> Path:
        """Derive file path from CTS URN.

        Args:
            base_dir: Base directory for the data files

        Returns:
            Path object for the file

        Raises:
            ValueError: If the URN doesn't contain version information
        """
        if not self.version:
            raise ValueError("Cannot derive file path without version information")

        return (
            Path(base_dir)
            / self.namespace
            / self.textgroup
            / self.work
            / f"{self.textgroup}.{self.work}.{self.version}.xml"
        )

    def get_textgroup_urn(self) -> str:
        """Get URN for the textgroup level.

        Returns:
            URN string for the textgroup
        """
        return f"urn:cts:{self.namespace}:{self.textgroup}"

    def get_work_urn(self) -> str:
        """Get URN for the work level.

        Returns:
            URN string for the work
        """
        return f"urn:cts:{self.namespace}:{self.textgroup}.{self.work}"

    def get_version_urn(self) -> str:
        """Get URN for the version level without passage.

        Returns:
            URN string for the version
        """
        return f"urn:cts:{self.namespace}:{self.textgroup}.{self.work}.{self.version}"

    def __str__(self) -> str:
        """Get string representation of the URN.

        Returns:
            The original URN string
        """
        return self.urn_string
