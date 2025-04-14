"""Text processing utilities for catalog generation."""

import os
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, List

from app.scripts.catalog_generator.xml_parser import (
    NAMESPACE, 
    extract_editor_info, 
    get_language_display_name,
    find_matching_xml_file,
    count_words_in_text
)

# Configure logging
logger = logging.getLogger(__name__)


def process_work_cts(
    cts_path: str, 
    xml_files: List[str], 
    work_dir: str, 
    catalog: Dict[str, Any], 
    author_id: str, 
    work_id: str,
    data_dir: str,
    include_content_sample: bool = False
) -> None:
    """Process a work-level __cts__.xml file and add work information to the catalog.
    
    Args:
        cts_path: Path to the work-level __cts__.xml file
        xml_files: List of XML files in the same directory
        work_dir: Directory containing the work files
        catalog: The catalog to update
        author_id: The author ID (e.g., tlg0004)
        work_id: The work ID (e.g., tlg001)
        data_dir: Base data directory for relative path calculation
        include_content_sample: Whether to include content samples
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
                    "archived": False,  # Default to not archived
                    "editions": {},
                    "translations": {}
                }
                
                logger.debug(f"Added work: {author_id}/{work_id} - {work_title}")
                
                # Process editions
                for edition in root.findall(".//ti:edition", NAMESPACE):
                    process_text_version(
                        edition, 
                        "edition", 
                        xml_files, 
                        work_dir, 
                        catalog, 
                        author_id, 
                        work_id, 
                        data_dir,
                        include_content_sample
                    )
                
                # Process translations
                for translation in root.findall(".//ti:translation", NAMESPACE):
                    process_text_version(
                        translation, 
                        "translation", 
                        xml_files, 
                        work_dir, 
                        catalog, 
                        author_id, 
                        work_id,
                        data_dir,
                        include_content_sample
                    )
    
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
    data_dir: str,
    include_content_sample: bool = False
) -> None:
    """Process a single edition or translation element and add it to the catalog.
    
    Args:
        element: The edition or translation XML element
        version_type: Either "edition" or "translation"
        xml_files: List of XML files in the work directory
        work_dir: Directory containing the work files
        catalog: The catalog to update
        author_id: The author ID (e.g., tlg0004)
        work_id: The work ID (e.g., tlg001)
        data_dir: Base data directory for relative path calculation
        include_content_sample: Whether to include content samples
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
        rel_path = os.path.relpath(file_path, data_dir)
        
        # Count words if this is an edition
        word_count = 0
        if version_type == "edition":
            word_count = count_words_in_text(file_path, lang)
        
        # Extract content sample if requested
        content_sample = None
        if include_content_sample:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    # Read first 2000 chars
                    sample = f.read(2000)
                    # Simple extraction of first paragraph text
                    content_sample = sample[:sample.find('</p>')] if '</p>' in sample else sample[:200]
                    # Strip tags
                    content_sample = content_sample.replace('<p>', '').replace('</p>', '')
            except Exception as e:
                logger.warning(f"Error extracting content sample from {file_path}: {e}")
        
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
            "word_count": word_count
        }
        
        # Add content sample if available
        if content_sample:
            version_info["content_sample"] = content_sample
        
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
                    catalog["statistics"]["greekWords"] += word_count
                elif lang == "lat":
                    catalog["statistics"]["latinWords"] += word_count
                elif lang == "ara":
                    catalog["statistics"]["arabicwords"] += word_count
            else:
                catalog["statistics"]["translations"] += 1
            
            logger.debug(f"Added {version_type}: {urn} -> {rel_path}")
        
    else:
        logger.warning(f"No matching XML file found for URN: {urn}") 