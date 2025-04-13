#!/usr/bin/env python3
"""Script to validate the catalog index against data files."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger

# Add the parent directory to sys.path to make app package available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.catalog_service import CatalogService
from app.utils.urn import CtsUrn


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
    logger.add("logs/catalog_validation.log", rotation="10 MB", level="DEBUG")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Validate catalog index against data files")
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
        "--data", "-d", 
        default="data", 
        help="Path to data directory"
    )
    parser.add_argument(
        "--output", "-o", 
        help="Output file for validation results (JSON format)"
    )
    parser.add_argument(
        "--log-level", "-l", 
        default="info", 
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the log level"
    )
    parser.add_argument(
        "--missing-only", "-m", 
        action="store_true",
        help="Only report missing files and authors"
    )
    
    return parser.parse_args()


def format_results(results: Dict, missing_only: bool = False) -> str:
    """Format validation results for display.
    
    Args:
        results: Validation results
        missing_only: Only show missing files and authors
    
    Returns:
        Formatted results string
    """
    output = []
    stats = results["stats"]
    
    output.append("=== Catalog Validation Results ===")
    output.append(f"Total catalog entries: {stats['total_catalog_entries']}")
    output.append(f"Total authors: {stats['total_authors']}")
    output.append(f"Missing files: {stats['missing_files']}")
    output.append(f"Missing authors: {stats['missing_authors']}")
    output.append(f"Unlisted files: {stats['unlisted_files']}")
    output.append(f"Validity: {'VALID' if results['validity'] else 'INVALID'}")
    
    if not missing_only or stats['missing_files'] > 0:
        output.append("\n=== Missing Files ===")
        for urn, file_path in results["missing_files"]:
            output.append(f"URN: {urn}")
            output.append(f"File: {file_path}")
            output.append("")
    
    if not missing_only or stats['missing_authors'] > 0:
        output.append("\n=== Textgroups Without Authors ===")
        for textgroup in results["textgroups_without_authors"]:
            output.append(f"Textgroup: {textgroup}")
    
    return "\n".join(output)


def main() -> None:
    """Run the catalog validation."""
    args = parse_args()
    setup_logger(args.log_level)
    
    logger.info(f"Starting catalog validation")
    logger.info(f"Catalog file: {args.catalog}")
    logger.info(f"Author file: {args.authors}")
    logger.info(f"Data directory: {args.data}")
    
    # Validate the catalog
    try:
        service = CatalogService(args.catalog, args.authors, args.data)
        results = service.validate_catalog_files()
        
        # Display results
        formatted_results = format_results(results, args.missing_only)
        print(formatted_results)
        
        # Write results to file if requested
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Validation results written to {args.output}")
        
        # Set exit code based on validity
        sys.exit(0 if results["validity"] else 1)
    
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main() 