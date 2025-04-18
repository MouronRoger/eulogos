"""Enhanced URN model for textual references only.

This module provides a compatibility layer for code that previously relied on
enhanced URN functionality. URNs in Eulogos are only treated as textual references,
not for path resolution. All path resolution must use the catalog.
"""

from app.models.urn import URN


class EnhancedURN(URN):
    """Enhanced URN model for textual references only.

    This class exists purely for backward compatibility. All path resolution
    must go through the catalog service (using integrated_catalog.json) as the
    single source of truth.

    Do not use this class for new code - use the standard URN class instead,
    and resolve paths through the catalog service.
    """

    def __init__(self, value: str):
        """Initialize an EnhancedURN object.

        Args:
            value: The URN string
        """
        super().__init__(value)
