"""Pydantic models for enhanced catalog data.

These models provide a comprehensive representation of the catalog data,
with support for editions, translations, and enhanced metadata.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ModelVersion(BaseModel):
    """Version information for models."""

    version: str = "1.0.0"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class TextVersion(BaseModel):
    """A version of a text (edition or translation)."""

    urn: str
    label: str
    description: Optional[str] = None
    language: str
    path: Optional[str] = None
    word_count: int = 0
    editor: Optional[str] = None
    translator: Optional[str] = None
    archived: bool = False  # Maintain compatibility with existing feature
    favorite: bool = False  # Maintain compatibility with existing feature

    # Methods to convert between old and new models
    @classmethod
    def from_original(cls, original_model: Any) -> "TextVersion":
        """Convert from original model to new model."""
        return cls(
            urn=original_model.urn,
            label=getattr(original_model, "label", getattr(original_model, "work_name", "")),
            description=getattr(original_model, "description", None),
            language=getattr(original_model, "language", ""),
            path=getattr(original_model, "path", None),
            word_count=getattr(original_model, "wordcount", 0),
            editor=getattr(original_model, "editor", None),
            translator=getattr(original_model, "translator", None),
            archived=getattr(original_model, "archived", False),
            favorite=getattr(original_model, "favorite", False),
        )

    def to_original(self, original_class: Any) -> Any:
        """Convert to original model."""
        return original_class(
            urn=self.urn,
            group_name=getattr(self, "group_name", ""),
            work_name=getattr(self, "label", ""),
            language=self.language,
            wordcount=self.word_count,
            path=self.path,
            archived=self.archived,
            favorite=self.favorite,
        )


class Work(BaseModel):
    """A work with editions and translations."""

    id: str  # Work ID (e.g., tlg001)
    title: str
    urn: str
    language: str
    editions: Dict[str, TextVersion] = {}
    translations: Dict[str, TextVersion] = {}
    archived: bool = False


class Author(BaseModel):
    """An author with works."""

    id: str  # Author ID (e.g., tlg0004)
    name: str
    century: Optional[int] = None
    type: Optional[str] = None
    works: Dict[str, Work] = {}
    archived: bool = False


class CatalogStatistics(BaseModel):
    """Statistics about the catalog."""

    author_count: int = 0
    work_count: int = 0
    edition_count: int = 0
    translation_count: int = 0
    greek_word_count: int = 0
    latin_word_count: int = 0
    arabic_word_count: int = 0


class Catalog(BaseModel):
    """The integrated catalog."""

    statistics: CatalogStatistics = Field(default_factory=CatalogStatistics)
    authors: Dict[str, Author] = {}

    model_version: ModelVersion = Field(default_factory=ModelVersion)
