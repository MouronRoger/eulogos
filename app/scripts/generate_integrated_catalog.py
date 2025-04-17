#!/usr/bin/env python3
"""Script to generate the integrated catalog from existing data sources.

This script reads from the existing catalog_index.json and author_index.json files
and generates an integrated_catalog.json file that follows the enhanced catalog
model structure defined in app/models/enhanced_catalog.py.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from app.models.enhanced_catalog import (
    Author,
    Catalog,
    CatalogStatistics,
    ModelVersion,
    TextVersion,
    Work,
)
from app.models.enhanced_urn import EnhancedURN

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
    logger.add("logs/generate_integrated_catalog.log", rotation="10 MB", level="DEBUG")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Generate integrated catalog from existing data sources")
    parser.add_argument("--catalog", "-c", default="catalog_index.json", help="Path to catalog_index.json file")
    parser.add_argument("--authors", "-a", default="author_index.json", help="Path to author_index.json file")
    parser.add_argument(
        "--output", "-o", default="integrated_catalog.json", help="Output file for the integrated catalog"
    )
    parser.add_argument("--data-dir", "-d", default="data", help="Path to the data directory containing text files")
    parser.add_argument(
        "--log-level",
        "-l",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set the log level",
    )
    parser.add_argument(
        "--pretty", "-p", action="store_true", help="Format the output JSON with indentation for readability"
    )
    parser.add_argument(
        "--validate", "-v", action="store_true", help="Validate paths in the catalog against actual files"
    )
    parser.add_argument(
        "--lenient", "-len", action="store_true", help="Be lenient with URN validation to include non-standard URNs"
    )

    return parser.parse_args()


def load_json_file(file_path: str) -> Dict:
    """Load JSON data from a file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dictionary containing the JSON data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise


def validate_paths(catalog: Catalog, data_dir: Path) -> Dict[str, Any]:
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
    }

    # Check each URN in the catalog
    for author_id, author in catalog.authors.items():
        for work_id, work in author.works.items():
            # Check editions
            for edition_id, edition in work.editions.items():
                results["total_urns"] += 1

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

    return results


def parse_urn_components(urn_str: str) -> Dict[str, Optional[str]]:
    """Parse a URN string into components manually, even if non-standard.

    Args:
        urn_str: The URN string to parse

    Returns:
        Dictionary with URN components
    """
    # Default values
    components = {"namespace": None, "textgroup": None, "work": None, "version": None, "reference": None}

    # Remove the reference part if present
    if "#" in urn_str:
        urn_str = urn_str.split("#")[0]

    # Split by colon
    parts = urn_str.split(":")

    # Parse namespace (handling both standard and non-standard URNs)
    if len(parts) >= 3:
        if parts[0] == "urn" and parts[1] == "cts":
            # Standard CTS URN
            components["namespace"] = parts[2]
        elif parts[0] == "urn" and parts[1] in ["nbn", "doi"]:
            # Non-standard URN like urn:nbn:de:...
            components["namespace"] = parts[2]

    # Parse identifier
    if len(parts) >= 4:
        identifier = parts[3]
        if ":" in identifier:
            # Handle case where reference is part of the identifier
            id_parts = identifier.split(":", 1)
            identifier = id_parts[0]
            if len(id_parts) > 1:
                components["reference"] = id_parts[1]

        # Split identifier by dot
        id_parts = identifier.split(".")
        if len(id_parts) >= 1:
            components["textgroup"] = id_parts[0]
        if len(id_parts) >= 2:
            components["work"] = id_parts[1]
        if len(id_parts) >= 3:
            components["version"] = id_parts[2]

    # Parse reference if it's a separate part
    if len(parts) >= 5:
        components["reference"] = parts[4]

    return components


def generate_integrated_catalog(catalog_data: Dict, authors_data: Dict, lenient: bool = False) -> Catalog:
    """Generate an integrated catalog from existing data sources.

    Args:
        catalog_data: Data from catalog_index.json
        authors_data: Data from author_index.json
        lenient: Whether to be lenient with URN validation

    Returns:
        Integrated catalog
    """
    # Create a new integrated catalog
    catalog = Catalog(
        statistics=CatalogStatistics(),
        authors={},
        model_version=ModelVersion(version="1.0.0", last_updated=datetime.utcnow()),
    )

    # Create authors dictionary
    author_dict = {}
    if "authors" in authors_data:
        for author_id, author_data in authors_data["authors"].items():
            author_dict[author_id] = Author(
                id=author_id,
                name=author_data.get("name", "Unknown"),
                century=author_data.get("century"),
                type=author_data.get("type", "Author"),
                works={},
            )

    # Process catalog entries
    text_entries = []
    if "texts" in catalog_data:
        text_entries = catalog_data["texts"]
    elif "catalog" in catalog_data:
        text_entries = catalog_data["catalog"]

    # Statistics
    greek_word_count = 0
    latin_word_count = 0
    arabic_word_count = 0
    edition_count = 0
    translation_count = 0

    # Track skipped texts
    skipped_count = 0

    for text in text_entries:
        try:
            urn_str = text["urn"]

            # Try to use the EnhancedURN model for standard URNs
            try:
                urn_obj = EnhancedURN(value=urn_str)
                parsed_components = {
                    "namespace": urn_obj.namespace,
                    "textgroup": urn_obj.textgroup,
                    "work": urn_obj.work,
                    "version": urn_obj.version,
                    "reference": urn_obj.reference,
                }
            except ValueError:
                if not lenient:
                    logger.warning(f"Skipping text with invalid URN format: {urn_str}")
                    skipped_count += 1
                    continue

                # For non-standard URNs, manually parse the components
                logger.debug(f"Using manual parsing for non-standard URN: {urn_str}")
                parsed_components = parse_urn_components(urn_str)

            # Skip if missing essential components
            if not parsed_components["textgroup"] or not parsed_components["work"] or not parsed_components["version"]:
                logger.warning(f"Skipping text with incomplete URN: {urn_str}")
                skipped_count += 1
                continue

            # Get or create author
            author_id = parsed_components["textgroup"]
            if author_id not in author_dict:
                logger.debug(f"Creating author entry for {author_id}")
                author_dict[author_id] = Author(
                    id=author_id, name=text.get("group_name", f"Author {author_id}"), works={}
                )

            author = author_dict[author_id]

            # Get or create work
            work_id = parsed_components["work"]
            if work_id not in author.works:
                logger.debug(f"Creating work entry for {author_id}.{work_id}")
                work_urn = f"urn:cts:{parsed_components['namespace'] or 'unknown'}:{author_id}.{work_id}"
                author.works[work_id] = Work(
                    id=work_id,
                    title=text.get("work_name", f"Work {work_id}"),
                    urn=work_urn,
                    language=text.get("language", ""),
                    editions={},
                    translations={},
                )

            work = author.works[work_id]

            # Create text version
            text_version = TextVersion(
                urn=text["urn"],
                label=text.get("work_name", ""),
                language=text.get("language", ""),
                path=text.get("path", ""),
                word_count=text.get("wordcount", 0),
                archived=text.get("archived", False),
                favorite=text.get("favorite", False),
            )

            # Add to appropriate collection based on language
            version_id = parsed_components["version"]
            work_language = work.language.lower()
            text_language = text.get("language", "").lower()

            # Determine if this is an edition or translation
            is_edition = work_language == text_language or not work_language

            if is_edition:
                work.editions[version_id] = text_version
                edition_count += 1
            else:
                work.translations[version_id] = text_version
                translation_count += 1

            # Update language specific word counts
            word_count = text.get("wordcount", 0)
            if text_language.startswith("grc"):
                greek_word_count += word_count
            elif text_language.startswith("lat"):
                latin_word_count += word_count
            elif text_language.startswith("ara"):
                arabic_word_count += word_count

        except Exception as e:
            logger.error(f"Error processing text {text.get('urn', 'unknown')}: {e}")
            skipped_count += 1

    # Set all authors in the catalog
    catalog.authors = author_dict

    # Update statistics
    catalog.statistics.author_count = len(author_dict)
    catalog.statistics.work_count = sum(len(author.works) for author in author_dict.values())
    catalog.statistics.edition_count = edition_count
    catalog.statistics.translation_count = translation_count
    catalog.statistics.greek_word_count = greek_word_count
    catalog.statistics.latin_word_count = latin_word_count
    catalog.statistics.arabic_word_count = arabic_word_count

    logger.info(f"Processed {len(text_entries)} texts, skipped {skipped_count}")

    return catalog


def main() -> None:
    """Run the integrated catalog generator."""
    args = parse_args()
    setup_logger(args.log_level)

    logger.info("Starting integrated catalog generation")
    logger.info(f"Catalog file: {args.catalog}")
    logger.info(f"Author file: {args.authors}")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Data directory: {args.data_dir}")

    try:
        # Load existing data sources
        catalog_data = load_json_file(args.catalog)
        authors_data = load_json_file(args.authors)

        # Generate integrated catalog
        logger.info("Generating integrated catalog")
        integrated_catalog = generate_integrated_catalog(catalog_data, authors_data, lenient=args.lenient)

        # Validate paths if requested
        if args.validate:
            logger.info("Validating paths")
            data_dir = Path(args.data_dir)
            validation_results = validate_paths(integrated_catalog, data_dir)
            logger.info(
                f"Path validation complete: {validation_results['existing_files']} existing files, "
                f"{validation_results['missing_files']} missing"
            )

            if validation_results["missing_files"] > 0:
                logger.warning(f"Found {validation_results['missing_files']} missing files")
                for urn, path in validation_results["missing_files_list"][:10]:  # Show first 10
                    logger.warning(f"Missing: {urn} -> {path}")

                if len(validation_results["missing_files_list"]) > 10:
                    logger.warning(f"... and {len(validation_results['missing_files_list']) - 10} more")

        # Convert to dict for serialization
        catalog_dict = integrated_catalog.model_dump()

        # Write to file using custom JSON encoder for datetime
        indent = 2 if args.pretty else None
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(catalog_dict, f, indent=indent, ensure_ascii=False, cls=DateTimeEncoder)

        # Show statistics
        stats = catalog_dict["statistics"]
        print("=== Integrated Catalog Created ===")
        print(f"Authors: {stats['author_count']}")
        print(f"Works: {stats['work_count']}")
        print(f"Editions: {stats['edition_count']}")
        print(f"Translations: {stats['translation_count']}")
        print(f"Greek words: {stats['greek_word_count']}")
        print(f"Latin words: {stats['latin_word_count']}")
        print(f"Arabic words: {stats['arabic_word_count']}")
        print(f"Output file: {args.output}")

        logger.info(
            f"Integrated catalog created with {stats['author_count']} authors and " f"{stats['work_count']} works"
        )

    except Exception as e:
        logger.error(f"Error during catalog generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
