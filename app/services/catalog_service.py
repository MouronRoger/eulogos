"""Service for catalog operations."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from loguru import logger

from app.models.catalog import Author, Text, UnifiedCatalog


class CatalogService:
    """Service for accessing the unified catalog."""

    def __init__(
        self, 
        catalog_path: str = None, 
        author_path: str = None, 
        data_dir: str = None,
        settings = None
    ):
        """Initialize the catalog service.

        Args:
            catalog_path: Path to the catalog_index.json file
            author_path: Path to the author_index.json file
            data_dir: Path to the data directory containing the XML files
            settings: Optional application settings
        """
        # If settings are provided, extract paths from it
        if settings:
            catalog_path = catalog_path or str(settings.catalog_path)
            data_dir = data_dir or str(settings.data_dir)
            
        self.catalog_path = Path(catalog_path) if catalog_path else Path("catalog_index.json")
        self.author_path = Path(author_path) if author_path else None
        self.data_dir = Path(data_dir) if data_dir else Path("data")

        # Primary data
        self._catalog_data = None
        self._author_data = None
        self._unified_catalog = None

        # Derived indexes
        self._texts_by_id: Dict[str, Text] = {}
        self._texts_by_author: Dict[str, List[Text]] = {}
        self._texts_by_language: Dict[str, List[Text]] = {}
        self._authors_by_century: Dict[int, List[Author]] = {}
        self._authors_by_type: Dict[str, List[Author]] = {}
        self._available_languages: Set[str] = set()
        
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

                # If this is an integrated catalog with authors included
                if "authors" in self._catalog_data and not self.author_path:
                    self._author_data = self._catalog_data.get("authors", {})
                    logger.info(f"Extracted {len(self._author_data)} authors from integrated catalog")

                return self._catalog_data
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            raise

    def _save_catalog(self) -> bool:
        """Save the catalog data to file.

        Returns:
            True if successful, False otherwise
        """
        if not self._catalog_data:
            logger.error("No catalog data to save")
            return False

        try:
            # Update catalog entries with current state
            for text in self._texts_by_id.values():
                # Find the corresponding entry in the catalog data
                for entry in self._catalog_data.get("catalog", []):
                    if entry.get("id") == text.id:
                        # Update with current state of archived/favorite
                        entry["archived"] = text.archived
                        entry["favorite"] = text.favorite
                        break

            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(self._catalog_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved catalog to {self.catalog_path}")
                return True
        except Exception as e:
            logger.error(f"Error saving catalog: {e}")
            return False

    def load_authors(self) -> Dict:
        """Load the author data from file.

        Returns:
            The author data as a dictionary
        """
        # If we already have author data from the integrated catalog
        if self._author_data is not None:
            return self._author_data

        # If no author path specified, try to extract from catalog
        if not self.author_path:
            if self._catalog_data is None:
                self.load_catalog()
            return self._author_data or {}

        # Load from separate author file if path exists
        if not self.author_path.exists():
            logger.error(f"Author file not found: {self.author_path}")
            raise FileNotFoundError(f"Author file not found: {self.author_path}")

        try:
            with open(self.author_path, "r", encoding="utf-8") as f:
                self._author_data = json.load(f)
                logger.info(f"Loaded authors from {self.author_path}")
                return self._author_data
        except Exception as e:
            logger.error(f"Error loading authors: {e}")
            raise

    def create_unified_catalog(self) -> UnifiedCatalog:
        """Create a unified catalog from the catalog and author data.

        Returns:
            A UnifiedCatalog object
        """
        if self._catalog_data is None:
            self.load_catalog()

        if self._author_data is None:
            self.load_authors()

        # Extract statistics from catalog data
        stats = {
            "nodeCount": self._catalog_data.get("statistics", {}).get("textCount", 0),
            "greekWords": self._catalog_data.get("statistics", {}).get("greekWords", 0),
            "latinWords": self._catalog_data.get("statistics", {}).get("latinWords", 0),
            "arabicwords": self._catalog_data.get("statistics", {}).get("arabicwords", 0),
            "authorCount": len(self._author_data),
            "textCount": self._catalog_data.get("statistics", {}).get("textCount", 0),
        }

        # Process catalog entries and link to authors
        catalog_entries = []

        # Process the nested structure of authors->works in integrated_catalog.json
        for author_id, author_data in self._author_data.items():
            # Get works for this author from the nested structure
            works_data = author_data.get("works", {})

            for work_id, work_data in works_data.items():
                # Extract base work info
                work_name = work_data.get("title", "Unknown Work")
                work_urn_base = f"urn:cts:greekLit:{author_id}.{work_id}"

                # Process editions
                editions = work_data.get("editions", {})
                for edition_id, edition_data in editions.items():
                    edition_urn = f"{work_urn_base}.{edition_id}"
                    language = edition_data.get("language", "grc")

                    # Get the file path from edition data
                    file_path = edition_data.get("path", None)

                    # Create text entry for this edition
                    text_entry = {
                        "id": file_path,  # Use the canonical path as the stable ID
                        "urn": edition_urn,
                        "group_name": author_data.get("name", "Unknown Author"),
                        "work_name": work_name,
                        "language": language,
                        "wordcount": edition_data.get("word_count", 0),
                        "author_id": author_id,
                        "archived": False,
                        "favorite": False,
                        "path": file_path,  # Add the path to the text entry
                    }

                    catalog_entries.append(Text(**text_entry))

                # Process translations
                translations = work_data.get("translations", {})
                for translation_id, translation_data in translations.items():
                    translation_urn = f"{work_urn_base}.{translation_id}"
                    language = translation_data.get("language", "eng")

                    # Get the file path from translation data
                    file_path = translation_data.get("path", None)

                    # Create text entry for this translation
                    text_entry = {
                        "id": file_path,  # Use the canonical path as the stable ID
                        "urn": translation_urn,
                        "group_name": author_data.get("name", "Unknown Author"),
                        "work_name": f"{work_name} ({language} translation)",
                        "language": language,
                        "wordcount": translation_data.get("word_count", 0),
                        "author_id": author_id,
                        "archived": False,
                        "favorite": False,
                        "path": file_path,  # Add the path to the text entry
                    }

                    catalog_entries.append(Text(**text_entry))

        # Convert authors to model objects and set the id field
        authors = {}
        for author_id, data in self._author_data.items():
            author_data = {
                "name": data.get("name", "Unknown"),
                "century": data.get("century", 0),
                "type": data.get("type", "Unknown"),
                "id": author_id,
                "archived": data.get("archived", False),
            }
            authors[author_id] = Author(**author_data)

        # Create unified catalog
        self._unified_catalog = UnifiedCatalog(
            statistics=stats,
            authors=authors,
            catalog=catalog_entries,
        )

        # Build indexes for efficient access
        self._build_indexes()

        # Validate paths
        self._validate_paths()

        logger.info(f"Created unified catalog with {len(authors)} authors and {len(catalog_entries)} texts")
        return self._unified_catalog

    def _build_indexes(self):
        """Build internal indexes for efficient access."""
        if not self._unified_catalog:
            logger.error("Cannot build indexes: unified catalog not created")
            return

        # Index texts by ID
        self._texts_by_id = {}
        for text in self._unified_catalog.catalog:
            if text.id:
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
            self._available_languages.add(text.language)

        # Index authors by century and type
        self._authors_by_century = {}
        self._authors_by_type = {}

        for author_id, author in self._unified_catalog.authors.items():
            # Index by century
            if author.century not in self._authors_by_century:
                self._authors_by_century[author.century] = []
            self._authors_by_century[author.century].append(author)

            # Index by type
            if author.type not in self._authors_by_type:
                self._authors_by_type[author.type] = []
            self._authors_by_type[author.type].append(author)

    def get_text_by_id(self, text_id: str) -> Optional[Text]:
        """Get a text by its stable ID (not URN).
        
        Args:
            text_id: The stable ID of the text
            
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
            text_id: The ID of the text
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
            text_id: The ID of the text

        Returns:
            True if successful, False if the text was not found
        """
        text = self.get_text_by_id(text_id)
        if not text:
            return False

        text.favorite = not text.favorite
        self._save_catalog()
        return True

    def delete_text_by_id(self, text_id: str) -> bool:
        """Delete a text from the catalog by its ID.

        Args:
            text_id: The ID of the text

        Returns:
            True if successful, False if the text was not found
        """
        text = self.get_text_by_id(text_id)
        if not text:
            return False

        # Remove from catalog data
        if self._catalog_data and "catalog" in self._catalog_data:
            self._catalog_data["catalog"] = [
                entry for entry in self._catalog_data["catalog"] if entry.get("id") != text_id
            ]

        # Remove from unified catalog
        if self._unified_catalog:
            self._unified_catalog.catalog = [text_obj for text_obj in self._unified_catalog.catalog if text_obj.id != text_id]

        # Remove from indexes
        text = self._texts_by_id.pop(text_id, None)

        if text and text.author_id:
            if text.author_id in self._texts_by_author:
                self._texts_by_author[text.author_id] = [
                    t for t in self._texts_by_author[text.author_id] if t.id != text_id
                ]

        if text and text.language:
            if text.language in self._texts_by_language:
                self._texts_by_language[text.language] = [
                    t for t in self._texts_by_language[text.language] if t.id != text_id
                ]

        # Save changes
        self._save_catalog()
        return True

    def validate_catalog_files(self) -> Dict:
        """Validate synchronization between actual files and catalog data.

        Returns:
            Dictionary with validation results
        """
        if self._catalog_data is None:
            self.load_catalog()

        if self._author_data is None:
            self.load_authors()

        # Find all actual XML files in the data directory
        all_xml_files = set(str(p.relative_to(self.data_dir)) for p in self.data_dir.glob("**/*.xml"))
        
        # Get all paths from catalog
        catalog_paths = {entry.get("path", "") for entry in self._catalog_data.get("catalog", [])}

        # Statistics
        stats = {
            "total_files": len(all_xml_files),
            "files_in_catalog": len(catalog_paths),
            "uncatalogued_files": len(all_xml_files - catalog_paths),
            "invalid_catalog_entries": len(catalog_paths - all_xml_files),
        }

        # Track issues
        uncatalogued_files = list(all_xml_files - catalog_paths)
        invalid_entries = list(catalog_paths - all_xml_files)

        # Return validation results
        return {
            "stats": stats,
            "uncatalogued_files": uncatalogued_files,
            "invalid_catalog_entries": invalid_entries,
            "validity": len(uncatalogued_files) == 0 and len(invalid_entries) == 0
        }

    def _validate_paths(self) -> None:
        """Validate paths in the unified catalog.

        This ensures all texts have a valid path field from the catalog.
        """
        if not self._unified_catalog:
            return

        for text in self._unified_catalog.catalog:
            # Log warning if text has no path from catalog
            if not text.path:
                logger.warning(f"Text {text.id} has no path in catalog")
                continue

            # Validate that the path exists on disk
            file_path = self.data_dir / text.path
            if not file_path.exists():
                logger.warning(f"Path does not exist for {text.id}: {file_path}")

    