"""Enhanced URN model and utilities.

This module provides functionality for handling and validating URNs in the system.
"""

from pathlib import Path
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class EnhancedURN(BaseModel):
    """Enhanced model for Canonical Text Services URNs."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    value: str
    namespace: Optional[str] = None
    textgroup: Optional[str] = None
    work: Optional[str] = None
    version: Optional[str] = None
    reference: Optional[str] = None

    @field_validator("value")
    def validate_urn(cls, v: str) -> str:
        """Validate the URN string format."""
        if not v.startswith("urn:cts:"):
            raise ValueError(f"Invalid CTS URN format: {v}")
        return v

    def __init__(self, **data: Any) -> None:
        """Initialize and parse the URN components."""
        super().__init__(**data)
        # Need to modify protected fields after init due to frozen model
        object.__setattr__(self, "namespace", None)
        object.__setattr__(self, "textgroup", None)
        object.__setattr__(self, "work", None)
        object.__setattr__(self, "version", None)
        object.__setattr__(self, "reference", None)
        self._parse()

    def _parse(self) -> None:
        """Parse the URN string into components."""
        urn = self.value.split("#")[0]
        parts = urn.split(":")

        if len(parts) >= 3:
            object.__setattr__(self, "namespace", parts[2])

        if len(parts) >= 4:
            id_part = parts[3].split(":", 1)
            identifier = id_part[0]

            if len(id_part) > 1:
                object.__setattr__(self, "reference", id_part[1])

            id_parts = identifier.split(".")
            if len(id_parts) >= 1:
                object.__setattr__(self, "textgroup", id_parts[0])
            if len(id_parts) >= 2:
                object.__setattr__(self, "work", id_parts[1])
            if len(id_parts) >= 3:
                object.__setattr__(self, "version", id_parts[2])

        if len(parts) >= 5:
            object.__setattr__(self, "reference", parts[4])

    def get_id_components(self) -> Dict[str, Optional[str]]:
        """Get the ID components of the URN."""
        return {
            "namespace": self.namespace,
            "textgroup": self.textgroup,
            "work": self.work,
            "version": self.version,
            "reference": self.reference,
        }

    def is_valid_for_path(self) -> bool:
        """Check if the URN has all components needed for path resolution."""
        return bool(self.textgroup and self.work and self.version)

    def get_file_path(self, base_dir: str = "data") -> Path:
        """Derive file path from URN components."""
        if not self.is_valid_for_path():
            raise ValueError(f"URN missing components needed for path: {self.value}")

        # Compatibility with existing structure: don't include namespace in path
        return Path(base_dir) / f"{self.textgroup}/{self.work}/{self.textgroup}.{self.work}.{self.version}.xml"

    @classmethod
    def from_original(cls, original_urn: Any) -> "EnhancedURN":
        """Convert from original URN model."""
        if hasattr(original_urn, "value"):
            # It's already a Pydantic model
            return cls(value=original_urn.value)
        elif hasattr(original_urn, "urn_string"):
            # It's a CtsUrn
            return cls(value=original_urn.urn_string)
        else:
            # Assume it's a string
            return cls(value=str(original_urn))

    def to_original_urn(self, original_class: Any) -> Any:
        """Convert to original URN model if needed."""
        if hasattr(original_class, "value"):
            # It's a Pydantic model
            return original_class(value=self.value)
        elif hasattr(original_class, "urn_string"):
            # It's the old CtsUrn
            return original_class(self.value)
        else:
            # Try to instantiate with the value
            try:
                return original_class(self.value)
            except Exception:
                # Return self as fallback
                return self

    def __eq__(self, other: object) -> bool:
        """Compare URNs by value."""
        if isinstance(other, EnhancedURN):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        """Make URN hashable by using the value string."""
        return hash(self.value)
