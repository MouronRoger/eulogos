"""Simple catalog service for Eulogos without complex URN abstractions.

This service provides a streamlined approach to catalog operations by using
direct URN-to-path translation without the need for complex URN model classes.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from app.models.catalog import Author, Text, UnifiedCatalog


class SimpleCatalogService:
    """Simplified service for accessing the catalog with direct URN handling."""

    def __init__(self, catalog_path: str = None, data_dir: str = None):
        """Initialize the catalog service.

        Args:
            catalog_path: Path to the catalog file (defaults to integrated_catalog.json)
            data_dir: Path to the data directory containing the XML files
        """
        self.catalog_path = Path(catalog_path or "integrated_catalog.json")
        self.data_dir = Path(data_dir or "data")

        # Primary data
        self._catalog_data = None
        self._unified_catalog = None

        # Derived indexes for efficient access
        self._texts_by_urn: Dict[str, Text] = {}
        self._texts_by_author: Dict[str, List[Text]] = {}
        self._texts_by_language: Dict[str, List[Text]] = {}
        self._authors_by_id: Dict[str, Author] = {}

    def load_catalog(self, force_reload: bool = False) -> Dict:
        """Load the catalog data from file.

        Args:
            force_reload: Whether to force reload even if already loaded

        Returns:
            The loaded catalog data

        Raises:
            FileNotFoundError: If catalog file not found
        """
        if self._catalog_data is not None and not force_reload:
            return self._catalog_data

        if not self.catalog_path.exists():
            logger.error(f"Catalog file not found: {self.catalog_path}")
            raise FileNotFoundError(f"Catalog file not found: {self.catalog_path}")

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                self._catalog_data = json.load(f)
                logger.info(f"Loaded catalog from {self.catalog_path}")

                # Build the unified catalog for easier access
                self._build_unified_catalog()

                return self._catalog_data
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            raise

    def _build_unified_catalog(self):
        """Build a unified catalog model from the loaded catalog data."""
        if not self._catalog_data:
            logger.error("Cannot build unified catalog: no catalog data loaded")
            return

        # Process authors and works from hierarchical structure
        authors = {}
        catalog_entries = []

        # Extract authors
        for author_id, author_data in self._catalog_data.items():
            # Create author entry
            author = Author(
                id=author_id,
                name=author_data.get("name", "Unknown"),
                century=author_data.get("century", 0),
                type=author_data.get("type", "Unknown"),
            )
            authors[author_id] = author
            self._authors_by_id[author_id] = author

            # Process works
            works_data = author_data.get("works", {})
            for work_id, work_data in works_data.items():
                # Process editions
                for edition_id, edition_data in work_data.get("editions", {}).items():
                    urn = edition_data.get("urn")
                    if not urn:
                        continue

                    text = Text(
                        urn=urn,
                        group_name=author.name,
                        work_name=work_data.get("title", "Unknown Work"),
                        language=edition_data.get("language", "grc"),
                        wordcount=edition_data.get("word_count", 0),
                        path=edition_data.get("path"),
                        author_id=author_id,
                        archived=False,
                        favorite=False,
                    )
                    catalog_entries.append(text)
                    self._texts_by_urn[urn] = text

                    # Add to author index
                    if author_id not in self._texts_by_author:
                        self._texts_by_author[author_id] = []
                    self._texts_by_author[author_id].append(text)

                    # Add to language index
                    if text.language not in self._texts_by_language:
                        self._texts_by_language[text.language] = []
                    self._texts_by_language[text.language].append(text)

                # Process translations
                for translation_id, translation_data in work_data.get("translations", {}).items():
                    urn = translation_data.get("urn")
                    if not urn:
                        continue

                    text = Text(
                        urn=urn,
                        group_name=author.name,
                        work_name=(
                            f"{work_data.get('title', 'Unknown Work')} "
                            f"({translation_data.get('language', 'Unknown')} translation)"
                        ),
                        language=translation_data.get("language", "eng"),
                        wordcount=translation_data.get("word_count", 0),
                        path=translation_data.get("path"),
                        author_id=author_id,
                        archived=False,
                        favorite=False,
                    )
                    catalog_entries.append(text)
                    self._texts_by_urn[urn] = text

                    # Add to author index
                    if author_id not in self._texts_by_author:
                        self._texts_by_author[author_id] = []
                    self._texts_by_author[author_id].append(text)

                    # Add to language index
                    if text.language not in self._texts_by_language:
                        self._texts_by_language[text.language] = []
                    self._texts_by_language[text.language].append(text)

        # Compute statistics
        stats = {
            "nodeCount": len(catalog_entries),
            "greekWords": sum(t.wordcount for t in catalog_entries if t.language == "grc"),
            "latinWords": sum(t.wordcount for t in catalog_entries if t.language == "lat"),
            "arabicwords": sum(t.wordcount for t in catalog_entries if t.language == "ara"),
            "authorCount": len(authors),
            "textCount": len(catalog_entries),
        }

        # Create unified catalog
        self._unified_catalog = UnifiedCatalog(
            statistics=stats,
            authors=authors,
            catalog=catalog_entries,
        )

        logger.info(f"Built unified catalog with {len(authors)} authors and {len(catalog_entries)} texts")

    def _save_catalog(self) -> bool:
        """Save the catalog with any modifications back to disk.

        Returns:
            True if successful, False otherwise
        """
        if not self._catalog_data:
            logger.error("No catalog data to save")
            return False

        try:
            # Update catalog entries in the hierarchical structure
            for text in self._texts_by_urn.values():
                if not text.author_id:
                    continue

                # Parse the URN to find the work and edition/translation
                try:
                    parts = text.urn.split(":")
                    if len(parts) >= 4:
                        identifier = parts[3].split(":")[0]
                        id_parts = identifier.split(".")

                        if len(id_parts) >= 3:
                            author_id = text.author_id
                            work_id = id_parts[1]
                            version_id = id_parts[2]

                            # Find if it's an edition or translation based on language
                            is_edition = text.language == "grc" or text.language == "lat"
                            version_type = "editions" if is_edition else "translations"

                            # Update the archived/favorite status
                            if author_id in self._catalog_data and "works" in self._catalog_data[author_id]:
                                works = self._catalog_data[author_id]["works"]
                                if work_id in works and version_type in works[work_id]:
                                    versions = works[work_id][version_type]
                                    if version_id in versions:
                                        versions[version_id]["archived"] = text.archived
                                        versions[version_id]["favorite"] = text.favorite
                except Exception as e:
                    logger.error(f"Error updating catalog entry for {text.urn}: {e}")

            # Write the updated catalog to disk
            with open(self.catalog_path, "w", encoding="utf-8") as f:
                json.dump(self._catalog_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved catalog to {self.catalog_path}")
                return True
        except Exception as e:
            logger.error(f"Error saving catalog: {e}")
            return False

    def resolve_urn_to_path(self, urn: str) -> Path:
        """Resolve a URN to a file path through direct transformation.

        Args:
            urn: The URN string to resolve

        Returns:
            Path object for the XML file

        Raises:
            ValueError: If the URN format is invalid
        """
        # First try to get the path from the catalog
        if urn in self._texts_by_urn and self._texts_by_urn[urn].path:
            return self.data_dir / self._texts_by_urn[urn].path

        # Fall back to direct URN to path transformation
        parts = urn.split(":")
        if len(parts) < 4:
            raise ValueError(f"Invalid URN format: {urn}")

        # Extract the identifier (e.g., tlg0532.tlg001.perseus-grc2)
        identifier = parts[3].split("#")[0]

        # Split into components
        id_parts = identifier.split(".")
        if len(id_parts) < 3:
            raise ValueError(f"URN missing version information: {urn}")

        # Extract the pieces we need
        textgroup = id_parts[0]
        work = id_parts[1]
        version = id_parts[2]

        # Build the path
        return self.data_dir / textgroup / work / f"{textgroup}.{work}.{version}.xml"

    def get_text_by_urn(self, urn: str) -> Optional[Text]:
        """Get a text by its URN.

        Args:
            urn: The URN of the text

        Returns:
            The Text object or None if not found
        """
        if not self._catalog_data:
            self.load_catalog()

        return self._texts_by_urn.get(urn)

    def get_text_by_path(self, path: str) -> Optional[Text]:
        """Get a text by its file path.

        Args:
            path: Path to the text file (relative to data_dir)

        Returns:
            The Text object or None if not found
        """
        if not self._catalog_data:
            self.load_catalog()

        # Search through texts to find one with matching path
        for text in self._texts_by_urn.values():
            if text.path == path:
                return text

        return None

    def get_all_texts(self, include_archived: bool = False) -> List[Text]:
        """Get all texts in the catalog.

        Args:
            include_archived: Whether to include archived texts

        Returns:
            List of text objects
        """
        if not self._catalog_data:
            self.load_catalog()

        if include_archived:
            return list(self._texts_by_urn.values())

        return [text for text in self._texts_by_urn.values() if not text.archived]

    def get_author_by_id(self, author_id: str) -> Optional[Author]:
        """Get an author by ID.

        Args:
            author_id: ID of the author

        Returns:
            Author object or None if not found
        """
        if not self._catalog_data:
            self.load_catalog()

        return self._authors_by_id.get(author_id)

    def get_authors(self, include_archived: bool = False) -> List[Author]:
        """Get all authors in the catalog.

        Args:
            include_archived: Whether to include authors with only archived texts

        Returns:
            List of author objects
        """
        if not self._catalog_data:
            self.load_catalog()

        if include_archived:
            return list(self._authors_by_id.values())

        # Filter out authors who only have archived texts
        result = []
        for author_id, author in self._authors_by_id.items():
            texts = self.get_texts_by_author(author_id, include_archived=False)
            if texts:  # Author has at least one non-archived text
                result.append(author)

        return result

    def get_all_authors(self) -> List[Author]:
        """Get all authors in the catalog.

        Returns:
            List of author objects
        """
        return self.get_authors(include_archived=True)

    def get_texts_by_author(self, author_id: str, include_archived: bool = False) -> List[Text]:
        """Get all texts by an author.

        Args:
            author_id: ID of the author
            include_archived: Whether to include archived texts

        Returns:
            List of text objects
        """
        if not self._catalog_data:
            self.load_catalog()

        texts = self._texts_by_author.get(author_id, [])

        if include_archived:
            return texts

        return [text for text in texts if not text.archived]

    def get_texts_by_language(self, language: str, include_archived: bool = False) -> List[Text]:
        """Get all texts in a specific language.

        Args:
            language: ISO language code (e.g., 'grc', 'lat', 'eng')
            include_archived: Whether to include archived texts

        Returns:
            List of text objects
        """
        if not self._catalog_data:
            self.load_catalog()

        texts = self._texts_by_language.get(language, [])

        if include_archived:
            return texts

        return [text for text in texts if not text.archived]

    def archive_text(self, urn: str, archive: bool = True) -> bool:
        """Archive or unarchive a text.

        Args:
            urn: URN of the text
            archive: True to archive, False to unarchive

        Returns:
            True if successful, False if text not found
        """
        text = self.get_text_by_urn(urn)
        if not text:
            return False

        text.archived = archive
        return self._save_catalog()

    def favorite_text(self, urn: str, favorite: bool = True) -> bool:
        """Mark a text as favorite or not.

        Args:
            urn: URN of the text
            favorite: True to mark as favorite, False to unmark

        Returns:
            True if successful, False if text not found
        """
        text = self.get_text_by_urn(urn)
        if not text:
            return False

        text.favorite = favorite
        return self._save_catalog()

    def toggle_favorite(self, urn: str) -> bool:
        """Toggle the favorite status of a text.

        Args:
            urn: URN of the text

        Returns:
            New favorite status if successful, False if text not found
        """
        text = self.get_text_by_urn(urn)
        if not text:
            return False

        text.favorite = not text.favorite
        if self._save_catalog():
            return text.favorite
        return False

    def get_catalog_statistics(self) -> Dict[str, int]:
        """Get catalog statistics.

        Returns:
            Dictionary with catalog statistics
        """
        if not self._unified_catalog:
            self.load_catalog()

        stats = self._unified_catalog.statistics.model_dump()
        return stats
