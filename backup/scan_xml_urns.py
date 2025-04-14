#!/usr/bin/env python3
"""
Script to scan XML files in the data directory and generate a hierarchical catalog index.

This script walks through the data directory, identifies all __cts__.xml files,
extracts information about authors and their works, and creates a JSON catalog
mapping URNs to their corresponding XML files while preserving the author-work hierarchy.
"""

import os
import json
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# XML namespace for CTS files
NAMESPACE = {"ti": "http://chs.harvard.edu/xmlns/cts"}


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate a hierarchical catalog index of XML files in the data directory.'
    )
    parser.add_argument(
        '--data-dir', default='data', help='Path to the data directory (default: data)'
    )
    parser.add_argument(
        '--output',
        default='generated_catalog_index.json',
        help='Output file path (default: generated_catalog_index.json)',
    )
    parser.add_argument(
        '--compare',
        default='catalog_index.json',
        help='Path to existing catalog for comparison (default: catalog_index.json)',
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', help='Enable verbose output'
    )
    parser.add_argument(
        '--flat', action='store_true', 
        help='Generate a flat catalog instead of hierarchical structure'
    )
    parser.add_argument(
        '--format', choices=['hierarchical', 'flat', 'entries'], default='hierarchical',
        help=('Output format: hierarchical (default, nested structure), '
              'flat (dictionary of URNs), or entries (flat list of author-work-edition entries)')
    )
    return parser.parse_args()


def scan_data_directory(data_dir):
    """
    Scan the data directory for __cts__.xml files and build a hierarchical catalog.
    
    Args:
        data_dir (str): Path to the data directory
        
    Returns:
        dict: A dictionary with hierarchical structure of authors, works, and editions
    """
    catalog = {
        "authors": {},
        "urns": {}
    }
    
    total_xml_files = 0
    processed_cts_files = 0
    
    logger.info(f"Scanning data directory: {data_dir}")
    
    # First pass: Identify and process author (textgroup) level __cts__.xml files
    for author_dir in os.listdir(data_dir):
        author_path = os.path.join(data_dir, author_dir)
        
        # Skip if not a directory
        if not os.path.isdir(author_path):
            continue
            
        # Process author-level __cts__.xml
        author_cts_path = os.path.join(author_path, "__cts__.xml")
        if os.path.exists(author_cts_path):
            try:
                logger.info(f"Processing author: {author_cts_path}")
                process_author_cts(author_cts_path, catalog)
                processed_cts_files += 1
            except Exception as e:
                logger.error(f"Error processing author {author_cts_path}: {e}")
    
    # Second pass: Process work-level __cts__.xml files
    for author_dir in os.listdir(data_dir):
        author_path = os.path.join(data_dir, author_dir)
        
        # Skip if not a directory
        if not os.path.isdir(author_path):
            continue
            
        for work_dir in os.listdir(author_path):
            work_path = os.path.join(author_path, work_dir)
            
            # Skip if not a directory or if it's __cts__.xml
            if not os.path.isdir(work_path) or work_dir == "__cts__.xml":
                continue
                
            # Process work-level __cts__.xml
            work_cts_path = os.path.join(work_path, "__cts__.xml")
            if os.path.exists(work_cts_path):
                try:
                    logger.info(f"Processing work: {work_cts_path}")
                    xml_files = [f for f in os.listdir(work_path) if f.endswith('.xml') and f != '__cts__.xml']
                    total_xml_files += len(xml_files)
                    process_work_cts(work_cts_path, xml_files, catalog)
                    processed_cts_files += 1
                except Exception as e:
                    logger.error(f"Error processing work {work_cts_path}: {e}")
    
    logger.info(f"Scan completed. Processed {processed_cts_files} CTS files.")
    logger.info(f"Found {len(catalog['authors'])} authors.")
    logger.info(f"Found {len(catalog['urns'])} URNs mapped to XML files.")
    logger.info(f"Total XML content files found: {total_xml_files}.")
    
    return catalog


def process_author_cts(cts_path, catalog):
    """
    Process an author-level __cts__.xml file and add author information to the catalog.
    
    Args:
        cts_path (str): Path to the author-level __cts__.xml file
        catalog (dict): The catalog to update
    """
    try:
        tree = ET.parse(cts_path)
        root = tree.getroot()
        
        if root.tag == f"{{{NAMESPACE['ti']}}}textgroup":
            author_id = root.get("urn")
            
            # Extract the author ID (e.g., tlg0004)
            short_id = os.path.basename(os.path.dirname(cts_path))
            
            # Get the author name
            groupname = root.find(".//ti:groupname", NAMESPACE)
            author_name = groupname.text if groupname is not None else short_id
            
            # Create an entry for this author
            catalog["authors"][short_id] = {
                "name": author_name,
                "urn": author_id,
                "works": {}
            }
            
            logger.debug(f"Added author: {short_id} - {author_name}")
    
    except ET.ParseError as e:
        logger.error(f"XML parsing error in {cts_path}: {e}")
    except Exception as e:
        logger.error(f"Error processing {cts_path}: {e}")


def process_work_cts(cts_path, xml_files, catalog):
    """
    Process a work-level __cts__.xml file and add work information to the catalog.
    
    Args:
        cts_path (str): Path to the work-level __cts__.xml file
        xml_files (list): List of XML files in the same directory
        catalog (dict): The catalog to update
    """
    try:
        tree = ET.parse(cts_path)
        root = tree.getroot()
        
        if root.tag == f"{{{NAMESPACE['ti']}}}work":
            work_urn = root.get("urn")
            group_urn = root.get("groupUrn")
            
            # Extract the author ID and work ID
            path_parts = cts_path.split(os.path.sep)
            author_id = path_parts[-3]  # e.g., tlg0004
            work_id = path_parts[-2]    # e.g., tlg001
            
            # Get the work title
            title_elem = root.find(".//ti:title", NAMESPACE)
            work_title = title_elem.text if title_elem is not None else work_id
            
            # Create an entry for this work if author exists
            if author_id in catalog["authors"]:
                catalog["authors"][author_id]["works"][work_id] = {
                    "title": work_title,
                    "urn": work_urn,
                    "editions": {},
                    "translations": {}
                }
                
                logger.debug(f"Added work: {author_id}/{work_id} - {work_title}")
                
                # Process editions and translations
                process_text_versions(root, xml_files, cts_path, catalog, author_id, work_id)
    
    except ET.ParseError as e:
        logger.error(f"XML parsing error in {cts_path}: {e}")
    except Exception as e:
        logger.error(f"Error processing {cts_path}: {e}")


def process_text_versions(root, xml_files, cts_path, catalog, author_id, work_id):
    """
    Process editions and translations from a work-level __cts__.xml file.
    
    Args:
        root (Element): The root element of the work __cts__.xml
        xml_files (list): List of XML files in the work directory
        cts_path (str): Path to the work __cts__.xml file
        catalog (dict): The catalog to update
        author_id (str): The author ID (e.g., tlg0004)
        work_id (str): The work ID (e.g., tlg001)
    """
    directory = os.path.dirname(cts_path)
    
    # Process editions
    for edition in root.findall(".//ti:edition", NAMESPACE):
        urn = edition.get("urn")
        if urn:
            process_text_version(edition, urn, "edition", xml_files, directory, catalog, author_id, work_id)
    
    # Process translations
    for translation in root.findall(".//ti:translation", NAMESPACE):
        urn = translation.get("urn")
        if urn:
            process_text_version(translation, urn, "translation", xml_files, directory, catalog, author_id, work_id)


def process_text_version(element, urn, version_type, xml_files, directory, catalog, author_id, work_id):
    """
    Process a single edition or translation element and add it to the catalog.
    
    Args:
        element (Element): The edition or translation XML element
        urn (str): The URN of the text version
        version_type (str): Either "edition" or "translation"
        xml_files (list): List of XML files in the work directory
        directory (str): Path to the work directory
        catalog (dict): The catalog to update
        author_id (str): The author ID (e.g., tlg0004)
        work_id (str): The work ID (e.g., tlg001)
    """
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
        rel_path = os.path.join(os.path.relpath(directory, args.data_dir), matching_file)
        version_info = {
            "urn": urn,
            "label": label,
            "description": description,
            "lang": lang,
            "path": rel_path,
            "filename": matching_file  # Add the filename for easier access
        }
        
        # Add to both hierarchical structure and flat URN lookup
        if author_id in catalog["authors"] and work_id in catalog["authors"][author_id]["works"]:
            target_dict = catalog["authors"][author_id]["works"][work_id]["editions" if version_type == "edition" else "translations"]
            # Use the last part of the URN as the version ID
            version_id = urn.split(":")[-1].split(".")[-1]  # e.g., perseus-grc2
            target_dict[version_id] = version_info
        
        # Add to flat URN lookup for easier access
        catalog["urns"][urn] = {
            "path": rel_path,
            "type": version_type,
            "lang": lang,
            "label": label,
            "description": description,
            "author_id": author_id,
            "work_id": work_id,
            "filename": matching_file  # Add the filename for easier access
        }
        
        logger.debug(f"Added {version_type}: {urn} -> {rel_path}")
    else:
        logger.warning(f"No matching XML file found for URN: {urn}")


def find_matching_xml_file(urn, xml_files):
    """
    Find an XML file that matches the URN.
    
    Args:
        urn (str): The URN to match
        xml_files (list): List of XML files to search
        
    Returns:
        str: The name of the matching XML file, or None if not found
    """
    urn_id = urn.split(":")[-1]  # Get the last part of the URN
    
    for file in xml_files:
        if urn_id in file:
            return file
    
    return None


def generate_flattened_catalog(catalog):
    """
    Generate a flattened catalog in the format requested by the user.
    
    Args:
        catalog (dict): The hierarchical catalog
        
    Returns:
        list: A list of flattened entries, each containing author, work, and edition information
    """
    flattened_entries = []
    
    # Iterate through each author
    for author_ref, author_data in catalog["authors"].items():
        author_name = author_data["name"]
        
        # Iterate through each work of this author
        for work_ref, work_data in author_data["works"].items():
            work_title = work_data["title"]
            
            # Process editions
            for edition_id, edition_data in work_data["editions"].items():
                entry = {
                    "author_ref": author_ref,
                    "author_name": author_name,
                    "work_ref": work_ref,
                    "work_title": work_title,
                    "urn_lang": edition_data["filename"],
                    "edition_title": edition_data["label"]
                }
                flattened_entries.append(entry)
                
            # Process translations
            for translation_id, translation_data in work_data["translations"].items():
                entry = {
                    "author_ref": author_ref,
                    "author_name": author_name,
                    "work_ref": work_ref,
                    "work_title": work_title,
                    "urn_lang": translation_data["filename"],
                    "edition_title": translation_data["label"]
                }
                flattened_entries.append(entry)
    
    return flattened_entries


def compare_catalogs(existing_catalog_path, generated_catalog, verbose=False):
    """
    Compare the existing catalog with the generated one.
    
    Args:
        existing_catalog_path (str): Path to the existing catalog file
        generated_catalog (dict): The generated catalog
        verbose (bool): Whether to show detailed output
    """
    if not os.path.exists(existing_catalog_path):
        logger.warning(f"Existing catalog {existing_catalog_path} not found. Cannot compare.")
        return
    
    try:
        with open(existing_catalog_path, 'r', encoding='utf-8') as f:
            existing_catalog = json.load(f)
        
        # Extract URNs from both catalogs for comparison
        generated_urns = set(generated_catalog["urns"].keys())
        
        # Determine if existing catalog is flat or hierarchical
        if "urns" in existing_catalog:
            existing_urns = set(existing_catalog["urns"].keys())
        else:
            # Assume flat structure
            existing_urns = set(existing_catalog.keys())
        
        # Check for URNs in generated catalog that are missing from existing catalog
        missing_urns = generated_urns - existing_urns
        
        # Check for URNs in existing catalog that don't exist in the data directory
        extra_urns = existing_urns - generated_urns
        
        # Report findings
        if missing_urns:
            logger.warning(f"Found {len(missing_urns)} URNs in data directory that are not in {existing_catalog_path}")
            if verbose or len(missing_urns) <= 5:
                for urn in list(missing_urns)[:10 if verbose else 5]:
                    logger.warning(f"  Missing URN: {urn}")
                if len(missing_urns) > (10 if verbose else 5):
                    logger.warning(f"  ... and {len(missing_urns) - (10 if verbose else 5)} more")
        
        if extra_urns:
            logger.warning(f"Found {len(extra_urns)} URNs in {existing_catalog_path} that don't exist in data directory")
            if verbose or len(extra_urns) <= 5:
                for urn in list(extra_urns)[:10 if verbose else 5]:
                    logger.warning(f"  Extra URN: {urn}")
                if len(extra_urns) > (10 if verbose else 5):
                    logger.warning(f"  ... and {len(extra_urns) - (10 if verbose else 5)} more")
        
        if not missing_urns and not extra_urns:
            logger.info(f"The existing catalog {existing_catalog_path} matches the data directory contents.")
        
    except json.JSONDecodeError:
        logger.error(f"Error decoding {existing_catalog_path}. It may not be a valid JSON file.")
    except Exception as e:
        logger.error(f"Error comparing catalogs: {e}")


def main():
    """Main function to orchestrate the catalog generation and comparison."""
    global args
    args = parse_arguments()
    
    # Configure logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Scan the data directory and build the catalog
    catalog = scan_data_directory(args.data_dir)
    
    # Determine the output format
    if args.format == 'flat' or args.flat:
        output_catalog = catalog["urns"]
        logger.info("Generating flat URN catalog")
    elif args.format == 'entries':
        output_catalog = generate_flattened_catalog(catalog)
        logger.info("Generating flattened entries catalog")
    else:
        output_catalog = catalog
        logger.info("Generating hierarchical catalog")
    
    # Write the catalog to the output file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_catalog, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Generated catalog index saved to {args.output}")
    
    # Compare with existing catalog if provided
    compare_catalogs(args.compare, catalog, args.verbose)


if __name__ == "__main__":
    main() 