#!/usr/bin/env python3
"""Script to merge author_index.json and catalog_index.json into a unified catalog."""

import argparse
import json
import os
import sys
from pathlib import Path

from loguru import logger

# Add the parent directory to sys.path to make app package available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.catalog_service import CatalogService


def setup_logger(log_level: str) -> None:
    """Set up the logger with the specified log level.
    
    Args:
        log_level: The log level to use
    """
    log_levels = {
        "debug": "DEBUG",
        "info": "INFO",
        "warning": "WARNING",
        "error": "ERROR",
        "critical": "CRITICAL",
    }
    level = log_levels.get(log_level.lower(), "INFO")
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(sys.stderr, level=level)
    
    # Add file logger
    os.makedirs("logs", exist_ok=True)
    logger.add("logs/catalog_merge.log", rotation="10 MB", level="DEBUG")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Merge author_index.json and catalog_index.json into a unified catalog"
    )
    parser.add_argument(
        "--catalog", "-c",
        default="catalog_index.json",
        help="Path to catalog_index.json file"
    )
    parser.add_argument(
        "--authors", "-a",
        default="author_index.json",
        help="Path to author_index.json file"
    )
    parser.add_argument(
        "--output", "-o",
        default="unified_catalog.json",
        help="Output file for the unified catalog"
    )
    parser.add_argument(
        "--log-level", "-l",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the log level"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Format the output JSON with indentation for readability"
    )
    
    return parser.parse_args()


def main() -> None:
    """Run the catalog merger."""
    args = parse_args()
    setup_logger(args.log_level)
    
    logger.info(f"Starting catalog merge")
    logger.info(f"Catalog file: {args.catalog}")
    logger.info(f"Author file: {args.authors}")
    logger.info(f"Output file: {args.output}")
    
    try:
        # Create the service and merge catalogs
        service = CatalogService(args.catalog, args.authors)
        unified_catalog = service.create_unified_catalog()
        
        # Convert to dict for serialization
        catalog_dict = unified_catalog.dict()
        
        # Write to file
        indent = 2 if args.pretty else None
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(catalog_dict, f, indent=indent, ensure_ascii=False)
        
        # Show statistics
        stats = catalog_dict["statistics"]
        print("=== Unified Catalog Created ===")
        print(f"Authors: {stats['authorCount']}")
        print(f"Texts: {stats['textCount']}")
        print(f"Greek words: {stats['greekWords']}")
        print(f"Latin words: {stats['latinWords']}")
        print(f"Arabic words: {stats['arabicwords']}")
        print(f"Nodes: {stats['nodeCount']}")
        print(f"Output file: {args.output}")
        
        logger.info(f"Unified catalog created with {stats['authorCount']} authors and {stats['textCount']} texts")
        
    except Exception as e:
        logger.error(f"Error during catalog merge: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 