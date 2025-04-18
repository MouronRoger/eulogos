"""Pydantic models for catalog data."""

from typing import ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Author(BaseModel):
    """Author model."""

    name: str
    century: int  # Negative for BCE, positive for CE
    type: str
    id: Optional[str] = None  # Author ID (typically the textgroup)


class Text:
    """Model for a text in the catalog."""

    def __init__(
        self,
        urn: str,
        group_name: str,
        work_name: str,
        language: str,
        wordcount: int,
        author_id: str,
        path: Optional[str] = None,
        archived: bool = False,
        favorite: bool = False,
    ):
        """Initialize a text.

        Args:
            urn: The URN of the text
            group_name: The name of the text group
            work_name: The name of the work
            language: The language of the text
            wordcount: The word count of the text
            author_id: The ID of the author
            path: The path to the text file from catalog
            archived: Whether the text is archived
            favorite: Whether the text is favorited
        """
        self.urn = urn
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
        """
        # Path must come from catalog
        if "path" not in values:
            logger.warning(f"No path provided in catalog for text {values.get('urn', 'unknown')}")

        return cls(
            urn=values["urn"],
            group_name=values["group_name"],
            work_name=values["work_name"],
            language=values["language"],
            wordcount=values["wordcount"],
            author_id=values["author_id"],
            path=values.get("path"),  # Path must come from catalog
            archived=values.get("archived", False),
            favorite=values.get("favorite", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert text to dictionary.

        Returns:
            Dictionary representation of the text
        """
        return {
            "urn": self.urn,
            "group_name": self.group_name,
            "work_name": self.work_name,
            "language": self.language,
            "wordcount": self.wordcount,
            "author_id": self.author_id,
            "path": self.path,  # Path from catalog
            "archived": self.archived,
            "favorite": self.favorite,
        }


class CatalogStatistics(BaseModel):
    """Statistics about the catalog."""

    nodeCount: int = 0
    greekWords: int = 0
    latinWords: int = 0
    arabicwords: int = 0
    authorCount: int = 0
    textCount: int = 0


class UnifiedCatalog(BaseModel):
    """Unified catalog model combining author and text data."""

    statistics: CatalogStatistics
    authors: Dict[str, Author]
    catalog: List[Text]
