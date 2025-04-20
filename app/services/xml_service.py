"""XML processing service for Eulogos application.

This service handles direct XML file loading and processing, using file paths
from the catalog as canonical identifiers.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from loguru import logger

# XML namespace mappings
NAMESPACES = {
    "tei": "http://www.tei-c.org/ns/1.0",
    "xml": "http://www.w3.org/XML/1998/namespace",
}

# Register namespaces for ElementTree
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


class XMLService:
    """Service for processing XML files."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the XML service.
        
        Args:
            data_dir: Path to the data directory containing XML files
        """
        self.data_dir = Path(data_dir)
        logger.info(f"Initialized XML service with data directory: {self.data_dir}")
    
    def load_xml(self, path: str) -> Optional[ET.Element]:
        """Load an XML file by path.
        
        Args:
            path: Relative path to the XML file from the data directory
            
        Returns:
            The root XML element if successful, None otherwise
            
        Raises:
            FileNotFoundError: If the XML file doesn't exist
        """
        file_path = self.data_dir / path
        logger.debug(f"Loading XML file: {file_path}")
        
        if not file_path.exists():
            logger.error(f"XML file not found: {file_path}")
            raise FileNotFoundError(f"XML file not found: {file_path}")
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            logger.debug(f"Loaded XML file with root tag: {root.tag}")
            return root
        except ET.ParseError as e:
            logger.error(f"Error parsing XML file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading XML file {file_path}: {e}")
            return None
    
    def extract_text_content(self, element: ET.Element) -> str:
        """Extract plain text content from an XML element.
        
        Args:
            element: The XML element to extract text from
            
        Returns:
            The extracted text content
        """
        if element is None:
            return ""
        
        try:
            return "".join(element.itertext())
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return ""
    
    def extract_references(self, element: ET.Element) -> Dict[str, ET.Element]:
        """Extract reference sections from an XML document.
        
        This method identifies sections with 'n' attributes to create
        a navigation structure.
        
        Args:
            element: The XML root element
            
        Returns:
            Dictionary mapping reference strings to XML elements
        """
        if element is None:
            return {}
        
        references = {}
        
        def extract_recursive(el: ET.Element, parent_ref: str = "") -> None:
            """Recursively extract references from element tree."""
            if el is None:
                return
            
            # Check for 'n' attribute
            n_value = el.get("n")
            if n_value:
                # Build reference
                ref = f"{parent_ref}.{n_value}" if parent_ref else n_value
                references[ref] = el
            else:
                ref = parent_ref
            
            # Process children
            for child in el:
                extract_recursive(child, ref)
        
        try:
            # Start extraction from root
            extract_recursive(element)
            logger.debug(f"Extracted {len(references)} references from XML")
            return references
        except Exception as e:
            logger.error(f"Error extracting references: {e}")
            return {}
    
    def get_passage_by_reference(self, element: ET.Element, reference: str) -> Optional[ET.Element]:
        """Get a specific passage by reference.
        
        Args:
            element: The XML root element
            reference: The reference string (e.g., "1.2.3")
            
        Returns:
            The XML element for the reference if found, None otherwise
        """
        if element is None or not reference:
            return None
        
        # Get all references
        references = self.extract_references(element)
        
        # Return the element for the reference
        return references.get(reference)
    
    def get_adjacent_references(self, element: ET.Element, reference: str) -> Dict[str, Optional[str]]:
        """Get adjacent references for navigation.
        
        Args:
            element: The XML root element
            reference: The current reference string
            
        Returns:
            Dictionary with 'prev' and 'next' references
        """
        if element is None or not reference:
            return {"prev": None, "next": None}
        
        # Get all references
        references = self.extract_references(element)
        
        # Sort references numerically
        def sort_key(ref: str) -> List[Union[int, str]]:
            """Create sort key to handle numeric parts properly."""
            parts = []
            for part in ref.split("."):
                try:
                    parts.append(int(part))
                except ValueError:
                    parts.append(part)
            return parts
        
        sorted_refs = sorted(references.keys(), key=sort_key)
        
        # Find current reference index
        try:
            current_idx = sorted_refs.index(reference)
        except ValueError:
            return {"prev": None, "next": None}
        
        # Get previous and next
        prev_ref = sorted_refs[current_idx - 1] if current_idx > 0 else None
        next_ref = sorted_refs[current_idx + 1] if current_idx < len(sorted_refs) - 1 else None
        
        return {"prev": prev_ref, "next": next_ref}
    
    def transform_to_html(self, element: ET.Element, reference: Optional[str] = None) -> str:
        """Transform XML to HTML for display.
        
        If a reference is provided, only that section will be transformed.
        
        Args:
            element: The XML element to transform
            reference: Optional reference to limit the transformation to
            
        Returns:
            HTML string
        """
        if element is None:
            return "<div class='error'>No content available</div>"
        
        # If a reference is provided, get just that section
        if reference:
            target_element = self.get_passage_by_reference(element, reference)
            if target_element is None:
                return f"<div class='error'>Reference '{reference}' not found</div>"
            element = target_element
        
        # Transform the element to HTML
        return self._process_element_to_html(element)
    
    def _process_element_to_html(self, element: ET.Element, parent_ref: str = "") -> str:
        """Process an XML element to HTML with reference attributes.
        
        Args:
            element: The XML element to process
            parent_ref: Parent reference string for nested references
            
        Returns:
            HTML string
        """
        if element is None:
            return ""
        
        try:
            # Get clean tag name without namespace
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
            
            # Get attributes
            attributes = element.attrib
            n_value = attributes.get("n")
            
            # Determine reference
            ref = f"{parent_ref}.{n_value}" if parent_ref and n_value else n_value or parent_ref
            
            # Start HTML output
            html = []
            
            # Process based on tag type
            if tag in ["div", "body", "text", "TEI"]:
                # Container elements
                container_class = f"tei-{tag}" if tag != "TEI" else "tei-document"
                if ref:
                    html.append(f'<div class="{container_class}" data-ref="{ref}">')
                    if n_value:
                        html.append(f'<div class="section-num">{n_value}</div>')
                else:
                    html.append(f'<div class="{container_class}">')
                
                # Handle text content
                if element.text and element.text.strip():
                    html.append(f'<span class="text">{element.text}</span>')
                
                # Process children
                for child in element:
                    child_html = self._process_element_to_html(child, ref)
                    html.append(child_html)
                    
                    # Handle tail text
                    if child.tail and child.tail.strip():
                        html.append(f'<span class="text">{child.tail}</span>')
                
                html.append('</div>')
            
            elif tag in ["p", "l"]:
                # Paragraph-like elements
                html.append(f'<p class="tei-{tag}">')
                
                if element.text and element.text.strip():
                    html.append(element.text)
                
                # Process children
                for child in element:
                    child_html = self._process_element_to_html(child, ref)
                    html.append(child_html)
                    
                    # Handle tail text
                    if child.tail and child.tail.strip():
                        html.append(child.tail)
                
                html.append('</p>')
            
            elif tag in ["head", "title"]:
                # Heading elements
                level = 3  # Default heading level
                html.append(f'<h{level} class="tei-{tag}">')
                
                if element.text and element.text.strip():
                    html.append(element.text)
                
                # Process children
                for child in element:
                    child_html = self._process_element_to_html(child, ref)
                    html.append(child_html)
                    
                    # Handle tail text
                    if child.tail and child.tail.strip():
                        html.append(child.tail)
                
                html.append(f'</h{level}>')
            
            else:
                # Generic inline elements
                html.append(f'<span class="tei-{tag}">')
                
                if element.text and element.text.strip():
                    html.append(element.text)
                
                # Process children
                for child in element:
                    child_html = self._process_element_to_html(child, ref)
                    html.append(child_html)
                    
                    # Handle tail text
                    if child.tail and child.tail.strip():
                        html.append(child.tail)
                
                html.append('</span>')
            
            return "".join(html)
            
        except Exception as e:
            logger.error(f"Error processing element to HTML: {e}")
            return f"<div class='error'>Error processing content: {str(e)}</div>"
    
    def get_metadata(self, element: ET.Element) -> Dict[str, str]:
        """Extract metadata from an XML document.
        
        Args:
            element: The XML root element
            
        Returns:
            Dictionary of metadata
        """
        if element is None:
            return {}
        
        metadata = {}
        
        try:
            # Try to extract title
            title_elem = element.find(".//tei:title", NAMESPACES)
            if title_elem is not None and title_elem.text:
                metadata["title"] = title_elem.text.strip()
            
            # Try to extract author
            author_elem = element.find(".//tei:author", NAMESPACES)
            if author_elem is not None and author_elem.text:
                metadata["author"] = author_elem.text.strip()
            
            # Try to extract language
            lang_attr = element.get("{http://www.w3.org/XML/1998/namespace}lang")
            if lang_attr:
                metadata["language"] = lang_attr
            
            # Try to extract date
            date_elem = element.find(".//tei:date", NAMESPACES)
            if date_elem is not None and date_elem.text:
                metadata["date"] = date_elem.text.strip()
            
            # Try to extract publisher
            publisher_elem = element.find(".//tei:publisher", NAMESPACES)
            if publisher_elem is not None and publisher_elem.text:
                metadata["publisher"] = publisher_elem.text.strip()
            
            # Try to extract source
            source_elem = element.find(".//tei:sourceDesc", NAMESPACES)
            if source_elem is not None:
                text = self.extract_text_content(source_elem)
                if text:
                    metadata["source"] = text.strip()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return metadata 