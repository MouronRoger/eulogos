"""Catalog service for Eulogos application.

This service loads and manages the catalog data, providing access methods
that use file paths as canonical identifiers for texts.
"""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from app.models.catalog import Catalog, Text, Statistics


class CatalogService:
    """Service for accessing and managing the catalog data."""
    
    def __init__(self, catalog_path: str = "integrated_catalog.json"):
        """Initialize the catalog service.
        
        Args:
            catalog_path: Path to the catalog JSON file
        """
        self.catalog_path = Path(catalog_path)
        self._catalog: Optional[Catalog] = None
        self._texts_by_path: Dict[str, Text] = {}
        self._authors: List[str] = []
        self._languages: List[str] = []
        
        # Load catalog on initialization
        self.load_catalog()
        
    def load_catalog(self) -> Catalog:
        """Load the catalog from the JSON file.
        
        Returns:
            The loaded catalog
            
        Raises:
            FileNotFoundError: If the catalog file doesn't exist
            ValueError: If the catalog file isn't valid JSON
        """
        if not self.catalog_path.exists():
            logger.error(f"Catalog file not found: {self.catalog_path}")
            raise FileNotFoundError(f"Catalog file not found: {self.catalog_path}")
        
        try:
            logger.info(f"Loading catalog from {self.catalog_path}")
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Create Catalog object from JSON data
            self._catalog = Catalog.parse_obj(data)
            
            # Build lookup indexes
            self._build_indexes()
            
            logger.info(f"Loaded catalog with {len(self._catalog.texts)} texts")
            return self._catalog
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in catalog file: {e}")
            raise ValueError(f"Invalid JSON in catalog file: {e}")
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            raise
    
    def _build_indexes(self) -> None:
        """Build lookup indexes for efficient access."""
        if not self._catalog:
            return
        
        # Build text index by path
        self._texts_by_path = {text.path: text for text in self._catalog.texts}
        
        # Build author and language lists
        self._authors = sorted(set(text.author for text in self._catalog.texts))
        self._languages = sorted(set(text.language for text in self._catalog.texts))
        
        logger.debug(f"Built indexes with {len(self._texts_by_path)} texts, "
                   f"{len(self._authors)} authors, {len(self._languages)} languages")
    
    def save_catalog(self) -> bool:
        """Save the catalog to the JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._catalog:
            logger.error("No catalog to save")
            return False
        
        try:
            logger.info(f"Saving catalog to {self.catalog_path}")
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(self._catalog.dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving catalog: {e}")
            return False
    
    def get_all_texts(self, include_archived: bool = False) -> List[Text]:
        """Get all texts in the catalog.
        
        Args:
            include_archived: Whether to include archived texts
            
        Returns:
            List of all texts
        """
        if not self._catalog:
            return []
        
        if include_archived:
            return self._catalog.texts
        
        return [text for text in self._catalog.texts if not text.archived]
    
    def get_text_by_path(self, path: str) -> Optional[Text]:
        """Get a text by its path.
        
        Args:
            path: The path to the text
            
        Returns:
            The text if found, None otherwise
        """
        return self._texts_by_path.get(path)
    
    def get_texts_by_author(self, author: str, include_archived: bool = False) -> List[Text]:
        """Get all texts by a specific author.
        
        Args:
            author: The author name
            include_archived: Whether to include archived texts
            
        Returns:
            List of texts by the author
        """
        if not self._catalog:
            return []
        
        texts = [
            text for text in self._catalog.texts 
            if text.author == author and (include_archived or not text.archived)
        ]
        
        return texts
    
    def get_texts_by_language(self, language: str, include_archived: bool = False) -> List[Text]:
        """Get all texts in a specific language.
        
        Args:
            language: The language code
            include_archived: Whether to include archived texts
            
        Returns:
            List of texts in the language
        """
        if not self._catalog:
            return []
        
        texts = [
            text for text in self._catalog.texts 
            if text.language == language and (include_archived or not text.archived)
        ]
        
        return texts
    
    def get_favorite_texts(self) -> List[Text]:
        """Get all favorited texts.
        
        Returns:
            List of favorited texts
        """
        if not self._catalog:
            return []
        
        return [text for text in self._catalog.texts if text.favorite and not text.archived]
    
    def get_all_authors(self) -> List[str]:
        """Get all unique authors.
        
        Returns:
            List of author names
        """
        return self._authors
    
    def get_all_languages(self) -> List[str]:
        """Get all unique languages.
        
        Returns:
            List of language codes
        """
        return self._languages
    
    def search_texts(self, query: str, include_archived: bool = False) -> List[Text]:
        """Search for texts by title or author.
        
        Args:
            query: The search query
            include_archived: Whether to include archived texts
            
        Returns:
            List of matching texts
        """
        if not self._catalog or not query:
            return []
        
        query = query.lower()
        
        return [
            text for text in self._catalog.texts 
            if (query in text.title.lower() or query in text.author.lower())
            and (include_archived or not text.archived)
        ]
    
    def toggle_favorite(self, path: str) -> bool:
        """Toggle the favorite status of a text.
        
        Args:
            path: The path to the text
            
        Returns:
            True if successful, False if the text was not found
        """
        if not self._catalog:
            return False
        
        success = self._catalog.toggle_favorite(path)
        if success:
            self.save_catalog()
        return success
    
    def set_archived(self, path: str, archived: bool = True) -> bool:
        """Set the archived status of a text.
        
        Args:
            path: The path to the text
            archived: Whether to archive or unarchive
            
        Returns:
            True if successful, False if the text was not found
        """
        if not self._catalog:
            return False
        
        success = self._catalog.set_archived(path, archived)
        if success:
            self.save_catalog()
        return success
    
    def get_statistics(self) -> Statistics:
        """Get catalog statistics.
        
        Returns:
            Catalog statistics
        """
        if not self._catalog:
            return Statistics()
        
        return self._catalog.statistics


@lru_cache(maxsize=1)
def get_catalog_service() -> CatalogService:
    """Get a singleton instance of the catalog service.
    
    Returns:
        Catalog service instance
    """
    return CatalogService()
