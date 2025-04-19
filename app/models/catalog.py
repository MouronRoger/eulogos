"""Pydantic models for catalog data."""

from typing import Any, ClassVar, Dict, List, Optional
import uuid

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Author(BaseModel):
    """Author model."""

    name: str
    century: int  # Negative for BCE, positive for CE
    type: str
    id: Optional[str] = None  # Author ID (typically the textgroup)

    def __str__(self) -> str:
        """String representation of the author."""
        century_abs = abs(self.century)
        era = "BCE" if self.century < 0 else "CE"
        return f"{self.name} ({century_abs}th century {era})"


class Text:
    """Model for a text in the catalog."""

    def __init__(
        self,
        id: str,  # Keep id as the primary parameter for backward compatibility
        group_name: str,
        work_name: str,
        language: str,
        wordcount: int,
        author_id: str,
        path: str,  # Path is required - there is no text without a path
        archived: bool = False,
        favorite: bool = False,
    ):
        """Initialize a text.

        Args:
            id: The stable ID of the text (should be equal to path)
            group_name: The name of the text group
            work_name: The name of the work
            language: The language of the text
            wordcount: The word count of the text
            author_id: The ID of the author
            path: The path to the text file from catalog (required)
            archived: Whether the text is archived
            favorite: Whether the text is favorited
        """
        self.id = id  # Keep id as is for backward compatibility
        self.group_name = group_name
        self.work_name = work_name
        self.language = language
        self.wordcount = wordcount
        self.author_id = author_id
        self.path = path
        self.archived = archived
        self.favorite = favorite

    @classmethod
    def from_dict(cls, values: Dict[str, Any]) -> "Text":
        """Create a text from a dictionary.

        Args:
            values: Dictionary of values

        Returns:
            A Text object

        Raises:
            ValueError: If no path is provided
        """
        # Path is required - there is no text without a path
        if "path" not in values or not values["path"]:
            raise ValueError("Path is required for a Text object - there is no text without a path")
        
        # Use path as ID - this is the key change
        text_id = values["path"]
            
        return cls(
            id=text_id,  # Set id equal to path
            group_name=values["group_name"],
            work_name=values["work_name"],
            language=values["language"],
            wordcount=values["wordcount"],
            author_id=values["author_id"],
            path=values["path"],  # Path is required
            archived=values.get("archived", False),
            favorite=values.get("favorite", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert text to dictionary.

        Returns:
            Dictionary representation of the text
        """
        return {
            "id": self.id,
            "group_name": self.group_name,
            "work_name": self.work_name,
            "language": self.language,
            "wordcount": self.wordcount,
            "author_id": self.author_id,
            "path": self.path,  # Path is required and defines the text
            "archived": self.archived,
            "favorite": self.favorite,
        }
        
    def __str__(self) -> str:
        """String representation of the text."""
        return f"{self.group_name}: {self.work_name} ({self.language})"


class CatalogStatistics(BaseModel):
    """Statistics about the catalog."""

    author_count: int = 0
    text_count: int = 0
    work_count: int = 0
    greek_word_count: int = 0
    latin_word_count: int = 0
    arabic_word_count: int = 0


class UnifiedCatalog(BaseModel):
    """Unified catalog model combining author and text data."""

    model_config = {"arbitrary_types_allowed": True}
    
    statistics: CatalogStatistics
    authors: Dict[str, Author]
    catalog: List[Text]
