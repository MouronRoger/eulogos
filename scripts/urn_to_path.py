#!/usr/bin/env python3
"""Script to demonstrate direct URN to path transformation."""


def urn_to_path(urn: str, data_path: str = "data") -> str:
    """Transform a URN directly to a file path.

    Examples:
        urn:cts:greekLit:tlg0532.tlg001.perseus-grc2 -> data/tlg0532/tlg001/tlg0532.tlg001.perseus-grc2.xml
        urn:cts:greekLit:tlg4026.tlg001.1st1K-grc1 -> data/tlg4026/tlg001/tlg4026.tlg001.1st1K-grc1.xml

    Args:
        urn: The URN to transform
        data_path: Base data directory

    Returns:
        The file path corresponding to the URN
    """
    # Extract the identifier after the 3rd colon
    parts = urn.split(":")
    if len(parts) < 4:
        raise ValueError(f"Invalid URN format: {urn}")

    # Get the identifier (e.g., tlg0532.tlg001.perseus-grc2)
    identifier = parts[3].split("#")[0]

    # Split into components
    id_parts = identifier.split(".")
    if len(id_parts) < 3:
        raise ValueError(f"URN missing version information: {urn}")

    # Extract components
    textgroup = id_parts[0]
    work = id_parts[1]
    version = id_parts[2]

    # Construct the path
    path = f"{data_path}/{textgroup}/{work}/{textgroup}.{work}.{version}.xml"

    return path


if __name__ == "__main__":
    import sys

    # Use command line arg if provided, otherwise use examples
    if len(sys.argv) > 1:
        urn = sys.argv[1]
        data_path = sys.argv[2] if len(sys.argv) > 2 else "data"
        path = urn_to_path(urn, data_path)
        print(f"URN: {urn}\nPath: {path}")
    else:
        # Example URNs
        examples = [
            "urn:cts:greekLit:tlg0532.tlg001.perseus-grc2",
            "urn:cts:greekLit:tlg4026.tlg001.1st1K-grc1",
            "urn:cts:greekLit:tlg0552.tlg001.1st1K-grc1",
        ]

        # Display examples
        print("URN to Path Transformation Examples:")
        print("===================================")
        for urn in examples:
            path = urn_to_path(urn)
            print(f"URN:  {urn}")
            print(f"Path: {path}")
            print()
