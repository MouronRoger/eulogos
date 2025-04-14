"""XML parser utilities for catalog generation."""

import re
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Any, List
import logging

# Configure logging
logger = logging.getLogger(__name__)

# XML namespaces
NAMESPACE = {"ti": "http://chs.harvard.edu/xmlns/cts"}
TEI_NAMESPACE = {"tei": "http://www.tei-c.org/ns/1.0"}


def extract_editor_info(xml_file_path: str) -> Dict[str, Optional[str]]:
    """Extract editor information from a TEI XML file.
    
    Args:
        xml_file_path: Path to the TEI XML file
        
    Returns:
        Dictionary containing editor and translator information
    """
    editor_info = {
        "editor": None,
        "translator": None
    }
    
    try:
        # Extract the first part of the file to speed up parsing (only need header)
        with open(xml_file_path, 'r', encoding='utf-8', errors='replace') as f:
            xml_content = f.read(10000)  # Read first 10KB which should include the header
        
        # Extract editor information using regex for speed
        # Look for standard editor tags
        editor_match = re.search(r'<editor[^>]*>([^<]+)</editor>', xml_content)
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
        "cop": "Coptic"
    }
    return language_map.get(lang_code, lang_code)


def count_words_in_text(xml_file_path: str, language: str) -> int:
    """Count actual words in a text file by language.
    
    Args:
        xml_file_path: Path to the XML file
        language: Language code (e.g., 'grc', 'lat')
        
    Returns:
        Word count
    """
    try:
        with open(xml_file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        # Extract text content from XML
        # This is a simplified approach - a real implementation would use proper XML parsing
        # and handle different document structures
        text_content = re.sub(r'<[^>]+>', ' ', content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Count words based on language-specific rules
        if language == "grc":  # Greek
            # Greek-specific word counting logic
            words = len(re.findall(r'[\p{Greek}]+', text_content, re.UNICODE))
        elif language == "lat":  # Latin
            # Latin-specific word counting
            words = len(re.findall(r'[\p{Latin}]+', text_content, re.UNICODE))
        else:
            # Default word counting
            words = len(text_content.split())
            
        return words
    except Exception as e:
        logger.warning(f"Error counting words in {xml_file_path}: {e}")
        return 0


def find_matching_xml_file(urn: str, xml_files: List[str]) -> Optional[str]:
    """Find an XML file that matches the URN.
    
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