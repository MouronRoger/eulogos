#!/usr/bin/env python3
"""Script to test the integrated catalog generation with the fixed code."""

import json
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.scripts.generate_integrated_catalog import (  # noqa: E402
    DateTimeEncoder,
    generate_integrated_catalog,
)


def main():
    """Test the integrated catalog generation."""
    # Paths to catalog and author files
    catalog_path = "catalog_index.json"
    author_path = "author_index.json"
    output_path = "new_integrated_catalog.json"

    print(f"Loading catalog data from {catalog_path}")
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)

    print(f"Loading author data from {author_path}")
    with open(author_path, "r", encoding="utf-8") as f:
        author_data = json.load(f)

    print("Generating integrated catalog")
    catalog = generate_integrated_catalog(catalog_data, author_data, lenient=True)

    # Convert to dict
    catalog_dict = catalog.model_dump()

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog_dict, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

    print(f"Generated integrated catalog with {len(catalog.authors)} authors")
    print(f"New catalog saved to {output_path}")


if __name__ == "__main__":
    main()
