"""Pydantic models for XML document representation.

These models provide a structured representation of XML documents,
with support for references and caching.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class XMLReference(BaseModel):
    """A reference to a section in an XML document."""

    reference: str
    element: Any  # ElementTree element
    text_content: Optional[str] = None
    parent_ref: Optional[str] = None
    child_refs: List[str] = []

    class Config:
        """Configure model behavior."""

        arbitrary_types_allowed = True


class XMLDocument(BaseModel):
    """A parsed XML document with references."""

    file_path: str
    urn: str
    root_element: Any  # ElementTree root element
    references: Dict[str, XMLReference] = {}
    metadata: Dict[str, Any] = {}

    # Cache information
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0
    file_mtime: float = Field(default=0.0, description="File modification time (mtime) when document was loaded")
    cache_valid: bool = Field(default=True, description="Whether the cached document is still valid")
    cache_size: int = Field(default=0, description="Approximate memory size of the document in bytes")

    class Config:
        """Configure model behavior."""

        arbitrary_types_allowed = True

    def validate_cache(self, current_mtime: float) -> bool:
        """Check if the cached document is still valid.

        Args:
            current_mtime: Current modification time of the file

        Returns:
            bool: Whether the cache is still valid
        """
        # Update cache validity based on file modification time
        self.cache_valid = self.file_mtime == current_mtime
        return self.cache_valid

    def update_cache_metadata(self, mtime: float) -> None:
        """Update cache metadata when document is loaded.

        Args:
            mtime: Current modification time of the file
        """
        self.file_mtime = mtime
        self.cache_valid = True
        self.last_accessed = datetime.utcnow()
        # Rough estimate of memory size based on text content
        self.cache_size = sum(len(ref.text_content or "") for ref in self.references.values()) + len(str(self.metadata))
