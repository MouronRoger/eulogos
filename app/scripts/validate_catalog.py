#!/usr/bin/env python
"""Validate the integrated catalog JSON structure and content.

This script checks the integrated_catalog.json file for structural integrity
and basic content validation, ensuring it meets expected format requirements.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple


def setup_logger(log_level: str = "info") -> logging.Logger:
    """Set up and configure the logger.

    Args:
        log_level: The logging level as a string (debug, info, warning, error, critical)

    Returns:
        Logger: Configured logger instance
    """
    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    level = log_levels.get(log_level.lower(), logging.INFO)

    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()]
    )

    return logging.getLogger("catalog_validator")


def load_catalog(catalog_path: str) -> Dict[str, Any]:
    """Load and parse the catalog JSON file.

    Args:
        catalog_path: Path to the catalog file

    Returns:
        Dict: The parsed catalog as a dictionary

    Raises:
        FileNotFoundError: If the catalog file doesn't exist
        json.JSONDecodeError: If the catalog file contains invalid JSON
    """
    logger = logging.getLogger("catalog_validator")

    if not os.path.exists(catalog_path):
        logger.error(f"Catalog file not found: {catalog_path}")
        raise FileNotFoundError(f"Catalog file not found: {catalog_path}")

    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        logger.info(f"Successfully loaded catalog from {catalog_path}")
        return catalog
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse catalog JSON: {e}")
        raise


def validate_catalog_structure(catalog: Dict[str, Any]) -> List[str]:
    """Validate the overall structure of the catalog.

    Args:
        catalog: The catalog dictionary to validate

    Returns:
        List[str]: List of structural validation errors, empty if no errors
    """
    errors = []

    # Check for required top-level keys
    required_keys = ["metadata", "works"]
    for key in required_keys:
        if key not in catalog:
            errors.append(f"Missing required top-level key: '{key}'")

    # Check metadata structure if it exists
    if "metadata" in catalog:
        metadata = catalog["metadata"]
        if not isinstance(metadata, dict):
            errors.append("'metadata' must be a dictionary")
        else:
            # Check for required metadata fields
            metadata_fields = ["version", "generated", "total_entries"]
            for field in metadata_fields:
                if field not in metadata:
                    errors.append(f"Missing required metadata field: '{field}'")

    # Check works structure if it exists
    if "works" in catalog:
        works = catalog["works"]
        if not isinstance(works, dict):
            errors.append("'works' must be a dictionary")

    return errors


def validate_work_entries(catalog: Dict[str, Any], data_dir: Optional[str] = None) -> List[str]:
    """Validate individual work entries in the catalog.

    Args:
        catalog: The catalog dictionary to validate
        data_dir: Optional path to the data directory to verify file existence

    Returns:
        List[str]: List of validation errors for work entries
    """
    errors = []
    work_ids = set()

    if "works" not in catalog:
        return ["Missing 'works' section in catalog"]

    works = catalog["works"]

    # Required fields for each work entry
    required_fields = ["title", "author", "path", "file_id", "language"]

    for work_id, work in works.items():
        # Check for duplicate work IDs
        if work_id in work_ids:
            errors.append(f"Duplicate work ID: {work_id}")
        work_ids.add(work_id)

        # Check required fields
        for field in required_fields:
            if field not in work:
                errors.append(f"Work {work_id}: Missing required field '{field}'")

        # Check field types
        if "title" in work and not isinstance(work["title"], str):
            errors.append(f"Work {work_id}: 'title' must be a string")

        if "author" in work and not isinstance(work["author"], str):
            errors.append(f"Work {work_id}: 'author' must be a string")

        if "path" in work and not isinstance(work["path"], str):
            errors.append(f"Work {work_id}: 'path' must be a string")

        if "file_id" in work and not isinstance(work["file_id"], str):
            errors.append(f"Work {work_id}: 'file_id' must be a string")

        # Check if files exist if data_dir is provided
        if data_dir and "path" in work:
            file_path = os.path.join(data_dir, work["path"])
            if not os.path.exists(file_path):
                errors.append(f"Work {work_id}: File does not exist: {file_path}")

    return errors


def validate_catalog(catalog_path: str, data_dir: Optional[str] = None) -> Tuple[bool, List[str]]:
    """Validate the catalog file.

    Args:
        catalog_path: Path to the catalog file
        data_dir: Optional path to the data directory

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_validation_errors)
    """
    logger = logging.getLogger("catalog_validator")

    try:
        catalog = load_catalog(catalog_path)

        # Perform validation
        structure_errors = validate_catalog_structure(catalog)
        work_errors = validate_work_entries(catalog, data_dir)

        all_errors = structure_errors + work_errors

        if not all_errors:
            logger.info("Catalog validation successful. No errors found.")
            is_valid = True
        else:
            for error in all_errors:
                logger.error(f"Validation error: {error}")
            logger.error(f"Catalog validation failed with {len(all_errors)} errors.")
            is_valid = False

        return is_valid, all_errors

    except Exception as e:
        logger.error(f"Validation failed due to exception: {str(e)}")
        return False, [f"Exception during validation: {str(e)}"]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Validate the integrated catalog JSON file.")

    parser.add_argument("catalog", type=str, help="Path to the catalog file")
    parser.add_argument("--data-dir", type=str, help="Optional path to the data directory to verify file existence")
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the logging level",
    )

    return parser.parse_args()


def main() -> int:
    """Run the catalog validation process.

    Returns:
        int: Exit code (0 for success, 1 for validation errors)
    """
    args = parse_args()

    # Setup logger
    logger = setup_logger(args.log_level)

    # Resolve paths
    catalog_path = os.path.abspath(args.catalog)
    data_dir = os.path.abspath(args.data_dir) if args.data_dir else None

    logger.info(f"Starting validation of catalog: {catalog_path}")
    if data_dir:
        logger.info(f"Will check file existence in data directory: {data_dir}")

    # Validate the catalog
    is_valid, errors = validate_catalog(catalog_path, data_dir)

    if is_valid:
        logger.info("Catalog validation completed successfully.")
        return 0
    else:
        logger.error(f"Catalog validation failed with {len(errors)} errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
