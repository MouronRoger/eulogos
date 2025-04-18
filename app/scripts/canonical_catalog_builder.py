#!/usr/bin/env python3
"""Canonical catalog builder for Eulogos.

This script is the definitive and authoritative catalog generator for the Eulogos project.
It scans the data directory for __cts__.xml files, extracts author/work/edition/translation metadata,
merges with author_index.json, and outputs a hierarchical integrated_catalog.json.
It ensures all fields are present, paths are correct, and missing authors are added with blank metadata.
Output is sorted alphabetically at each level.

Usage:
  python app/scripts/canonical_catalog_builder.py --data-dir=data --output=integrated_catalog.json \
  --author-index=author_index.json
"""

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional

NAMESPACE = {"ti": "http://chs.harvard.edu/xmlns/cts"}

LANGUAGE_DISPLAY_NAMES = {
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


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate integrated_catalog.json for Eulogos.")
    parser.add_argument("--data-dir", default="data", help="Path to data directory")
    parser.add_argument("--output", default="integrated_catalog.json", help="Output file path")
    parser.add_argument("--author-index", default="author_index.json", help="Path to author_index.json")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    return parser.parse_args()


def load_author_index(author_path: str) -> Dict[str, Dict[str, Any]]:
    """Load author metadata from author_index.json."""
    try:
        with open(author_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"Loaded author_index.json with {len(data)} authors")
            if "authors" in data and isinstance(data["authors"], dict):
                return data["authors"]
            return data
    except Exception as e:
        print(f"Error loading author_index.json: {e}")
        return {}


def extract_author_info(cts_path: str) -> Dict[str, Any]:
    """Extract author URN and name from author-level __cts__.xml."""
    try:
        tree = ET.parse(cts_path)
        root = tree.getroot()
        urn = root.get("urn")
        groupname = root.find(".//ti:groupname", NAMESPACE)
        name = groupname.text.strip() if groupname is not None else None
        return {"urn": urn, "name": name}
    except Exception as e:
        print(f"Error parsing author CTS {cts_path}: {e}")
        return {"urn": None, "name": None}


def extract_work_info(cts_path: str) -> Dict[str, Any]:
    """Extract work URN, title, and language from work-level __cts__.xml."""
    try:
        tree = ET.parse(cts_path)
        root = tree.getroot()
        urn = root.get("urn")
        title_elem = root.find(".//ti:title", NAMESPACE)
        title = title_elem.text.strip() if title_elem is not None else None
        lang = root.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        return {"urn": urn, "title": title, "language": lang}
    except Exception as e:
        print(f"Error parsing work CTS {cts_path}: {e}")
        return {"urn": None, "title": None, "language": ""}


def extract_editions_and_translations(
    root: ET.Element, xml_files: List[str], work_dir: str, data_dir: str, verbose: bool = False
) -> tuple[OrderedDict, OrderedDict]:
    """Extract editions and translations from a work-level __cts__.xml."""
    editions = OrderedDict()
    translations = OrderedDict()

    if verbose:
        print(f"Extracting from work dir: {work_dir}")
        print(f"Available XML files: {xml_files}")

    for elem in root.findall(".//ti:edition", NAMESPACE):
        info = extract_version_info(elem, xml_files, work_dir, data_dir, verbose)
        if info:
            version_id = info.pop("id", elem.get("urn", "").split(":")[-1].split(".")[-1])
            editions[version_id] = info
    for elem in root.findall(".//ti:translation", NAMESPACE):
        info = extract_version_info(elem, xml_files, work_dir, data_dir, verbose)
        if info:
            version_id = info.pop("id", elem.get("urn", "").split(":")[-1].split(".")[-1])
            translations[version_id] = info

    if verbose:
        print(f"Found {len(editions)} editions and {len(translations)} translations")

    return editions, translations


def extract_version_info(
    elem: ET.Element, xml_files: List[str], work_dir: str, data_dir: str, verbose: bool = False
) -> Optional[Dict[str, Any]]:
    """Extract info for an edition or translation."""
    urn = elem.get("urn")
    if not urn:
        return None

    lang = elem.get("{http://www.w3.org/XML/1998/namespace}lang", "")
    label_elem = elem.find(".//ti:label", NAMESPACE)
    label = label_elem.text.strip() if label_elem is not None else urn.split(":")[-1]
    desc_elem = elem.find(".//ti:description", NAMESPACE)
    description = desc_elem.text.strip() if desc_elem is not None else ""
    version_id = urn.split(":")[-1].split(".")[-1]

    if verbose:
        print(f"Processing {urn} with version_id {version_id}")

    matching_file = next((f for f in xml_files if version_id in f), None)
    if not matching_file:
        if verbose:
            print(f"No matching file found for {version_id} in {work_dir}")
        return None

    if verbose:
        print(f"Found matching file: {matching_file}")

    rel_path = os.path.relpath(os.path.join(work_dir, matching_file), data_dir).replace("\\", "/")

    # Try to extract editor/translator info
    editor = None
    translator = None
    try:
        file_path = os.path.join(work_dir, matching_file)
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            header = f.read(10000)  # Read first 10KB which should include the header

        # Look for editor info
        editor_match = re.search(r"<editor[^>]*>([^<]+)</editor>", header)
        if editor_match:
            editor = editor_match.group(1).strip()

        # Look for translator info
        translator_match = re.search(r'<editor role="translator"[^>]*>([^<]+)</editor>', header)
        if translator_match:
            translator = translator_match.group(1).strip()
    except Exception as e:
        if verbose:
            print(f"Error extracting editor info: {e}")

    return {
        "id": version_id,
        "urn": urn,
        "label": label,
        "description": description,
        "lang": lang,
        "language": LANGUAGE_DISPLAY_NAMES.get(lang, lang),
        "editor": editor,
        "translator": translator,
        "path": rel_path,
        "filename": matching_file,
    }


def build_catalog(data_dir: str, author_index: Dict[str, Dict[str, Any]], verbose: bool = False) -> Dict[str, Any]:
    """Build the hierarchical catalog from XML and author_index.json."""
    catalog = OrderedDict()
    author_count = 0
    work_count = 0
    edition_count = 0
    translation_count = 0

    # Count how many files we're dealing with
    xml_file_count = sum(1 for _ in Path(data_dir).glob("**/*.xml") if _.name != "__cts__.xml")
    cts_file_count = sum(1 for _ in Path(data_dir).glob("**/__cts__.xml"))

    print(f"Found {xml_file_count} XML content files and {cts_file_count} __cts__.xml files")

    # First process all author directories with __cts__.xml
    for author_dir in Path(data_dir).iterdir():
        if not author_dir.is_dir():
            continue

        author_id = author_dir.name
        author_cts = author_dir / "__cts__.xml"

        if not author_cts.exists():
            print(f"Skipping {author_id}: No author-level __cts__.xml")
            continue

        author_info = extract_author_info(str(author_cts))
        meta = author_index.get(author_id, {})

        catalog[author_id] = {
            "name": author_info["name"] or meta.get("name", author_id),
            "urn": author_info["urn"],
            "century": meta.get("century", 0),
            "type": meta.get("type", ""),
            "works": OrderedDict(),
        }

        author_count += 1
        print(f"Processed author #{author_count}: {author_id}")

    # Now process all work directories with __cts__.xml and XML content files
    for author_dir in Path(data_dir).iterdir():
        if not author_dir.is_dir():
            continue

        author_id = author_dir.name

        # Skip if author not in catalog
        if author_id not in catalog:
            continue

        for work_dir in author_dir.iterdir():
            if not work_dir.is_dir():
                continue

            work_id = work_dir.name
            work_cts = work_dir / "__cts__.xml"

            if not work_cts.exists():
                if verbose:
                    print(f"Skipping {author_id}/{work_id}: No work-level __cts__.xml")
                continue

            xml_files = [f.name for f in work_dir.glob("*.xml") if f.name != "__cts__.xml"]

            if not xml_files:
                if verbose:
                    print(f"Skipping {author_id}/{work_id}: No XML content files")
                continue

            work_info = extract_work_info(str(work_cts))

            try:
                tree = ET.parse(str(work_cts))
                root = tree.getroot()
                editions, translations = extract_editions_and_translations(
                    root, xml_files, str(work_dir), data_dir, verbose
                )
            except Exception as e:
                print(f"Error processing {work_cts}: {e}")
                editions, translations = OrderedDict(), OrderedDict()

            edition_count += len(editions)
            translation_count += len(translations)

            catalog[author_id]["works"][work_id] = {
                "title": work_info["title"] or work_id,
                "urn": work_info["urn"],
                "language": work_info["language"],
                "editions": editions,
                "translations": translations,
            }

            work_count += 1

            if work_count % 100 == 0:
                print(f"Processed {work_count} works...")

    # Add any authors in author_index.json not found in XML
    for author_id, meta in author_index.items():
        if author_id not in catalog:
            catalog[author_id] = {
                "name": meta.get("name", author_id),
                "urn": None,
                "century": meta.get("century", 0),
                "type": meta.get("type", ""),
                "works": OrderedDict(),
            }
            author_count += 1
            print(f"Added author from index: {author_id}")

    # Sort authors and works alphabetically
    sorted_catalog = OrderedDict(
        sorted(
            (
                (
                    aid,
                    {
                        **adata,
                        "works": OrderedDict(sorted(adata["works"].items(), key=lambda x: x[1]["title"] or x[0])),
                    },
                )
                for aid, adata in catalog.items()
            ),
            key=lambda x: x[1]["name"] or x[0],
        )
    )

    print(
        f"Catalog summary: {author_count} authors, {work_count} works, "
        f"{edition_count} editions, {translation_count} translations"
    )

    return sorted_catalog


def main() -> int:
    """Execute the catalog building process and save the results."""
    args = parse_arguments()
    author_index = load_author_index(args.author_index)
    catalog = build_catalog(args.data_dir, author_index, args.verbose)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"Catalog written to {args.output}")
    return 0


if __name__ == "__main__":
    main()
