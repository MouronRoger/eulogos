"""Adapter for backward compatibility with the old CatalogService."""

import warnings
from typing import Any, Dict, List, Optional

from app.config import EulogosSettings
from app.models.enhanced_urn import EnhancedURN


class CatalogServiceAdapter:
    """Adapter for backward compatibility with original CatalogService.

    This adapter provides the same interface as the original CatalogService but
    delegates to the new EnhancedCatalogService. This allows existing code to
    continue working without modification during the transition period.
    """

    def __init__(self, enhanced_service: Optional[Any] = None, settings: Optional[EulogosSettings] = None):
        """Initialize the adapter.

        Args:
            enhanced_service: EnhancedCatalogService instance to delegate to
            settings: Optional settings for the adapter
        """
        # Import here to avoid circular imports and pydantic warnings
        from app.services.enhanced_catalog_service import EnhancedCatalogService

        self.settings = settings or EulogosSettings()

        if enhanced_service:
            self.enhanced_service = enhanced_service
        else:
            # Directly create an instance to avoid extra dependencies warnings
            self.enhanced_service = EnhancedCatalogService(settings=self.settings)

        # Issue deprecation warning
        warnings.warn(
            "CatalogServiceAdapter is deprecated. Use EnhancedCatalogService directly.",
            DeprecationWarning,
            stacklevel=2,
        )

    def load_catalog(self):
        """Load the catalog data.

        Returns:
            Loaded catalog data
        """
        return self.enhanced_service.load_catalog()

    def get_path_by_urn(self, urn: str) -> str:
        """Get file path for a URN string.

        Args:
            urn: URN string

        Returns:
            Path to the file
        """
        return str(self.enhanced_service.get_path_by_urn(urn))

    def resolve_file_path(self, urn_obj: Any) -> Any:
        """Resolve a URN object to file path.

        Args:
            urn_obj: URN object

        Returns:
            Path to the file
        """
        # Convert to string if it's not an EnhancedURN
        if not isinstance(urn_obj, EnhancedURN):
            urn_str = str(urn_obj)
            result = self.enhanced_service.resolve_file_path(urn_str)
        else:
            result = self.enhanced_service.resolve_file_path(urn_obj)

        return result

    def get_text_by_urn(self, urn: str) -> Dict[str, Any]:
        """Get text metadata by URN.

        Args:
            urn: URN string

        Returns:
            Text metadata
        """
        return self.enhanced_service.get_text_by_urn(urn)

    def get_text_by_path(self, path: str) -> Dict[str, Any]:
        """Get text metadata by file path.

        Args:
            path: Path to the text

        Returns:
            Text metadata
        """
        return self.enhanced_service.get_text_by_path(path)

    def get_all_texts(self) -> List[Dict[str, Any]]:
        """Get all texts in the catalog.

        Returns:
            List of text metadata
        """
        return self.enhanced_service.get_all_texts()

    def get_authors(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Get all authors in the catalog.

        Args:
            include_archived: Whether to include archived authors

        Returns:
            List of author metadata
        """
        # Mock objects in tests might not have get_all_authors but have get_authors
        if hasattr(self.enhanced_service, "get_authors"):
            return self.enhanced_service.get_authors(include_archived=include_archived)
        else:
            return self.enhanced_service.get_all_authors()

    def get_all_authors(self) -> List[Dict[str, Any]]:
        """Get all authors in the catalog.

        Returns:
            List of author metadata
        """
        return self.enhanced_service.get_all_authors()

    def get_author_by_id(self, author_id: str) -> Dict[str, Any]:
        """Get author metadata by ID.

        Args:
            author_id: Author ID

        Returns:
            Author metadata
        """
        return self.enhanced_service.get_author_by_id(author_id)

    def get_works_by_author(self, author_id: str) -> List[Dict[str, Any]]:
        """Get all works by an author.

        Args:
            author_id: Author ID

        Returns:
            List of work metadata
        """
        return self.enhanced_service.get_works_by_author(author_id)

    def get_texts_by_author(self, author_id: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Get all texts by an author.

        Args:
            author_id: Author ID
            include_archived: Whether to include archived texts

        Returns:
            List of text metadata
        """
        return self.enhanced_service.get_texts_by_author(author_id, include_archived=include_archived)

    def archive_text(self, urn: str, archive: bool = True) -> bool:
        """Archive or unarchive a text.

        Args:
            urn: URN string
            archive: Whether to archive or unarchive

        Returns:
            True if successful
        """
        # Pass the correct parameter name and return the result
        result = self.enhanced_service.archive_text(urn, archive=archive)
        return result if result is not None else True

    def favorite_text(self, urn: str, favorite: bool = True) -> None:
        """Mark a text as favorite or not.

        Args:
            urn: URN string
            favorite: Whether to mark as favorite
        """
        self.enhanced_service.favorite_text(urn, favorite)

    def toggle_text_favorite(self, urn: str) -> bool:
        """Toggle favorite status for a text.

        Args:
            urn: URN string

        Returns:
            New favorite status
        """
        return self.enhanced_service.toggle_favorite(urn)

    def get_catalog_statistics(self) -> Dict[str, int]:
        """Get catalog statistics.

        Returns:
            Dictionary with catalog statistics
        """
        return self.enhanced_service.get_catalog_statistics()
