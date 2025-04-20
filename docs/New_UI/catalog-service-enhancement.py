"""Catalog service enhancements for Eulogos application.

This module extends the CatalogService with methods to support hierarchical
organization of texts by author and work, while maintaining the canonical
path-based reference system.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Any

from loguru import logger

from app.models.catalog import Catalog, Text


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
        self._eras: List[str] = []
        self._centuries: List[str] = []
        self._author_types: List[str] = []
        
        # Load catalog on initialization
        self.load_catalog()
        
    def _transform_hierarchical_to_flat(self, hierarchical_data: Dict[str, Any]) -> List[Text]:
        """Transform hierarchical catalog data to flat list of Text objects.
        
        Args:
            hierarchical_data: Hierarchical catalog data from integrated_catalog.json
            
        Returns:
            List of Text objects
        """
        texts: List[Text] = []
        
        # Process each author
        for author_id, author_data in hierarchical_data.items():
            author_name = author_data.get("name", author_id)
            
            # Extract author metadata
            century = author_data.get("century", "Unknown")
            era = author_data.get("era", "Unknown")
            author_type = author_data.get("type", "Unknown")
            
            # Process each work
            for work_id, work_data in author_data.get("works", {}).items():
                work_title = work_data.get("title", work_id)
                work_language = work_data.get("language", "unknown")
                
                # Process editions
                for edition_id, edition_data in work_data.get("editions", {}).items():
                    path = edition_data.get("path")
                    if not path:
                        continue
                        
                    # Create metadata dictionary with author metadata
                    metadata = {
                        "urn": edition_data.get("urn"),
                        "label": edition_data.get("label"),
                        "description": edition_data.get("description"),
                        "editor": edition_data.get("editor"),
                        "work_id": work_id,
                        "author_id": author_id,
                        "edition_id": edition_id,
                        "author_metadata": {
                            "century": century,
                            "era": era,
                            "type": author_type
                        }
                    }
                    
                    # Create Text object
                    text = Text(
                        path=path,
                        title=edition_data.get("label", work_title),
                        author=author_name,
                        language=edition_data.get("language", work_language),
                        metadata=metadata,
                        favorite=False,
                        archived=False
                    )
                    
                    texts.append(text)
                
                # Process translations
                for translation_id, translation_data in work_data.get("translations", {}).items():
                    path = translation_data.get("path")
                    if not path:
                        continue
                        
                    # Create metadata dictionary with author metadata
                    metadata = {
                        "urn": translation_data.get("urn"),
                        "label": translation_data.get("label"),
                        "description": translation_data.get("description"),
                        "translator": translation_data.get("translator"),
                        "work_id": work_id,
                        "author_id": author_id,
                        "translation_id": translation_id,
                        "author_metadata": {
                            "century": century,
                            "era": era,
                            "type": author_type
                        }
                    }
                    
                    # Create Text object
                    text = Text(
                        path=path,
                        title=translation_data.get("label", work_title),
                        author=author_name,
                        language=translation_data.get("language", "unknown"),
                        metadata=metadata,
                        favorite=False,
                        archived=False
                    )
                    
                    texts.append(text)
        
        return texts
        
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
                hierarchical_data = json.load(f)
            
            # Transform hierarchical data to flat list
            texts = self._transform_hierarchical_to_flat(hierarchical_data)
            
            # Create Catalog object
            self._catalog = Catalog(texts=texts)
            
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
        
        # Build filter lists from metadata
        eras = set()
        centuries = set()
        author_types = set()
        
        for text in self._catalog.texts:
            author_metadata = text.metadata.get("author_metadata", {})
            
            era = author_metadata.get("era")
            if era and era != "Unknown":
                eras.add(era)
                
            century = author_metadata.get("century")
            if century and century != "Unknown":
                centuries.add(century)
                
            author_type = author_metadata.get("type")
            if author_type and author_type != "Unknown":
                author_types.add(author_type)
        
        self._eras = sorted(eras)
        self._centuries = sorted(centuries)
        self._author_types = sorted(author_types)
        
        logger.debug(f"Built indexes with {len(self._texts_by_path)} texts, "
                   f"{len(self._authors)} authors, {len(self._languages)} languages, "
                   f"{len(self._eras)} eras, {len(self._centuries)} centuries, "
                   f"{len(self._author_types)} author types")
    
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
                json.dump(self._catalog.model_dump(), f, indent=2, ensure_ascii=False)
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
    
    def get_hierarchical_texts(self, include_archived: bool = False) -> Dict[str, Dict]:
        """Get texts organized hierarchically by author.
        
        Args:
            include_archived: Whether to include archived texts
            
        Returns:
            Dictionary of authors with their texts organized by work
        """
        if not self._catalog:
            return {}
        
        # Filter texts
        texts = self._catalog.texts if include_archived else [
            text for text in self._catalog.texts if not text.archived
        ]
        
        # Build hierarchical structure
        hierarchical = {}
        
        for text in texts:
            # Extract work identifier from path or metadata
            work_id = text.metadata.get("work_id", "unknown")
            
            # Ensure author exists in hierarchical structure
            if text.author not in hierarchical:
                # Extract author metadata
                author_metadata = text.metadata.get("author_metadata", {})
                century = author_metadata.get("century", "Unknown")
                era = author_metadata.get("era", "Unknown")
                author_type = author_metadata.get("type", "Unknown")
                
                hierarchical[text.author] = {
                    "metadata": {
                        "century": century,
                        "era": era,
                        "type": author_type
                    },
                    "works": {}
                }
            
            # Ensure work exists for this author
            if work_id not in hierarchical[text.author]["works"]:
                # Get work title from the first text of this work
                hierarchical[text.author]["works"][work_id] = {
                    "title": text.title,  # Will be overridden by edition title if needed
                    "texts": []
                }
            
            # Add text to work
            hierarchical[text.author]["works"][work_id]["texts"].append(text)
        
        return hierarchical
    
    def get_filtered_hierarchical_texts(
        self, 
        era: Optional[str] = None,
        century: Optional[str] = None,
        author_type: Optional[str] = None,
        query: Optional[str] = None,
        author_query: Optional[str] = None,
        show_favorites: bool = False,
        include_archived: bool = False
    ) -> Dict[str, Dict]:
        """Get filtered texts organized hierarchically by author.
        
        Args:
            era: Optional era filter
            century: Optional century filter
            author_type: Optional author type filter
            query: Optional search query for text titles
            author_query: Optional search query for author names
            show_favorites: Whether to show only favorite texts
            include_archived: Whether to include archived texts
            
        Returns:
            Dictionary of authors with their texts organized by work
        """
        if not self._catalog:
            return {}
        
        # Start with all texts
        texts = self._catalog.texts
        
        # Apply global filters
        if not include_archived:
            texts = [text for text in texts if not text.archived]
        
        if show_favorites:
            texts = [text for text in texts if text.favorite]
        
        # Build hierarchical structure with filtering
        hierarchical = {}
        
        for text in texts:
            # Get author metadata for filtering
            author_metadata = text.metadata.get("author_metadata", {})
            text_century = author_metadata.get("century")
            text_era = author_metadata.get("era")
            text_author_type = author_metadata.get("type")
            
            # Apply metadata filters
            if era and text_era != era:
                continue
                
            if century and text_century != century:
                continue
                
            if author_type and text_author_type != author_type:
                continue
            
            # Apply text title search filter
            if query and query.lower() not in text.title.lower():
                continue
            
            # Apply author name search filter
            if author_query and author_query.lower() not in text.author.lower():
                continue
            
            # Extract work identifier from metadata
            work_id = text.metadata.get("work_id", "unknown")
            
            # Ensure author exists in hierarchical structure
            if text.author not in hierarchical:
                hierarchical[text.author] = {
                    "metadata": {
                        "century": text_century or "Unknown",
                        "era": text_era or "Unknown",
                        "type": text_author_type or "Unknown"
                    },
                    "works": {}
                }
            
            # Ensure work exists for this author
            if work_id not in hierarchical[text.author]["works"]:
                hierarchical[text.author]["works"][work_id] = {
                    "title": text.title,
                    "texts": []
                }
            
            # Add text to work
            hierarchical[text.author]["works"][work_id]["texts"].append(text)
        
        return hierarchical
    
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
    
    def get_all_eras(self) -> List[str]:
        """Get all unique eras.
        
        Returns:
            List of era names
        """
        return self._eras
    
    def get_all_centuries(self) -> List[str]:
        """Get all unique centuries.
        
        Returns:
            List of centuries
        """
        return self._centuries
    
    def get_all_author_types(self) -> List[str]:
        """Get all unique author types.
        
        Returns:
            List of author types
        """
        return self._author_types
    
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
    
    def search_texts_by_title(self, query: str, include_archived: bool = False) -> List[Text]:
        """Search for texts by title only.
        
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
            if query in text.title.lower()
            and (include_archived or not text.archived)
        ]
    
    def search_authors(self, query: str) -> List[str]:
        """Search for authors by name.
        
        Args:
            query: The search query
            
        Returns:
            List of matching author names
        """
        if not self._catalog or not query:
            return []
        
        query = query.lower()
        
        return sorted(set(
            text.author for text in self._catalog.texts 
            if query in text.author.lower()
        ))
    
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


@lru_cache(maxsize=1)
def get_catalog_service() -> CatalogService:
    """Get a singleton instance of the catalog service.
    
    Returns:
        Catalog service instance
    """
    return CatalogService()
