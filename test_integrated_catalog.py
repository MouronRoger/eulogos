#!/usr/bin/env python3
"""Script to test the canonical catalog builder for Eulogos."""

import json
import subprocess
import sys
from pathlib import Path


def main():
    """Test the canonical catalog generation."""
    # Paths to source files and output
    data_dir = "data"
    author_path = "author_index.json"
    output_path = "test_integrated_catalog.json"

    print("Testing canonical catalog builder with:")
    print(f"- Data directory: {data_dir}")
    print(f"- Author index: {author_path}")
    print(f"- Output path: {output_path}")

    # Run the canonical catalog builder
    cmd = [
        "python3",
        "app/scripts/canonical_catalog_builder.py",
        f"--data-dir={data_dir}",
        f"--output={output_path}",
        f"--author-index={author_path}",
        "--verbose",
    ]

    print("Running canonical catalog builder...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error running canonical catalog builder:")
        print(result.stderr)
        return 1

    print(result.stdout)

    # Verify the output file was created
    output_file = Path(output_path)
    if not output_file.exists():
        print(f"Error: Output file {output_path} was not created")
        return 1

    # Load and validate the catalog
    print(f"Validating generated catalog: {output_path}")
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        # Count statistics
        author_count = len(catalog)
        work_count = sum(len(author_data["works"]) for author_data in catalog.values())
        edition_count = sum(
            sum(len(work_data["editions"]) for work_data in author_data["works"].values())
            for author_data in catalog.values()
        )
        translation_count = sum(
            sum(len(work_data["translations"]) for work_data in author_data["works"].values())
            for author_data in catalog.values()
        )

        print("Catalog validation successful!")
        print("Generated catalog contains:")
        print(f"- {author_count} authors")
        print(f"- {work_count} works")
        print(f"- {edition_count} editions")
        print(f"- {translation_count} translations")

        return 0
    except Exception as e:
        print(f"Error validating catalog: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
