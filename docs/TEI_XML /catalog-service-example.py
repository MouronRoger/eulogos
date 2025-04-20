"""Catalog service for Eulogos, using file paths as text identifiers.

Key architectural principle:
1. text_id is ALWAYS the full data path including filename 
2. The integrated_catalog.json is the ONLY source of truth for all text paths
3. No URN processing or path reconstruction is permitted
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from app.models.catalog import Author, Text, UnifiedCatalog


class CatalogService:
    """Service for accessing the unified catalog with path-based text IDs."""

    def __init__(
        self, 
        catalog_path: str = None, 
        data_dir: str = None,
        settings = None
    ):
        """Initialize the catalog service.

        Args:
            catalog_path: Path to the integrated_catalog.json file
            data_dir: Path to the data directory containing the XML files
            settings: Optional application settings
        """
        # If settings are provided, extract paths from it
        if settings:
            catalog_path = catalog_path or str(settings.catalog_path)
            data_dir = data_dir or str(settings.data_dir)
            
        self.catalog_path = Path(catalog_path) if catalog_path else Path("integrated_catalog.json")
        self.data_dir = Path(data_dir) if data_dir else Path("data")

        # Primary data
        self._catalog_data = None
        self._unified_catalog = None

        # Derived indexes
        self._texts_by_id: Dict[str, Text] = {}  # text_id = full path to file
        self._texts_by_author: Dict[str, List[Text]] = {}
        self._texts_by_language: Dict[str, List[Text]] = {}
        
        logger.debug("Initializing CatalogService with catalog_path={}, data_dir={}", catalog_path, data_dir)

    def load_catalog(self) -> Dict:
        """Load the catalog data from file.

        Returns:
            The catalog data as a dictionary
        """
        if not self.catalog_path.exists():
            logger.error(f"Catalog file not found: {self.catalog_path}")
            raise FileNotFoundError(f"Catalog file not found: {self.catalog_path}")

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                self._catalog_data = json.load(f)
                logger.info(f"Loaded catalog from {self.catalog_path}")
                return self._catalog_data
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            raise

    def create_unified_catalog(self) -> UnifiedCatalog:
        """Create a unified catalog from the catalog data.

        Returns:
            A UnifiedCatalog object
        """
        if self._catalog_data is None:
            self.load_catalog()

        # Process catalog entries and create texts with path-based IDs
        catalog_entries = []
        authors = {}

        # Process the nested structure of authors->works in integrated_catalog.json
        for author_id, author_data in self._catalog_data.items():
            # Create author
            authors[author_id] = Author(
                id=author_id,
                name=author_data.get("name", "Unknown"),
                century=author_data.get("century", 0),
                type=author_data.get("type", ""),
            )
            
            # Process works and their editions/translations
            works_data = author_data.get("works", {})
            for work_id, work_data in works_data.items():
                # Process editions
                for edition_id, edition_data in work_data.get("editions", {}).items():
                    # Get the file path - THIS IS THE TEXT ID
                    file_path = edition_data.get("path")
                    if file_path:
                        # Create text entry with path as ID
                        text_entry = Text(
                            id=file_path,  # The ID is the full path
                            group_name=author_data.get("name", "Unknown Author"),
                            work_name=work_data.get("title", "Unknown Work"),
                            language=edition_data.get("language", "grc"),
                            wordcount=edition_data.get("word_count", 0),
                            author_id=author_id,
                            path=file_path,  # Path and ID are the same
                            archived=edition_data.get("archived", False),
                            favorite=edition_data.get("favorite", False),
                        )
                        catalog_entries.append(text_entry)

                # Process translations
                for translation_id, translation_data in work_data.get("translations", {}).items():
                    # Get the file path - THIS IS THE TEXT ID
                    file_path = translation_data.get("path")
                    if file_path:
                        # Create text entry with path as ID
                        text_entry = Text(
                            id=file_path,  # The ID is the full path
                            group_name=author_data.get("name", "Unknown Author"),
                            work_name=f"{work_data.get('title', 'Unknown Work')} ({translation_data.get('language', 'eng')} translation)",
                            language=translation_data.get("language", "eng"),
                            wordcount=translation_data.get("word_count", 0),
                            author_id=author_id,
                            path=file_path,  # Path and ID are the same
                            archived=translation_data.get("archived", False),
                            favorite=translation_data.get("favorite", False),
                        )
                        catalog_entries.append(text_entry)

        # Create unified catalog
        self._unified_catalog = UnifiedCatalog(
            statistics={
                "author_count": len(authors),
                "text_count": len(catalog_entries),
                "work_count": 0,  # To be calculated
                "greek_word_count": 0,  # To be calculated
                "latin_word_count": 0,  # To be calculated
                "arabic_word_count": 0,  # To be calculated
            },
            authors=authors,
            catalog=catalog_entries,
        )

        # Build indexes for efficient access
        self._build_indexes()

        logger.info(f"Created unified catalog with {len(authors)} authors and {len(catalog_entries)} texts")
        return self._unified_catalog

    def _build_indexes(self):
        """Build internal indexes for efficient access."""
        if not self._unified_catalog:
            logger.error("Cannot build indexes: unified catalog not created")
            return

        # Index texts by ID (which is the path)
        self._texts_by_id = {}
        for text in self._unified_catalog.catalog:
            # The ID is the full path
            if text.id:
                # Always verify ID matches path
                if text.id != text.path:
                    logger.warning(f"Text ID {text.id} does not match path {text.path}, fixing...")
                    text.id = text.path
                self._texts_by_id[text.id] = text

        # Index texts by author
        self._texts_by_author = {}
        for text in self._unified_catalog.catalog:
            if text.author_id:
                if text.author_id not in self._texts_by_author:
                    self._texts_by_author[text.author_id] = []
                self._texts_by_author[text.author_id].append(text)

        # Index texts by language
        self._texts_by_language = {}
        for text in self._unified_catalog.catalog:
            if text.language not in self._texts_by_language:
                self._texts_by_language[text.language] = []
            self._texts_by_language[text.language].append(text)

    def get_text_by_id(self, text_id: str) -> Optional[Text]:
        """Get a text by its ID (which is the full path).
        
        Args:
            text_id: The full path to the text file, used as ID
            
        Returns:
            The text object or None if not found
        """
        return self._texts_by_id.get(text_id)

    def get_texts_by_author(self, author_id: str, include_archived: bool = False) -> List[Text]:
        """Get all texts by an author.

        Args:
            author_id: The ID of the author
            include_archived: Whether to include archived texts

        Returns:
            A list of text objects
        """
        texts = self._texts_by_author.get(author_id, [])
        if not include_archived:
            texts = [text for text in texts if not text.archived]
        return texts

    def get_all_authors(self, include_archived: bool = False) -> List[Author]:
        """Get all authors.

        Args:
            include_archived: Whether to include authors with only archived texts

        Returns:
            A list of author objects
        """
        if not self._unified_catalog:
            return []

        if include_archived:
            return list(self._unified_catalog.authors.values())

        # Filter out authors who have only archived texts
        result = []
        for author_id, author in self._unified_catalog.authors.items():
            texts = self.get_texts_by_author(author_id, include_archived=False)
            if texts:  # Author has at least one non-archived text
                result.append(author)

        return result

    def get_author_by_id(self, author_id: str) -> Optional[Author]:
        """Get an author by their ID.
        
        Args:
            author_id: The ID of the author
            
        Returns:
            The author object or None if not found
        """
        if not self._unified_catalog or not self._unified_catalog.authors:
            return None
            
        return self._unified_catalog.authors.get(author_id)

    def archive_text_by_id(self, text_id: str, archive: bool = True) -> bool:
        """Archive or unarchive a text by its ID.

        Args:
            text_id: The ID of the text (which is the full path)
            archive: True to archive, False to unarchive

        Returns:
            True if successful, False if the text was not found
        """
        text = self.get_text_by_id(text_id)
        if not text:
            return False

        text.archived = archive
        self._save_catalog()
        return True

    def toggle_text_favorite_by_id(self, text_id: str) -> bool:
        """Toggle favorite status for a text by its ID.

        Args:
            text_id: The ID of the text (which is the full path)

        Returns:
            True if successful, False if the text was not found
        """
        text = self.get_text_by_id(text_id)
        if not text:
            return False

        text.favorite = not text.favorite
        self._save_catalog()
        return True

    def _save_catalog(self) -> bool:
        """Save the catalog data to file.

        Returns:
            True if successful, False otherwise
        """
        # Implementation left as an exercise
        # This would update the integrated_catalog.json with changes
        return True
        
    def _validate_paths(self) -> None:
        """Validate paths in the unified catalog."""
        if not self._unified_catalog:
            return

        for text in self._unified_catalog.catalog:
            # Validate that ID and path are the same
            if text.id != text.path:
                logger.warning(f"Text ID {text.id} does not match path {text.path} - fixing...")
                text.id = text.path  # Ensure ID and path match
                
            # Validate that the path exists on disk
            file_path = self.data_dir / text.path
            if not file_path.exists():
                logger.warning(f"Path does not exist for {text.id}: {file_path}")
