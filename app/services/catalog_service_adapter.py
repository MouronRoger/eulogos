"""Adapter for backward compatibility with existing CatalogService.

This module provides a compatibility layer that allows existing code to use
the enhanced catalog service without requiring changes.
"""

import warnings
from typing import Optional

from app.config import EulogosSettings
from app.services.enhanced_catalog_service import EnhancedCatalogService


class CatalogServiceAdapter:
    """Adapter for backward compatibility with existing CatalogService."""

    def __init__(
        self, enhanced_service: Optional[EnhancedCatalogService] = None, settings: Optional[EulogosSettings] = None
    ):
        """Initialize the adapter.

        Args:
            enhanced_service: Optional EnhancedCatalogService instance
            settings: Optional settings object
        """
        self.enhanced_service = enhanced_service or EnhancedCatalogService(settings=settings)
        # Issue deprecation warning
        warnings.warn(
            "CatalogServiceAdapter is deprecated. Use EnhancedCatalogService directly.",
            DeprecationWarning,
            stacklevel=2,
        )

    def load_catalog(self):
        """Load the catalog from file.

        Returns:
            The loaded catalog data
        """
        return self.enhanced_service.load_catalog()

    def get_text_by_urn(self, urn):
        """Get a text by URN.

        Args:
            urn: URN in any supported format

        Returns:
            Text object or None if not found
        """
        return self.enhanced_service.get_text_by_urn(urn)

    def get_path_by_urn(self, urn):
        """Get the file path for a text by URN.

        Args:
            urn: URN in any supported format

        Returns:
            File path or None if not found
        """
        return self.enhanced_service.get_path_by_urn(urn)

    def resolve_file_path(self, urn):
        """Resolve a URN to a full file path.

        Args:
            urn: URN in any supported format

        Returns:
            Full file path or None if not found
        """
        return self.enhanced_service.resolve_file_path(urn)

    def get_authors(self, include_archived=False):
        """Get all authors.

        Args:
            include_archived: Whether to include archived authors

        Returns:
            List of Author objects
        """
        return self.enhanced_service.get_authors(include_archived)

    def get_texts_by_author(self, author_id, include_archived=False):
        """Get all texts by an author.

        Args:
            author_id: Author ID
            include_archived: Whether to include archived texts

        Returns:
            List of Text objects
        """
        return self.enhanced_service.get_texts_by_author(author_id, include_archived)

    def archive_text(self, urn, archive=True):
        """Archive or unarchive a text.

        Args:
            urn: URN in any supported format
            archive: True to archive, False to unarchive

        Returns:
            True if successful, False otherwise
        """
        return self.enhanced_service.archive_text(urn, archive)

    def toggle_text_favorite(self, urn):
        """Toggle favorite status for a text.

        Args:
            urn: URN in any supported format

        Returns:
            True if successful, False otherwise
        """
        return self.enhanced_service.toggle_favorite(urn)
