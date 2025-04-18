"""Utility functions for file path handling."""

from pathlib import Path
from typing import Optional

from app.services.simple_catalog_service import SimpleCatalogService


def resolve_urn_to_path(
    urn: str, catalog_service: Optional[SimpleCatalogService] = None, data_path: str = "data"
) -> Path:
    """Resolve a URN to a file path through direct transformation.

    Simple URN to file path transformation:
    urn:cts:greekLit:tlg0532.tlg001.perseus-grc2 -> data/tlg0532/tlg001/tlg0532.tlg001.perseus-grc2.xml

    Args:
        urn: The URN to resolve as a string
        catalog_service: Optional SimpleCatalogService (used if path is in catalog)
        data_path: Base path for data files

    Returns:
        Path object for the XML file
    """
    data_path_obj = Path(data_path)

    # Try catalog first if available
    if catalog_service:
        return catalog_service.resolve_urn_to_path(urn)

    # Direct URN to path transformation
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
    file_path = data_path_obj / textgroup / work / f"{textgroup}.{work}.{version}.xml"

    return file_path
