#!/usr/bin/env python3
"""Script to look up author information by textgroup ID."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add the parent directory to sys.path to make app package available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.catalog_service import CatalogService


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Look up author information by textgroup ID"
    )
    parser.add_argument(
        "--authors", "-a",
        default="author_index.json",
        help="Path to author_index.json file"
    )
    parser.add_argument(
        "textgroups",
        nargs="*",
        help="Textgroup IDs to look up"
    )
    parser.add_argument(
        "--file", "-f",
        help="File containing textgroup IDs, one per line"
    )
    
    return parser.parse_args()


def load_authors(author_path: str) -> Dict:
    """Load the author data from file.
    
    Args:
        author_path: Path to the author_index.json file
    
    Returns:
        The author data as a dictionary
    """
    author_path = Path(author_path)
    if not author_path.exists():
        print(f"Error: Author file not found: {author_path}")
        sys.exit(1)
    
    try:
        with open(author_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading authors: {e}")
        sys.exit(1)


def get_textgroups_from_file(file_path: str) -> List[str]:
    """Read textgroup IDs from a file.
    
    Args:
        file_path: Path to the file containing textgroup IDs
    
    Returns:
        List of textgroup IDs
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Extract textgroup IDs, handling lines like "Textgroup: tlg0001"
            textgroups = []
            for line in f:
                line = line.strip()
                if line.startswith("Textgroup:"):
                    textgroups.append(line.split("Textgroup:")[1].strip())
                elif line:  # Any non-empty line is treated as a textgroup ID
                    textgroups.append(line)
            return textgroups
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def lookup_author(textgroup: str, authors: Dict) -> Optional[Dict]:
    """Look up author information by textgroup ID.
    
    Args:
        textgroup: Textgroup ID to look up
        authors: Author data dictionary
    
    Returns:
        Author information if found, None otherwise
    """
    if textgroup in authors:
        return {
            "id": textgroup,
            **authors[textgroup]
        }
    return None


def format_author_info(author: Dict) -> str:
    """Format author information for display.
    
    Args:
        author: Author information dictionary
    
    Returns:
        Formatted author information string
    """
    if not author:
        return "Not found"
    
    century = author["century"]
    century_str = f"{abs(century)} {'BCE' if century < 0 else 'CE'}"
    
    return f"ID: {author['id']}\nName: {author['name']}\nCentury: {century_str}\nType: {author['type']}"


def main() -> None:
    """Run the author lookup."""
    args = parse_args()
    
    # Load authors
    authors = load_authors(args.authors)
    
    # Get textgroups to look up
    textgroups = args.textgroups
    if args.file:
        textgroups.extend(get_textgroups_from_file(args.file))
    
    if not textgroups:
        print("No textgroups specified. Use the positional arguments or --file option.")
        sys.exit(1)
    
    # Look up authors
    print("=== Author Information ===")
    not_found = []
    
    for textgroup in textgroups:
        print(f"\n[{textgroup}]")
        author = lookup_author(textgroup, authors)
        if author:
            print(format_author_info(author))
        else:
            print("Not found in author index")
            not_found.append(textgroup)
    
    # Summary
    print("\n=== Summary ===")
    print(f"Total textgroups: {len(textgroups)}")
    print(f"Found: {len(textgroups) - len(not_found)}")
    print(f"Not found: {len(not_found)}")
    
    if not_found:
        print("\nTextgroups not found in author index:")
        for textgroup in not_found:
            print(f"- {textgroup}")


if __name__ == "__main__":
    main() 