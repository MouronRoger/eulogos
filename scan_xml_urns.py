#!/usr/bin/env python3
"""
Script to scan XML files in the data directory and generate a catalog index.

This script walks through the data directory, identifies all __cts__.xml files,
extracts URN information for editions and translations, and creates a JSON catalog
mapping URNs to their corresponding XML files.
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
        description='Generate a catalog index of XML files in the data directory.'
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
    return parser.parse_args()


def scan_data_directory(data_dir):
    """
    Scan the data directory for __cts__.xml files and extract URN information.
    
    Args:
        data_dir (str): Path to the data directory
        
    Returns:
        dict: A dictionary mapping URNs to file information
    """
    urn_catalog = {}
    total_xml_files = 0
    processed_cts_files = 0
    extracted_urns = 0
    
    logger.info(f"Scanning data directory: {data_dir}")
    
    # Walk through the data directory
    for root, dirs, files in os.walk(data_dir):
        xml_content_files = [f for f in files if f.endswith('.xml') and f != '__cts__.xml']
        total_xml_files += len(xml_content_files)
        
        if "__cts__.xml" in files:
            # Process the CTS file to extract URNs
            cts_path = os.path.join(root, "__cts__.xml")
            try:
                if len(xml_content_files) > 0:  # Only process if there are content XML files
                    logger.info(f"Processing {cts_path}")
                    new_urns = extract_urns_from_cts(cts_path, xml_content_files)
                    urn_catalog.update(new_urns)
                    processed_cts_files += 1
                    extracted_urns += len(new_urns)
            except Exception as e:
                logger.error(f"Error processing {cts_path}: {e}")
    
    logger.info(f"Scan completed. Processed {processed_cts_files} CTS files.")
    logger.info(f"Found {extracted_urns} URNs mapped to XML files.")
    logger.info(f"Total XML content files found: {total_xml_files}.")
    
    return urn_catalog


def extract_urns_from_cts(cts_path, xml_files_in_dir):
    """
    Extract URNs from a CTS XML file and map them to corresponding XML files.
    
    Args:
        cts_path (str): Path to the __cts__.xml file
        xml_files_in_dir (list): List of XML files in the same directory
        
    Returns:
        dict: A dictionary mapping URNs to file information
    """
    urns = {}
    directory = os.path.dirname(cts_path)
    
    try:
        tree = ET.parse(cts_path)
        root = tree.getroot()
        
        # Process editions
        for edition in root.findall(".//ti:edition", NAMESPACE):
            urn = edition.get("urn")
            if urn:
                process_urn_element(urns, edition, urn, "edition", directory, xml_files_in_dir)
        
        # Process translations
        for translation in root.findall(".//ti:translation", NAMESPACE):
            urn = translation.get("urn")
            if urn:
                process_urn_element(urns, translation, urn, "translation", directory, xml_files_in_dir)
    
    except ET.ParseError as e:
        logger.error(f"XML parsing error in {cts_path}: {e}")
    except Exception as e:
        logger.error(f"Error processing {cts_path}: {e}")
    
    return urns


def process_urn_element(urns, element, urn, urn_type, directory, xml_files):
    """
    Process a URN element and add it to the URN catalog.
    
    Args:
        urns (dict): Dictionary to add the URN information to
        element (Element): XML element containing URN information
        urn (str): The URN string
        urn_type (str): Type of URN (edition or translation)
        directory (str): Directory containing the XML files
        xml_files (list): List of XML files in the directory
    """
    lang = element.get("{http://www.w3.org/XML/1998/namespace}lang", "")
    
    # Get label if available
    label_elem = element.find(".//ti:label", NAMESPACE)
    label = label_elem.text if label_elem is not None else ""
    
    # Find matching XML file
    matching_file = find_matching_xml_file(urn, xml_files)
    
    if matching_file:
        rel_path = os.path.join(os.path.relpath(directory, args.data_dir), matching_file)
        urns[urn] = {
            "path": rel_path,
            "type": urn_type,
            "lang": lang,
            "label": label
        }
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
        
        # Check for URNs in generated catalog that are missing from existing catalog
        missing_urns = [urn for urn in generated_catalog if urn not in existing_catalog]
        
        # Check for URNs in existing catalog that don't exist in the data directory
        extra_urns = [urn for urn in existing_catalog if urn not in generated_catalog]
        
        # Report findings
        if missing_urns:
            logger.warning(f"Found {len(missing_urns)} URNs in data directory that are not in {existing_catalog_path}")
            if verbose or len(missing_urns) <= 5:
                for urn in missing_urns[:10 if verbose else 5]:
                    logger.warning(f"  Missing URN: {urn}")
                if len(missing_urns) > (10 if verbose else 5):
                    logger.warning(f"  ... and {len(missing_urns) - (10 if verbose else 5)} more")
        
        if extra_urns:
            logger.warning(f"Found {len(extra_urns)} URNs in {existing_catalog_path} that don't exist in data directory")
            if verbose or len(extra_urns) <= 5:
                for urn in extra_urns[:10 if verbose else 5]:
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
    urn_catalog = scan_data_directory(args.data_dir)
    
    # Write the catalog to the output file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(urn_catalog, f, indent=2)
    
    logger.info(f"Generated catalog index saved to {args.output}")
    
    # Compare with existing catalog if provided
    compare_catalogs(args.compare, urn_catalog, args.verbose)


if __name__ == "__main__":
    main() 