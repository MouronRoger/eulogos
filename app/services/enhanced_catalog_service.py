"""Enhanced catalog service for the Eulogos API.

This module provides enhanced catalog functionality with URN support.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from app.config import EulogosSettings
from app.models.enhanced_catalog import (  # noqa: F401 - Work used in type hints
    Author,
    Catalog,
    TextVersion,
    Work,
)
from app.models.enhanced_urn import EnhancedURN

# Configure logging
log = logging.getLogger(__name__)


class EnhancedCatalogService:
    """Enhanced service for accessing the integrated catalog."""

    def __init__(self, settings: Optional[EulogosSettings] = None):
        """Initialize the catalog service.

        Args:
            settings: Optional settings object
        """
        self.settings = settings or EulogosSettings()
        self._catalog: Optional[Catalog] = None
        self._last_loaded: float = 0

        # Indexes for efficient lookups
        self._text_path_by_urn: Dict[str, str] = {}
        self._urn_by_path: Dict[str, str] = {}
        self._texts_by_author: Dict[str, List[str]] = {}
        self._texts_by_language: Dict[str, List[str]] = {}
        self._original_models: Dict[str, Any] = {}

        # Import here to avoid circular imports
        try:
            from app.models.catalog import Text

            self._original_text_class = Text
        except ImportError:
            self._original_text_class = None

    def load_catalog(self, force_reload: bool = False) -> Catalog:
        """Load the catalog from file.

        Args:
            force_reload: Whether to force reload the catalog from disk

        Returns:
            Loaded catalog

        Raises:
            FileNotFoundError: If catalog file doesn't exist
        """
        if not force_reload and self._catalog and time.time() - self._last_loaded < 60:
            # Use cached catalog if it's less than 1 minute old
            return self._catalog

        if not self.settings.catalog_path.exists():
            logger.error(f"Catalog file not found: {self.settings.catalog_path}")
            raise FileNotFoundError(f"Catalog file not found: {self.settings.catalog_path}")

        try:
            logger.info(f"Loading catalog from {self.settings.catalog_path}")
            with open(self.settings.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._catalog = Catalog.model_validate(data)
                self._last_loaded = time.time()

                # Build indexes
                self._build_indexes()

                logger.info(f"Loaded catalog with {len(self._catalog.authors)} authors")
                return self._catalog
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            raise

    def _build_indexes(self) -> None:
        """Build lookup indexes for efficiency."""
        if not self._catalog:
            return

        logger.debug("Building catalog indexes")

        # Clear existing indexes
        self._text_path_by_urn = {}
        self._urn_by_path = {}
        self._texts_by_author = {}
        self._texts_by_language = {}

        # Build indexes from catalog entries
        for author_id, author in self._catalog.authors.items():
            if author_id not in self._texts_by_author:
                self._texts_by_author[author_id] = []

            for work_id, work in author.works.items():
                # Process editions
                for edition_id, edition in work.editions.items():
                    urn = edition.urn

                    # Add to indexes
                    if edition.path:
                        self._text_path_by_urn[urn] = edition.path
                        self._urn_by_path[edition.path] = urn

                    self._texts_by_author[author_id].append(urn)

                    # Add to language index
                    if edition.language not in self._texts_by_language:
                        self._texts_by_language[edition.language] = []
                    self._texts_by_language[edition.language].append(urn)

                # Process translations
                for translation_id, translation in work.translations.items():
                    urn = translation.urn

                    # Add to indexes
                    if translation.path:
                        self._text_path_by_urn[urn] = translation.path
                        self._urn_by_path[translation.path] = urn

                    self._texts_by_author[author_id].append(urn)

                    # Add to language index
                    if translation.language not in self._texts_by_language:
                        self._texts_by_language[translation.language] = []
                    self._texts_by_language[translation.language].append(urn)

        logger.debug(f"Built catalog indexes with {len(self._text_path_by_urn)} paths")

    def get_path_by_urn(self, urn: str) -> Optional[str]:
        """Get the file path for a text by URN.

        Args:
            urn: URN as string

        Returns:
            Relative file path or None if not found
        """
        if not self._catalog:
            self.load_catalog()

        return self._text_path_by_urn.get(urn)

    def resolve_file_path(self, urn: str) -> Optional[Path]:
        """Resolve a URN to a full file path.

        This method handles different URN formats for backward compatibility:
        - EnhancedURN instance
        - URN string
        - Legacy URN objects (with urn_string attribute)

        Args:
            urn: URN in any supported format

        Returns:
            Full file path or None if not found
        """
        if not self._catalog:
            self.load_catalog()

        # Look up path in catalog
        relative_path = self.get_path_by_urn(urn)
        if relative_path:
            full_path = self.settings.data_dir / relative_path
            logger.debug(f"Resolved URN {urn} to path {full_path}")
            return full_path

        logger.warning(f"No path found in catalog for URN: {urn}")

        # Fallback to direct path construction for backward compatibility
        try:
            if self.settings.compatibility_mode:
                enhanced_urn = EnhancedURN(value=urn)
                if enhanced_urn.is_valid_for_path():
                    fallback_path = enhanced_urn.get_file_path(str(self.settings.data_dir))
                    logger.warning(f"Using fallback path resolution for {urn}: {fallback_path}")
                    return fallback_path
        except Exception as e:
            logger.error(f"Error in fallback path resolution: {e}")

        return None

    def get_text_by_urn(self, urn: str) -> Optional[Union[TextVersion, Any]]:
        """Get a text by URN, with backward compatibility support.

        Args:
            urn: URN in any supported format

        Returns:
            TextVersion object or original model for compatibility
        """
        if not self._catalog:
            self.load_catalog()

        # Parse URN to navigate catalog
        try:
            enhanced_urn = EnhancedURN(value=urn)

            # Navigate through the catalog structure
            author = self._catalog.authors.get(enhanced_urn.textgroup)
            if not author:
                return None

            work = author.works.get(enhanced_urn.work)
            if not work:
                return None

            # Look in editions and translations
            text = None
            if enhanced_urn.version in work.editions:
                text = work.editions[enhanced_urn.version]
            elif enhanced_urn.version in work.translations:
                text = work.translations[enhanced_urn.version]

            if not text:
                return None

            # For compatibility, convert to original model if needed
            if self.settings.compatibility_mode and self._original_text_class:
                # Cache original model to avoid recreating it
                if urn not in self._original_models:
                    # Create original model with required fields
                    original = self._original_text_class(
                        urn=text.urn,
                        group_name=author.name,
                        work_name=work.title,
                        language=text.language,
                        wordcount=text.word_count,
                        path=text.path,
                        archived=getattr(text, "archived", False),
                        favorite=getattr(text, "favorite", False),
                    )
                    self._original_models[urn] = original

                return self._original_models[urn]

            return text

        except Exception as e:
            logger.error(f"Error getting text for URN {urn}: {e}")
            return None

    def get_authors(self, include_archived: bool = False) -> List[Author]:
        """Get all authors.

        Args:
            include_archived: Whether to include archived authors

        Returns:
            List of Author objects
        """
        if not self._catalog:
            self.load_catalog()

        authors = list(self._catalog.authors.values())

        if not include_archived:
            # Filter out archived authors
            authors = [a for a in authors if not getattr(a, "archived", False)]

        return authors

    def get_texts_by_author(self, author_id: str, include_archived: bool = False) -> List[Any]:
        """Get all texts by an author.

        Args:
            author_id: Author ID
            include_archived: Whether to include archived texts

        Returns:
            List of TextVersion objects or original models
        """
        if not self._catalog:
            self.load_catalog()

        if author_id not in self._texts_by_author:
            return []

        texts = []
        for urn in self._texts_by_author[author_id]:
            text = self.get_text_by_urn(urn)
            if text and (include_archived or not getattr(text, "archived", False)):
                texts.append(text)

        return texts

    def validate_path_consistency(self) -> Dict[str, Any]:
        """Validate that all URNs in the catalog have valid paths.

        Returns:
            Dictionary with validation results
        """
        if not self._catalog:
            self.load_catalog()

        results = {
            "total_urns": 0,
            "urns_with_path": 0,
            "urns_without_path": 0,
            "existing_files": 0,
            "missing_files": 0,
            "urns_without_path_list": [],
            "missing_files_list": [],
        }

        # Check each URN in the catalog
        for author_id, author in self._catalog.authors.items():
            for work_id, work in author.works.items():
                # Check editions
                for edition_id, edition in work.editions.items():
                    results["total_urns"] += 1

                    if edition.path:
                        results["urns_with_path"] += 1
                        file_path = self.settings.data_dir / edition.path

                        if file_path.exists():
                            results["existing_files"] += 1
                        else:
                            results["missing_files"] += 1
                            results["missing_files_list"].append((edition.urn, str(file_path)))
                    else:
                        results["urns_without_path"] += 1
                        results["urns_without_path_list"].append(edition.urn)

                # Check translations
                for translation_id, translation in work.translations.items():
                    results["total_urns"] += 1

                    if translation.path:
                        results["urns_with_path"] += 1
                        file_path = self.settings.data_dir / translation.path

                        if file_path.exists():
                            results["existing_files"] += 1
                        else:
                            results["missing_files"] += 1
                            results["missing_files_list"].append((translation.urn, str(file_path)))
                    else:
                        results["urns_without_path"] += 1
                        results["urns_without_path_list"].append(translation.urn)

        return results

    def archive_text(self, urn: str, archive: bool = True) -> bool:
        """Archive or unarchive a text.

        Args:
            urn: URN in any supported format
            archive: True to archive, False to unarchive

        Returns:
            True if successful, False otherwise
        """
        text = self.get_text_by_urn(urn)
        if not text:
            return False

        # Set archived status
        if hasattr(text, "archived"):
            text.archived = archive

        return True

    def toggle_favorite(self, urn: str) -> bool:
        """Toggle favorite status for a text.

        Args:
            urn: URN in any supported format

        Returns:
            True if successful, False otherwise
        """
        text = self.get_text_by_urn(urn)
        if not text:
            return False

        # Toggle favorite status
        if hasattr(text, "favorite"):
            text.favorite = not text.favorite

        return True
