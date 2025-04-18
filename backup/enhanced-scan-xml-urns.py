#!/usr/bin/env python3
"""
Script to scan XML files in the data directory and generate an integrated catalog.

This script walks through the data directory, identifies all XML files and __cts__.xml files,
extracts information about authors, works, and editions/translations, and creates a unified
JSON catalog that combines author metadata with text information in a hierarchical structure.

Features:
- Integrates author metadata (century, type) from author_index.json
- Extracts editor/translator information from TEI XML headers
- Orders editions and translations as pairs (original language first, then translations)
- Includes comprehensive statistics about the corpus
- Maintains a hierarchical structure to preserve the author-work-edition relationship
"""

import argparse
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# XML namespaces
NAMESPACE = {"ti": "http://chs.harvard.edu/xmlns/cts"}
TEI_NAMESPACE = {"tei": "http://www.tei-c.org/ns/1.0"}


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate an integrated catalog of authors and works from XML files.")
    parser.add_argument("--data-dir", default="data", help="Path to the data directory (default: data)")
    parser.add_argument(
        "--output",
        default="integrated_catalog.json",
        help="Output file path (default: integrated_catalog.json)",
    )
    parser.add_argument(
        "--author-index",
        default="author_index.json",
        help="Path to author_index.json file (default: author_index.json)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--stats-only", action="store_true", help="Only generate corpus statistics without texts")
    parser.add_argument(
        "--include-content-sample",
        action="store_true",
        help="Include a small sample of text content in the catalog (first paragraph)",
    )
    return parser.parse_args()


def load_author_index(author_path: str) -> Dict[str, Dict[str, Any]]:
    """Load author metadata from author_index.json.

    Args:
        author_path: Path to the author_index.json file

    Returns:
        Dictionary of author metadata indexed by author ID
    """
    try:
        with open(author_path, "r", encoding="utf-8") as f:
            author_data = json.load(f)
            logger.info(f"Loaded author metadata for {len(author_data)} authors from {author_path}")
            return author_data
    except Exception as e:
        logger.error(f"Error loading author index from {author_path}: {e}")
        return {}


def extract_editor_info(xml_file_path: str) -> Dict[str, str]:
    """Extract editor information from a TEI XML file.

    Args:
        xml_file_path: Path to the TEI XML file

    Returns:
        Dictionary containing editor and translator information
    """
    editor_info = {"editor": None, "translator": None}

    try:
        # Extract the first part of the file to speed up parsing (only need header)
        with open(xml_file_path, "r", encoding="utf-8", errors="replace") as f:
            xml_content = f.read(10000)  # Read first 10KB which should include the header

        # Extract editor information using regex for speed
        # Look for standard editor tags
        editor_match = re.search(r"<editor[^>]*>([^<]+)</editor>", xml_content)
        if editor_match:
            editor_info["editor"] = editor_match.group(1).strip()

        # Look for translators specifically
        translator_match = re.search(r'<editor role="translator">([^<]+)</editor>', xml_content)
        if translator_match:
            editor_info["translator"] = translator_match.group(1).strip()

    except Exception as e:
        logger.warning(f"Error extracting editor info from {xml_file_path}: {e}")

    return editor_info


def get_language_display_name(lang_code: str) -> str:
    """Convert language code to display name.

    Args:
        lang_code: ISO language code

    Returns:
        Display name for the language
    """
    language_map = {
        "grc": "Greek",
        "eng": "English",
        "lat": "Latin",
        "fre": "French",
        "ger": "German",
        "ita": "Italian",
        "spa": "Spanish",
        "ara": "Arabic",
        "heb": "Hebrew",
        "cop": "Coptic",
    }
    return language_map.get(lang_code, lang_code)


def scan_data_directory(data_dir: str, author_metadata: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Scan the data directory for XML files and build an integrated catalog.

    Args:
        data_dir: Path to the data directory
        author_metadata: Author metadata from author_index.json

    Returns:
        Integrated catalog with author metadata and works
    """
    # Initialize the catalog structure
    catalog = {
        "statistics": {
            "authorCount": 0,
            "textCount": 0,
            "greekWords": 0,
            "latinWords": 0,
            "arabicwords": 0,
            "editions": 0,
            "translations": 0,
            "files": 0,
        },
        "authors": OrderedDict(),
    }

    # Track processing statistics
    total_xml_files = 0
    processed_cts_files = 0

    logger.info(f"Scanning data directory: {data_dir}")

    # First pass: Process author-level __cts__.xml files
    for root, dirs, files in os.walk(data_dir):
        # Check if this is an author directory with a __cts__.xml file
        if "__cts__.xml" in files:
            author_cts_path = os.path.join(root, "__cts__.xml")

            # Get the author ID from the path
            path_parts = Path(root).parts
            if len(path_parts) < 2:  # Must have at least data_dir/author_id
                continue

            author_id = path_parts[-1]  # Last part of the path is author_id

            try:
                logger.info(f"Processing author: {author_cts_path}")

                # Get author metadata from author_index.json
                author_info = author_metadata.get(author_id, {})

                # Process the author CTS file
                process_author_cts(author_cts_path, catalog, author_id, author_info)

                processed_cts_files += 1
            except Exception as e:
                logger.error(f"Error processing author {author_cts_path}: {e}")

    # Second pass: Process work-level __cts__.xml files and actual text files
    for root, dirs, files in os.walk(data_dir):
        # Skip processing if no XML files in this directory
        xml_files = [f for f in files if f.endswith(".xml") and f != "__cts__.xml"]
        total_xml_files += len(xml_files)

        if "__cts__.xml" in files and len(xml_files) > 0:
            work_cts_path = os.path.join(root, "__cts__.xml")

            # Extract path components to identify author and work
            path_parts = Path(root).parts
            if len(path_parts) < 3:  # Must have at least data_dir/author_id/work_id
                continue

            author_id = path_parts[-2]  # Second-to-last part is author_id
            work_id = path_parts[-1]  # Last part is work_id

            # Skip if author not in catalog
            if author_id not in catalog["authors"]:
                continue

            try:
                logger.info(f"Processing work: {work_cts_path}")

                # Process the work CTS file
                process_work_cts(work_cts_path, xml_files, root, catalog, author_id, work_id)

                processed_cts_files += 1
            except Exception as e:
                logger.error(f"Error processing work {work_cts_path}: {e}")

    # Sort authors alphabetically by name
    catalog["authors"] = OrderedDict(sorted(catalog["authors"].items(), key=lambda x: x[1].get("name", "")))

    # Sort each author's works and their editions
    for author_id, author_data in catalog["authors"].items():
        # Sort works
        if "works" in author_data:
            author_data["works"] = OrderedDict(
                sorted(author_data["works"].items(), key=lambda x: x[1].get("title", ""))
            )

            # For each work, sort editions and translations
            for work_id, work_data in author_data["works"].items():
                # Create ordered pairs of editions and translations
                ordered_editions = []
                ordered_translations = []

                # Collect all editions and translations
                editions = work_data.get("editions", {})
                translations = work_data.get("translations", {})

                # Group editions and translations by language pairs
                language_pairs = defaultdict(list)

                # First, add all editions to their respective language buckets
                for edition_id, edition in editions.items():
                    lang = edition.get("lang", "unknown")
                    language_pairs[lang].append(("edition", edition_id, edition))

                # Then, try to match translations to their original language editions
                for trans_id, translation in translations.items():
                    lang = translation.get("lang", "unknown")
                    # If we have an edition in a language this was translated from, link them
                    found_match = False
                    for edition_lang in language_pairs:
                        if edition_lang != lang:
                            language_pairs[edition_lang].append(("translation", trans_id, translation))
                            found_match = True
                            break

                    # If no match found, create a new entry
                    if not found_match:
                        language_pairs[lang].append(("translation", trans_id, translation))

                # Sort by language
                sorted_languages = sorted(language_pairs.keys())

                # Recreate editions and translations as ordered dicts
                ordered_editions_dict = OrderedDict()
                ordered_translations_dict = OrderedDict()

                # Process each language group
                for lang in sorted_languages:
                    # Sort items within a language group (editions first, then translations)
                    items = sorted(language_pairs[lang], key=lambda x: (0 if x[0] == "edition" else 1, x[1]))

                    # Add to appropriate dictionary
                    for item_type, item_id, item_data in items:
                        if item_type == "edition":
                            ordered_editions_dict[item_id] = item_data
                        else:
                            ordered_translations_dict[item_id] = item_data

                # Update the work data with ordered editions and translations
                work_data["editions"] = ordered_editions_dict
                work_data["translations"] = ordered_translations_dict

    # Update statistics
    catalog["statistics"]["authorCount"] = len(catalog["authors"])
    catalog["statistics"]["textCount"] = sum(
        len(author_data.get("works", {})) for author_data in catalog["authors"].values()
    )
    catalog["statistics"]["files"] = total_xml_files

    logger.info(f"Scan completed. Processed {processed_cts_files} CTS files.")
    logger.info(f"Found {catalog['statistics']['authorCount']} authors.")
    logger.info(f"Found {catalog['statistics']['textCount']} works.")
    logger.info(f"Found {total_xml_files} XML content files.")

    return catalog


def process_author_cts(cts_path: str, catalog: Dict[str, Any], author_id: str, author_info: Dict[str, Any]):
    """
    Process an author-level __cts__.xml file and add author information to the catalog.

    Args:
        cts_path: Path to the author-level __cts__.xml file
        catalog: The catalog to update
        author_id: The author ID (e.g., tlg0004)
        author_info: Author metadata from author_index.json
    """
    try:
        tree = ET.parse(cts_path)
        root = tree.getroot()

        # Check if this is a textgroup element
        if root.tag.endswith("textgroup"):
            # Get the author URN
            author_urn = root.get("urn")

            # Get the author name from XML or fallback to author_info
            groupname = root.find(".//ti:groupname", NAMESPACE)
            author_name = groupname.text if groupname is not None else author_info.get("name", author_id)

            # Create an entry for this author, combining XML data with author_info
            catalog["authors"][author_id] = {
                "name": author_name,
                "urn": author_urn,
                "century": author_info.get("century", 0),
                "type": author_info.get("type", "Unknown"),
                "works": {},
            }

            logger.debug(f"Added author: {author_id} - {author_name}")

    except ET.ParseError as e:
        logger.error(f"XML parsing error in {cts_path}: {e}")
    except Exception as e:
        logger.error(f"Error processing {cts_path}: {e}")


def process_work_cts(
    cts_path: str, xml_files: List[str], work_dir: str, catalog: Dict[str, Any], author_id: str, work_id: str
):
    """
    Process a work-level __cts__.xml file and add work information to the catalog.

    Args:
        cts_path: Path to the work-level __cts__.xml file
        xml_files: List of XML files in the same directory
        work_dir: Directory containing the work files
        catalog: The catalog to update
        author_id: The author ID (e.g., tlg0004)
        work_id: The work ID (e.g., tlg001)
    """
    try:
        tree = ET.parse(cts_path)
        root = tree.getroot()

        # Check if this is a work element
        if root.tag.endswith("work"):
            work_urn = root.get("urn")
            group_urn = root.get("groupUrn")

            # Get the work title
            title_elem = root.find(".//ti:title", NAMESPACE)
            work_title = title_elem.text if title_elem is not None else work_id

            # Get work language
            work_lang = root.get("{http://www.w3.org/XML/1998/namespace}lang", "")

            # Create an entry for this work if author exists
            if author_id in catalog["authors"]:
                # Initialize work with an empty editions and translations dictionary
                catalog["authors"][author_id]["works"][work_id] = {
                    "title": work_title,
                    "urn": work_urn,
                    "language": work_lang,
                    "editions": {},
                    "translations": {},
                }

                logger.debug(f"Added work: {author_id}/{work_id} - {work_title}")

                # Process editions
                for edition in root.findall(".//ti:edition", NAMESPACE):
                    process_text_version(edition, "edition", xml_files, work_dir, catalog, author_id, work_id)

                # Process translations
                for translation in root.findall(".//ti:translation", NAMESPACE):
                    process_text_version(translation, "translation", xml_files, work_dir, catalog, author_id, work_id)

    except ET.ParseError as e:
        logger.error(f"XML parsing error in {cts_path}: {e}")
    except Exception as e:
        logger.error(f"Error processing {cts_path}: {e}")


def process_text_version(
    element: ET.Element,
    version_type: str,
    xml_files: List[str],
    work_dir: str,
    catalog: Dict[str, Any],
    author_id: str,
    work_id: str,
):
    """
    Process a single edition or translation element and add it to the catalog.

    Args:
        element: The edition or translation XML element
        version_type: Either "edition" or "translation"
        xml_files: List of XML files in the work directory
        work_dir: Directory containing the work files
        catalog: The catalog to update
        author_id: The author ID (e.g., tlg0004)
        work_id: The work ID (e.g., tlg001)
    """
    # Get URN and other attributes
    urn = element.get("urn")
    if not urn:
        return

    # Get language
    lang = element.get("{http://www.w3.org/XML/1998/namespace}lang", "")

    # Get label
    label_elem = element.find(".//ti:label", NAMESPACE)
    label = label_elem.text if label_elem is not None else ""

    # Get description
    desc_elem = element.find(".//ti:description", NAMESPACE)
    description = desc_elem.text if desc_elem is not None else ""

    # Find matching XML file
    matching_file = find_matching_xml_file(urn, xml_files)

    if matching_file:
        # Get full path to the XML file
        file_path = os.path.join(work_dir, matching_file)

        # Extract editor information from the XML file
        editor_info = extract_editor_info(file_path)

        # Get relative path
        rel_path = os.path.relpath(file_path, args.data_dir)

        # Create the version information dictionary
        version_info = {
            "urn": urn,
            "label": label,
            "description": description,
            "lang": lang,
            "language": get_language_display_name(lang),
            "editor": editor_info.get("editor"),
            "translator": editor_info.get("translator"),
            "path": rel_path,
            "filename": matching_file,
        }

        # Add to catalog
        if author_id in catalog["authors"] and work_id in catalog["authors"][author_id]["works"]:
            # Determine if this is an edition or translation
            target_dict = catalog["authors"][author_id]["works"][work_id][
                "editions" if version_type == "edition" else "translations"
            ]

            # Use the last part of the URN as the version ID
            version_id = urn.split(":")[-1].split(".")[-1]  # e.g., perseus-grc2
            target_dict[version_id] = version_info

            # Update statistics
            if version_type == "edition":
                catalog["statistics"]["editions"] += 1
                # Update word count statistics by language
                if lang == "grc":
                    catalog["statistics"]["greekWords"] += 1
                elif lang == "lat":
                    catalog["statistics"]["latinWords"] += 1
                elif lang == "ara":
                    catalog["statistics"]["arabicwords"] += 1
            else:
                catalog["statistics"]["translations"] += 1

            logger.debug(f"Added {version_type}: {urn} -> {rel_path}")

    else:
        logger.warning(f"No matching XML file found for URN: {urn}")


def find_matching_xml_file(urn: str, xml_files: List[str]) -> Optional[str]:
    """
    Find an XML file that matches the URN.

    Args:
        urn: The URN to match
        xml_files: List of XML files to search

    Returns:
        The name of the matching XML file, or None if not found
    """
    urn_id = urn.split(":")[-1]  # Get the last part of the URN

    for file in xml_files:
        if urn_id in file:
            return file

    return None


def simplified_catalog(catalog: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a simplified version of the catalog with only statistics.

    Args:
        catalog: The full catalog

    Returns:
        Simplified catalog with only statistics
    """
    return {
        "statistics": catalog["statistics"],
        "authorCount": catalog["statistics"]["authorCount"],
        "textCount": catalog["statistics"]["textCount"],
        "editionCount": catalog["statistics"]["editions"],
        "translationCount": catalog["statistics"]["translations"],
    }


def main():
    """Main function to orchestrate the catalog generation."""
    global args
    args = parse_arguments()

    # Configure logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load author metadata
    author_metadata = load_author_index(args.author_index)

    # Scan the data directory and build the integrated catalog
    catalog = scan_data_directory(args.data_dir, author_metadata)

    # Determine output based on flags
    output_catalog = simplified_catalog(catalog) if args.stats_only else catalog

    # Write the catalog to the output file
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_catalog, f, indent=2, ensure_ascii=False)

    logger.info(f"Generated integrated catalog saved to {args.output}")
    logger.info(
        f"Statistics: {catalog['statistics']['authorCount']} authors, "
        f"{catalog['statistics']['textCount']} works, "
        f"{catalog['statistics']['editions']} editions, "
        f"{catalog['statistics']['translations']} translations"
    )


if __name__ == "__main__":
    main()
