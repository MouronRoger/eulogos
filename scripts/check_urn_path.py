#!/usr/bin/env python3
"""Simple script to check URN to path resolution and file existence."""

import os
import sys


def urn_to_path(urn: str, data_path: str = "data") -> str:
    """Transform a URN directly to a file path.

    Examples:
        urn:cts:greekLit:tlg0532.tlg001.perseus-grc2 -> data/tlg0532/tlg001/tlg0532.tlg001.perseus-grc2.xml

    Args:
        urn: The URN to transform
        data_path: Base data directory

    Returns:
        The file path corresponding to the URN
    """
    parts = urn.split(":")
    if len(parts) < 4:
        return f"Invalid URN format: {urn}"

    # Get the identifier (e.g., tlg0532.tlg001.perseus-grc2)
    identifier = parts[3].split("#")[0]

    # Split into components
    id_parts = identifier.split(".")
    if len(id_parts) < 3:
        return f"URN missing version information: {urn}"

    # Extract components
    textgroup = id_parts[0]
    work = id_parts[1]
    version = id_parts[2]

    # Construct the path
    path = f"{data_path}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml"

    return path


def check_alternate_paths(urn: str, data_path: str = "data"):
    """Check various alternative path formats for the given URN.

    Args:
        urn: The URN to check
        data_path: Base data directory

    Returns:
        List of path information dictionaries
    """
    results = []

    # Parse URN to components
    parts = urn.split(":")
    if len(parts) < 4:
        return []

    identifier = parts[3].split("#")[0]
    id_parts = identifier.split(".")
    if len(id_parts) < 3:
        return []

    textgroup = id_parts[0]
    work = id_parts[1]
    version = id_parts[2]
    namespace = parts[2] if len(parts) >= 3 else "greekLit"

    # Try different path formats
    alternates = [
        f"{data_path}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml",
        f"{data_path}/{namespace}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml",
        f"{data_path}/{textgroup}.{work}.{version}.xml",
        f"{data_path}/{textgroup}/{textgroup}.{work}.{version}.xml",
    ]

    for path in alternates:
        exists = os.path.exists(path)
        is_file = os.path.isfile(path) if exists else False

        results.append({"path": path, "exists": exists, "is_file": is_file})

    return results


def main():
    """Run the script with command-line arguments."""
    # Check if URN provided
    if len(sys.argv) < 2:
        print("Usage: python check_urn_path.py <URN> [<data_path>]")
        print("Example: python check_urn_path.py urn:cts:greekLit:tlg0532.tlg001.perseus-grc2 /path/to/data")

        # Show examples
        print("\nExamples:")
        examples = [
            "urn:cts:greekLit:tlg0532.tlg001.perseus-grc2",
            "urn:cts:greekLit:tlg4026.tlg001.1st1K-grc1",
            "urn:cts:greekLit:tlg0552.tlg001.1st1K-grc1",
            "urn:cts:greekLit:tlg2948.tlg001.1st1K-grc1",
        ]

        for urn in examples:
            print(f"\nURN: {urn}")
            path = urn_to_path(urn)
            exists = os.path.exists(path)
            print(f"Path: {path}")
            print(f"Exists: {exists}")

        return

    # Get URN and data path
    urn = sys.argv[1]
    data_path = sys.argv[2] if len(sys.argv) > 2 else "data"

    # Convert to absolute path if not already
    if not os.path.isabs(data_path):
        data_path = os.path.abspath(data_path)

    # Check direct path
    direct_path = urn_to_path(urn, data_path)
    exists = os.path.exists(direct_path)
    is_file = os.path.isfile(direct_path) if exists else False

    print(f"URN: {urn}")
    print(f"Direct path: {direct_path}")
    print(f"Exists: {exists}")
    print(f"Is file: {is_file}")

    # Check alternate paths
    print("\nChecking alternate path formats:")
    alternates = check_alternate_paths(urn, data_path)

    for i, alt in enumerate(alternates):
        print(f"\nAlternate path {i+1}:")
        print(f"Path: {alt['path']}")
        print(f"Exists: {alt['exists']}")
        print(f"Is file: {alt['is_file']}")


if __name__ == "__main__":
    main()
