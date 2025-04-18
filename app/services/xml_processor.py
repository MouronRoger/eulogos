"""Service for processing and formatting XML files."""
import os
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom


class XMLProcessorService:
    """Service class for handling XML file operations."""

    def __init__(self, data_dir: str = "data") -> None:
        """Initialize the XML processor service.
        
        Args:
            data_dir: Directory containing XML files, defaults to 'data'
        """
        self.data_dir = data_dir

    def load_xml_from_path(self, file_path: str) -> ET.Element:
        """Load and parse XML from a file path.
        
        Args:
            file_path: Path to XML file relative to data directory
            
        Returns:
            Parsed XML element tree root
            
        Raises:
            FileNotFoundError: If XML file does not exist
            ET.ParseError: If XML is malformed
        """
        full_path = os.path.join(self.data_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"XML file not found: {full_path}")
            
        tree = ET.parse(full_path)
        return tree.getroot()

    def format_xml_for_display(self, root: ET.Element) -> str:
        """Format XML content for pretty display.
        
        Args:
            root: XML element tree root
            
        Returns:
            Formatted XML string with proper indentation
        """
        rough_string = ET.tostring(root, encoding="unicode")
        parsed = minidom.parseString(rough_string)
        return parsed.toprettyxml(indent="  ")

    def get_references(self, root: ET.Element) -> List[Dict[str, str]]:
        """Extract reference information from XML content.
        
        Args:
            root: XML element tree root
            
        Returns:
            List of reference dictionaries containing path and description
        """
        refs = []
        for ref in root.findall(".//reference"):
            path = ref.get("path", "")
            desc = ref.get("description", "")
            if path:
                refs.append({"path": path, "description": desc})
        return refs 