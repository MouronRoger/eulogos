"""Author processing utilities for catalog generation."""

import json
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, Optional
from collections import OrderedDict
from pathlib import Path

from app.scripts.catalog_generator.xml_parser import NAMESPACE

# Configure logging
logger = logging.getLogger(__name__)


def load_author_index(author_path: str) -> Dict[str, Dict[str, Any]]:
    """Load author metadata from author_index.json.
    
    Args:
        author_path: Path to the author_index.json file
        
    Returns:
        Dictionary of author metadata indexed by author ID
    """
    try:
        with open(author_path, 'r', encoding='utf-8') as f:
            author_data = json.load(f)
            logger.info(f"Loaded author metadata for {len(author_data)} authors from {author_path}")
            return author_data
    except Exception as e:
        logger.error(f"Error loading author index from {author_path}: {e}")
        return {}


def process_author_cts(
    cts_path: str, 
    catalog: Dict[str, Any], 
    author_id: str, 
    author_info: Dict[str, Any]
) -> None:
    """Process an author-level __cts__.xml file and add author information to the catalog.
    
    Args:
        cts_path: Path to the author-level __cts__.xml file
        catalog: The catalog dictionary to update
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
                "archived": author_info.get("archived", False),  # Add archive status
                "works": {}
            }
            
            logger.debug(f"Added author: {author_id} - {author_name}")
    
    except ET.ParseError as e:
        logger.error(f"XML parsing error in {cts_path}: {e}")
    except Exception as e:
        logger.error(f"Error processing {cts_path}: {e}") 