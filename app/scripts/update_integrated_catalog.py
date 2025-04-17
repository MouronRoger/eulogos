#!/usr/bin/env python3
"""Script to update the integrated catalog by scanning the data directory.

This script updates the integrated_catalog.json file by:
1. Scanning the data directory for changes
2. Identifying new, modified, and removed files
3. Updating the catalog accordingly
4. Preserving the enhanced catalog structure
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.models.enhanced_catalog import (
    Author,
    Catalog,
    CatalogStatistics,
    ModelVersion,
    TextVersion,
    Work,
)
from app.scripts.catalog_generator.catalog_builder import generate_catalog
from app.scripts.catalog_generator.config import CatalogGeneratorConfig

# Add the parent directory to sys.path to make app package available
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj):
        """Convert objects to JSON serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def setup_logger(log_level: str) -> logging.Logger:
    """Set up the logger with the specified log level.

    Args:
        log_level: The log level to use

    Returns:
        Configured logger
    """
    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    level = log_levels.get(log_level.lower(), logging.INFO)

    # Configure logging
    logger = logging.getLogger("update_catalog")
    logger.setLevel(level)

    # Remove default handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(console_handler)

    # Add file handler for logs
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler("logs/update_integrated_catalog.log")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    return logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Update the integrated catalog by scanning the data directory")
    parser.add_argument(
        "--catalog",
        "-c",
        default="integrated_catalog.json",
        help="Path to existing integrated_catalog.json file (default: integrated_catalog.json)",
    )
    parser.add_argument("--data-dir", "-d", default="data", help="Path to the data directory (default: data)")
    parser.add_argument(
        "--author-index",
        "-a",
        default="author_index.json",
        help="Path to author_index.json file (default: author_index.json)",
    )
    parser.add_argument(
        "--temporary",
        "-t",
        default="temp_catalog.json",
        help="Temporary file for generated catalog (default: temp_catalog.json)",
    )
    parser.add_argument(
        "--log-level",
        "-l",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the log level (default: info)",
    )
    parser.add_argument("--force", "-f", action="store_true", help="Force update even if no changes are detected")
    parser.add_argument(
        "--backup", "-b", action="store_true", help="Create a backup of the existing catalog before updating"
    )
    parser.add_argument(
        "--pretty", "-p", action="store_true", help="Format the output JSON with indentation for readability"
    )

    return parser.parse_args()


def load_catalog(catalog_path: str, logger: logging.Logger) -> Optional[Catalog]:
    """Load the integrated catalog from file.

    Args:
        catalog_path: Path to the integrated catalog JSON file
        logger: Logger instance

    Returns:
        Loaded catalog or None if error occurs
    """
    try:
        logger.info(f"Loading existing catalog from {catalog_path}")

        if not os.path.exists(catalog_path):
            logger.warning(f"Catalog file not found: {catalog_path}")
            return None

        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)

        return Catalog.model_validate(catalog_data)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in catalog file: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        return None


def generate_new_catalog(data_dir: str, author_index: str, output_file: str, logger: logging.Logger) -> bool:
    """Generate a new catalog by scanning the data directory.

    Args:
        data_dir: Path to the data directory
        author_index: Path to the author index file
        output_file: Path for the generated catalog
        logger: Logger instance

    Returns:
        True if catalog was generated successfully, False otherwise
    """
    try:
        logger.info(f"Generating new catalog from {data_dir}")

        # Configure the catalog generator
        config = CatalogGeneratorConfig(
            data_dir=Path(data_dir),
            author_index=Path(author_index),
            output_file=Path(output_file),
            log_level="debug" if logger.level == logging.DEBUG else "info",
            include_content_sample=False,
        )

        # Define progress callback
        def progress_callback(progress: int, message: str):
            logger.info(f"[{progress:3d}%] {message}")

        # Generate the catalog
        generate_catalog(config, progress_callback)

        return True

    except Exception as e:
        logger.error(f"Error generating new catalog: {e}")
        return False


def detect_catalog_changes(
    old_catalog_path: str, new_catalog_path: str, logger: logging.Logger
) -> Tuple[bool, Dict[str, Any]]:
    """Detect changes between old and new catalogs.

    Args:
        old_catalog_path: Path to the old catalog
        new_catalog_path: Path to the new catalog
        logger: Logger instance

    Returns:
        Tuple of (changes_detected, change_stats)
    """
    try:
        # Load catalogs
        with open(old_catalog_path, "r", encoding="utf-8") as f:
            old_catalog = json.load(f)

        with open(new_catalog_path, "r", encoding="utf-8") as f:
            new_catalog = json.load(f)

        # Extract URNs from old catalog
        old_urns = set()
        for author_id, author in old_catalog.get("authors", {}).items():
            for work_id, work in author.get("works", {}).items():
                for edition_id, edition in work.get("editions", {}).items():
                    if "urn" in edition:
                        old_urns.add(edition["urn"])
                for trans_id, trans in work.get("translations", {}).items():
                    if "urn" in trans:
                        old_urns.add(trans["urn"])

        # Extract URNs from new catalog
        new_urns = set()
        for author_id, author in new_catalog.get("authors", {}).items():
            for work_id, work in author.get("works", {}).items():
                for edition_id, edition in work.get("editions", {}).items():
                    if "urn" in edition:
                        new_urns.add(edition["urn"])
                for trans_id, trans in work.get("translations", {}).items():
                    if "urn" in trans:
                        new_urns.add(trans["urn"])

        # Identify added and removed URNs
        added_urns = new_urns - old_urns
        removed_urns = old_urns - new_urns

        # Get old and new author/work counts
        old_author_count = len(old_catalog.get("authors", {}))
        new_author_count = len(new_catalog.get("authors", {}))

        old_work_count = sum(len(author.get("works", {})) for author in old_catalog.get("authors", {}).values())
        new_work_count = sum(len(author.get("works", {})) for author in new_catalog.get("authors", {}).values())

        # Determine if there are changes
        changes_detected = bool(
            added_urns or removed_urns or old_author_count != new_author_count or old_work_count != new_work_count
        )

        # Compile change statistics
        change_stats = {
            "added_urns": list(added_urns),
            "removed_urns": list(removed_urns),
            "added_urns_count": len(added_urns),
            "removed_urns_count": len(removed_urns),
            "old_author_count": old_author_count,
            "new_author_count": new_author_count,
            "old_work_count": old_work_count,
            "new_work_count": new_work_count,
        }

        return changes_detected, change_stats

    except Exception as e:
        logger.error(f"Error detecting changes: {e}")
        return True, {"error": str(e)}


def update_catalog(
    old_catalog_path: str, new_catalog_path: str, output_path: str, logger: logging.Logger, pretty: bool = False
) -> bool:
    """Update the existing catalog with changes from the new catalog.

    Args:
        old_catalog_path: Path to the old catalog
        new_catalog_path: Path to the new catalog
        output_path: Path to save the updated catalog
        logger: Logger instance
        pretty: Whether to format output with indentation

    Returns:
        True if update was successful, False otherwise
    """
    try:
        # Load the old catalog as a Catalog model
        old_catalog = load_catalog(old_catalog_path, logger)
        if not old_catalog:
            logger.error("Failed to load old catalog")
            return False

        # Load the new catalog as JSON
        with open(new_catalog_path, "r", encoding="utf-8") as f:
            new_catalog_data = json.load(f)

        # Create a new catalog object
        updated_catalog = Catalog(
            statistics=CatalogStatistics(),
            authors={},
            model_version=ModelVersion(version=old_catalog.model_version.version, last_updated=datetime.utcnow()),
        )

        # Process authors, works, and texts from the new catalog
        for author_id, author_data in new_catalog_data.get("authors", {}).items():
            # Create author
            updated_catalog.authors[author_id] = Author(
                id=author_id,
                name=author_data.get("name", "Unknown"),
                century=author_data.get("century"),
                type=author_data.get("type", "Author"),
                works={},
            )

            # Process works
            for work_id, work_data in author_data.get("works", {}).items():
                # Create work
                updated_catalog.authors[author_id].works[work_id] = Work(
                    id=work_id,
                    title=work_data.get("title", ""),
                    urn=work_data.get("urn", ""),
                    language=work_data.get("language", ""),
                    editions={},
                    translations={},
                )

                # Process editions
                for edition_id, edition_data in work_data.get("editions", {}).items():
                    # Check if this edition existed in the old catalog
                    edition_urn = edition_data.get("urn", "")
                    old_edition = None

                    # Try to find the edition in the old catalog to preserve metadata
                    if author_id in old_catalog.authors and work_id in old_catalog.authors[author_id].works:
                        if edition_id in old_catalog.authors[author_id].works[work_id].editions:
                            old_edition = old_catalog.authors[author_id].works[work_id].editions[edition_id]

                    # Create edition with preserved metadata from old catalog where available
                    updated_catalog.authors[author_id].works[work_id].editions[edition_id] = TextVersion(
                        urn=edition_urn,
                        label=edition_data.get("label", ""),
                        description=edition_data.get("description") if old_edition is None else old_edition.description,
                        language=edition_data.get("lang", ""),
                        path=edition_data.get("path", ""),
                        word_count=edition_data.get("wordcount", 0),
                        editor=edition_data.get("editor") if old_edition is None else old_edition.editor,
                        translator=edition_data.get("translator") if old_edition is None else old_edition.translator,
                        archived=False if old_edition is None else old_edition.archived,
                        favorite=False if old_edition is None else old_edition.favorite,
                    )

                # Process translations
                for trans_id, trans_data in work_data.get("translations", {}).items():
                    # Check if this translation existed in the old catalog
                    trans_urn = trans_data.get("urn", "")
                    old_trans = None

                    # Try to find the translation in the old catalog to preserve metadata
                    if author_id in old_catalog.authors and work_id in old_catalog.authors[author_id].works:
                        if trans_id in old_catalog.authors[author_id].works[work_id].translations:
                            old_trans = old_catalog.authors[author_id].works[work_id].translations[trans_id]

                    # Create translation with preserved metadata from old catalog where available
                    updated_catalog.authors[author_id].works[work_id].translations[trans_id] = TextVersion(
                        urn=trans_urn,
                        label=trans_data.get("label", ""),
                        description=trans_data.get("description") if old_trans is None else old_trans.description,
                        language=trans_data.get("lang", ""),
                        path=trans_data.get("path", ""),
                        word_count=trans_data.get("wordcount", 0),
                        editor=trans_data.get("editor") if old_trans is None else old_trans.editor,
                        translator=trans_data.get("translator") if old_trans is None else old_trans.translator,
                        archived=False if old_trans is None else old_trans.archived,
                        favorite=False if old_trans is None else old_trans.favorite,
                    )

        # Update statistics
        stats = new_catalog_data.get("statistics", {})
        updated_catalog.statistics.author_count = len(updated_catalog.authors)
        updated_catalog.statistics.work_count = sum(len(author.works) for author in updated_catalog.authors.values())
        updated_catalog.statistics.edition_count = sum(
            sum(len(work.editions) for work in author.works.values()) for author in updated_catalog.authors.values()
        )
        updated_catalog.statistics.translation_count = sum(
            sum(len(work.translations) for work in author.works.values()) for author in updated_catalog.authors.values()
        )
        updated_catalog.statistics.greek_word_count = stats.get("greekWords", 0)
        updated_catalog.statistics.latin_word_count = stats.get("latinWords", 0)
        updated_catalog.statistics.arabic_word_count = stats.get("arabicwords", 0)

        # Save updated catalog
        catalog_dict = updated_catalog.model_dump()
        indent = 2 if pretty else None

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(catalog_dict, f, indent=indent, ensure_ascii=False, cls=DateTimeEncoder)

        logger.info(f"Updated catalog saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error updating catalog: {e}")
        return False


def main() -> None:
    """Run the integrated catalog update process."""
    # Parse arguments
    args = parse_args()

    # Set up logger
    logger = setup_logger(args.log_level)

    logger.info("Starting integrated catalog update")
    logger.info(f"Existing catalog: {args.catalog}")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Author index: {args.author_index}")

    # Create backup if requested
    if args.backup and os.path.exists(args.catalog):
        backup_path = f"{args.catalog}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            import shutil

            shutil.copy2(args.catalog, backup_path)
            logger.info(f"Created backup of existing catalog: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")

    # Generate new catalog by scanning data directory
    if not generate_new_catalog(args.data_dir, args.author_index, args.temporary, logger):
        logger.error("Failed to generate new catalog")
        sys.exit(1)

    # Detect changes between old and new catalogs
    if os.path.exists(args.catalog):
        changes_detected, change_stats = detect_catalog_changes(args.catalog, args.temporary, logger)

        if not changes_detected and not args.force:
            logger.info("No changes detected. Use --force to update anyway.")
            os.remove(args.temporary)
            sys.exit(0)

        # Log changes
        logger.info(
            f"Changes detected: {change_stats['added_urns_count']} new URNs, "
            f"{change_stats['removed_urns_count']} removed URNs"
        )

        if change_stats["added_urns_count"] > 0:
            logger.info("Added URNs (sample):")
            for urn in change_stats["added_urns"][:5]:
                logger.info(f"  + {urn}")
            if len(change_stats["added_urns"]) > 5:
                logger.info(f"  + ... and {len(change_stats['added_urns']) - 5} more")

        if change_stats["removed_urns_count"] > 0:
            logger.info("Removed URNs (sample):")
            for urn in change_stats["removed_urns"][:5]:
                logger.info(f"  - {urn}")
            if len(change_stats["removed_urns"]) > 5:
                logger.info(f"  - ... and {len(change_stats['removed_urns']) - 5} more")
    else:
        logger.info("No existing catalog found. Creating new one.")
        changes_detected = True

    # Update catalog
    if changes_detected or args.force:
        if update_catalog(args.catalog, args.temporary, args.catalog, logger, args.pretty):
            logger.info("Catalog update completed successfully")
        else:
            logger.error("Failed to update catalog")
            sys.exit(1)

    # Clean up temporary file
    try:
        if os.path.exists(args.temporary):
            os.remove(args.temporary)
    except Exception as e:
        logger.warning(f"Failed to remove temporary file {args.temporary}: {e}")

    logger.info("Update process completed")


if __name__ == "__main__":
    main()
