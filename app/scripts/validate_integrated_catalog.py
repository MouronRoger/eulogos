#!/usr/bin/env python3
"""Script to validate the integrated catalog.

This script validates the integrated_catalog.json file to ensure:
1. The catalog follows the correct structure
2. All file paths referenced in the catalog exist
3. All authors and works are properly related
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from app.models.enhanced_catalog import Catalog

# Add the parent directory to sys.path to make app package available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


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
    logger.add("logs/validate_integrated_catalog.log", rotation="10 MB", level="DEBUG")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Validate the integrated catalog")
    parser.add_argument(
        "--catalog", "-c", default="integrated_catalog.json", help="Path to integrated_catalog.json file"
    )
    parser.add_argument("--data-dir", "-d", default="data", help="Path to data directory containing text files")
    parser.add_argument("--output", "-o", help="Output file for validation results (JSON format)")
    parser.add_argument(
        "--log-level",
        "-l",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the log level",
    )
    parser.add_argument("--strict", "-s", action="store_true", help="Fail validation if any files are missing")

    return parser.parse_args()


def load_catalog(catalog_path: str) -> Catalog:
    """Load the integrated catalog from file.

    Args:
        catalog_path: Path to the integrated catalog JSON file

    Returns:
        Catalog object

    Raises:
        FileNotFoundError: If the catalog file doesn't exist
        ValueError: If the catalog file is not valid JSON or doesn't match the schema
    """
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)

        return Catalog.model_validate(catalog_data)

    except FileNotFoundError:
        logger.error(f"Catalog file not found: {catalog_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in catalog file: {e}")
        raise ValueError(f"Invalid JSON in catalog file: {e}")
    except Exception as e:
        logger.error(f"Error validating catalog schema: {e}")
        raise ValueError(f"Error validating catalog schema: {e}")


def validate_path_consistency(catalog: Catalog, data_dir: Path) -> Dict[str, Any]:
    """Validate that all URNs in the catalog have valid paths.

    Args:
        catalog: The integrated catalog
        data_dir: Path to the data directory

    Returns:
        Dictionary with validation results
    """
    results = {
        "total_urns": 0,
        "urns_with_path": 0,
        "urns_without_path": 0,
        "existing_files": 0,
        "missing_files": 0,
        "urns_without_path_list": [],
        "missing_files_list": [],
        "orphaned_authors": [],
        "orphaned_works": [],
        "valid": True,
    }

    # Track authors with no works, and works with no texts
    authors_with_works = set()
    works_with_texts = set()

    # Check each URN in the catalog
    for author_id, author in catalog.authors.items():
        work_count = 0

        for work_id, work in author.works.items():
            text_count = 0
            work_key = f"{author_id}.{work_id}"

            # Check editions
            for edition_id, edition in work.editions.items():
                results["total_urns"] += 1
                text_count += 1

                if edition.path:
                    results["urns_with_path"] += 1
                    file_path = data_dir / edition.path

                    if file_path.exists():
                        results["existing_files"] += 1
                    else:
                        results["missing_files"] += 1
                        results["missing_files_list"].append((edition.urn, str(file_path)))
                else:
                    results["urns_without_path"] += 1
                    results["urns_without_path_list"].append(edition.urn)

            # Check translations
            for translation_id, translation in work.translations.items():
                results["total_urns"] += 1
                text_count += 1

                if translation.path:
                    results["urns_with_path"] += 1
                    file_path = data_dir / translation.path

                    if file_path.exists():
                        results["existing_files"] += 1
                    else:
                        results["missing_files"] += 1
                        results["missing_files_list"].append((translation.urn, str(file_path)))
                else:
                    results["urns_without_path"] += 1
                    results["urns_without_path_list"].append(translation.urn)

            # Record work has texts
            if text_count > 0:
                works_with_texts.add(work_key)

            work_count += text_count

        # Record author has works
        if work_count > 0:
            authors_with_works.add(author_id)

    # Find orphaned authors (authors with no works or texts)
    for author_id in catalog.authors:
        if author_id not in authors_with_works:
            results["orphaned_authors"].append(author_id)

    # Find orphaned works (works with no texts)
    for author_id, author in catalog.authors.items():
        for work_id in author.works:
            work_key = f"{author_id}.{work_id}"
            if work_key not in works_with_texts:
                results["orphaned_works"].append(work_key)

    # Validate statistics
    stats = catalog.statistics
    calculated_stats = {
        "author_count": len(authors_with_works),
        "work_count": len(works_with_texts),
        "total_urns": results["total_urns"],
    }

    # Check for discrepancies
    if stats.author_count != calculated_stats["author_count"]:
        logger.warning(
            f"Author count mismatch: catalog has {stats.author_count}, calculated {calculated_stats['author_count']}"
        )
        results["statistic_discrepancies"] = True

    if stats.work_count != calculated_stats["work_count"]:
        logger.warning(
            f"Work count mismatch: catalog has {stats.work_count}, calculated {calculated_stats['work_count']}"
        )
        results["statistic_discrepancies"] = True

    # Determine overall validity
    if results["missing_files"] > 0:
        logger.warning(f"Found {results['missing_files']} missing files")
        if len(results["orphaned_authors"]) > 0 or len(results["orphaned_works"]) > 0:
            results["valid"] = False

    return results


def format_results(results: Dict[str, Any]) -> str:
    """Format validation results for display.

    Args:
        results: Validation results

    Returns:
        Formatted results string
    """
    output = []

    output.append("=== Integrated Catalog Validation Results ===")
    output.append(f"Total URNs: {results['total_urns']}")
    output.append(f"URNs with paths: {results['urns_with_path']}")
    output.append(f"URNs without paths: {results['urns_without_path']}")
    output.append(f"Existing files: {results['existing_files']}")
    output.append(f"Missing files: {results['missing_files']}")

    if results.get("orphaned_authors"):
        output.append(f"Orphaned authors: {len(results['orphaned_authors'])}")

    if results.get("orphaned_works"):
        output.append(f"Orphaned works: {len(results['orphaned_works'])}")

    output.append(f"Overall validity: {'VALID' if results['valid'] else 'INVALID'}")

    if results["missing_files"] > 0:
        output.append("\n=== Missing Files (Sample) ===")
        for urn, path in results["missing_files_list"][:10]:  # Show first 10
            output.append(f"URN: {urn}")
            output.append(f"Path: {path}")
            output.append("")

        if len(results["missing_files_list"]) > 10:
            output.append(f"... and {len(results['missing_files_list']) - 10} more")

    if results.get("orphaned_authors") and len(results["orphaned_authors"]) > 0:
        output.append("\n=== Orphaned Authors ===")
        for author_id in results["orphaned_authors"][:10]:  # Show first 10
            output.append(f"Author: {author_id}")

        if len(results["orphaned_authors"]) > 10:
            output.append(f"... and {len(results['orphaned_authors']) - 10} more")

    if results.get("orphaned_works") and len(results["orphaned_works"]) > 0:
        output.append("\n=== Orphaned Works ===")
        for work_key in results["orphaned_works"][:10]:  # Show first 10
            output.append(f"Work: {work_key}")

        if len(results["orphaned_works"]) > 10:
            output.append(f"... and {len(results['orphaned_works']) - 10} more")

    return "\n".join(output)


def main() -> None:
    """Run the integrated catalog validation."""
    args = parse_args()
    setup_logger(args.log_level)

    logger.info("Starting integrated catalog validation")
    logger.info(f"Catalog file: {args.catalog}")
    logger.info(f"Data directory: {args.data_dir}")

    try:
        # Load the catalog
        logger.info(f"Loading catalog from {args.catalog}")
        catalog = load_catalog(args.catalog)
        logger.info(f"Loaded catalog with {len(catalog.authors)} authors")

        # Validate paths
        logger.info("Validating path consistency")
        data_dir = Path(args.data_dir)
        results = validate_path_consistency(catalog, data_dir)

        # Display results
        formatted_results = format_results(results)
        print(formatted_results)

        # Write results to file if requested
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Validation results written to {args.output}")

        # Set exit code based on validity and strict flag
        if not results["valid"] or (args.strict and results["missing_files"] > 0):
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"Error during validation: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
