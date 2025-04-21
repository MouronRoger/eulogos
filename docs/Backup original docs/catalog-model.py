"""Catalog models for Eulogos application.

This module defines the data models for the catalog system, using file paths
as the canonical identifiers for texts.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Text(BaseModel):
    """Model for a text entry in the catalog.
    
    The path field serves as both the unique identifier and the relative
    file path to the XML file from the data directory.
    """
    
    path: str = Field(..., description="Relative path to the XML file (canonical ID)")
    title: str = Field(..., description="Title of the text")
    author: str = Field(..., description="Author of the text")
    language: str = Field(default="unknown", description="Language of the text")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")
    favorite: bool = Field(default=False, description="Whether the text is favorited")
    archived: bool = Field(default=False, description="Whether the text is archived")
    
    def __str__(self) -> str:
        """String representation of the text."""
        return f"{self.title} by {self.author} ({self.language})"


class Statistics(BaseModel):
    """Model for catalog statistics."""
    
    total_texts: int = Field(default=0, description="Total number of texts")
    languages: Dict[str, int] = Field(
        default_factory=dict, 
        description="Count of texts by language"
    )
    
    def __str__(self) -> str:
        """String representation of statistics."""
        return f"{self.total_texts} texts in {len(self.languages)} languages"


class Catalog(BaseModel):
    """Main catalog model containing all texts and statistics."""
    
    texts: List[Text] = Field(default_factory=list, description="List of all texts")
    statistics: Statistics = Field(
        default_factory=Statistics, 
        description="Catalog statistics"
    )
    
    def get_text_by_path(self, path: str) -> Optional[Text]:
        """Get a text by its path.
        
        Args:
            path: The path to the text
            
        Returns:
            The text if found, None otherwise
        """
        for text in self.texts:
            if text.path == path:
                return text
        return None
    
    def get_texts_by_author(self, author: str) -> List[Text]:
        """Get all texts by a specific author.
        
        Args:
            author: The author name
            
        Returns:
            List of texts by the author
        """
        return [text for text in self.texts if text.author == author]
    
    def get_texts_by_language(self, language: str) -> List[Text]:
        """Get all texts in a specific language.
        
        Args:
            language: The language code
            
        Returns:
            List of texts in the language
        """
        return [text for text in self.texts if text.language == language]
    
    def get_unique_authors(self) -> List[str]:
        """Get a list of all unique authors.
        
        Returns:
            List of author names
        """
        authors = set(text.author for text in self.texts)
        return sorted(authors)
    
    def get_unique_languages(self) -> List[str]:
        """Get a list of all unique languages.
        
        Returns:
            List of language codes
        """
        languages = set(text.language for text in self.texts)
        return sorted(languages)
    
    def toggle_favorite(self, path: str) -> bool:
        """Toggle the favorite status of a text.
        
        Args:
            path: The path to the text
            
        Returns:
            True if successful, False if the text was not found
        """
        text = self.get_text_by_path(path)
        if text:
            text.favorite = not text.favorite
            return True
        return False
    
    def set_archived(self, path: str, archived: bool = True) -> bool:
        """Set the archived status of a text.
        
        Args:
            path: The path to the text
            archived: Whether to archive or unarchive
            
        Returns:
            True if successful, False if the text was not found
        """
        text = self.get_text_by_path(path)
        if text:
            text.archived = archived
            return True
        return False
    
    def __str__(self) -> str:
        """String representation of the catalog."""
        return f"Catalog with {len(self.texts)} texts"
