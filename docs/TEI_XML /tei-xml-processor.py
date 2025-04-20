"""Service for processing TEI XML files with reference handling capabilities.

Key architectural principles:
1. text_id is ALWAYS the full data path including filename
2. The catalog is the ONLY source of truth for file paths
3. All XML loading happens through the catalog service
4. Direct path construction is not allowed
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException
from loguru import logger

from app.config import get_settings
from app.services.catalog_service import CatalogService

# Define TEI namespace
TEI_NS = "http://www.tei-c.org/ns/1.0"
NS_MAP = {"tei": TEI_NS}

class XMLProcessorService:
    """Service for processing TEI XML files with reference handling."""

    def __init__(self, catalog_service: CatalogService, data_path: str = "data"):
        """Initialize the XML processor service.

        Args:
            catalog_service: Catalog service for path resolution. Required
                as the catalog is the single source of truth for path resolution.
            data_path: Path to the data directory

        Raises:
            ValueError: If no catalog service is provided
        """
        if not catalog_service:
            raise ValueError(
                "XMLProcessorService requires a catalog_service. "
                "The catalog is the single source of truth for path resolution."
            )
            
        self.catalog_service = catalog_service
        self.data_path = Path(data_path)
        self.settings = get_settings()
        
        # Register TEI namespace
        ET.register_namespace('tei', TEI_NS)
        
        logger.debug(f"Initialized XMLProcessorService with data_path={self.data_path}")

    def load_xml_from_path(self, path: str) -> Optional[ET.Element]:
        """Load XML file from path.

        Args:
            path: Path to the XML file relative to data directory
                 This is the text_id in the catalog

        Returns:
            Root XML element or None if there was an error

        Raises:
            FileNotFoundError: If the XML file is not found
        """
        filepath = self.data_path / path
        logger.debug(f"Attempting to load XML from filepath: {filepath}")
        
        if not filepath.exists():
            logger.error(f"XML file not found: {filepath}")
            raise FileNotFoundError(f"XML file not found: {filepath}")
        
        try:
            # Parse the XML file
            tree = ET.parse(str(filepath))
            root = tree.getroot()
            
            logger.debug(f"Successfully parsed XML file: {filepath}")    
            return root
            
        except ET.ParseError as e:
            logger.exception(f"XML parse error for file {filepath}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error loading XML from {filepath}: {e}")
            raise

    def load_document(self, text_id: str) -> Optional[ET.Element]:
        """Load document by text ID.
        
        Args:
            text_id: The text ID to load, which is the full data path
                    including the filename as stored in the catalog
            
        Returns:
            Document object or None if there was an error
            
        Raises:
            FileNotFoundError: If text not found
        """
        # Get text from catalog
        logger.debug(f"Loading document for text_id: {text_id}")
        text = self.catalog_service.get_text_by_id(text_id)
        if not text:
            logger.error(f"Text not found for ID: {text_id}")
            raise FileNotFoundError(f"Text not found for ID: {text_id}")
        
        logger.debug(f"Found text with path: {text.path}")
        
        # The text ID is the path - validate they match
        if text_id != text.path:
            logger.warning(f"Text ID {text_id} does not match path {text.path} - using path from catalog")
            
        # Validate path
        if not text.path:
            logger.error(f"Text has no path: {text_id}")
            raise FileNotFoundError(f"Text has no path: {text_id}")
            
        # Load XML from path
        return self.load_xml_from_path(text.path)

    def extract_references(self, xml_root: Optional[ET.Element]) -> Dict[str, ET.Element]:
        """Extract all references from XML.

        Args:
            xml_root: Root XML element

        Returns:
            Dictionary mapping reference strings to elements
        """
        if xml_root is None:
            logger.error("Cannot extract references from None XML root")
            return {}
            
        try:
            references = {}
            logger.debug(f"Starting extraction of references from XML root with tag: {xml_root.tag}")
            self._extract_references_recursive(xml_root, "", references)
            logger.debug(f"Extracted {len(references)} references from XML")
            return references
        except Exception as e:
            logger.exception(f"Error extracting references: {e}")
            return {}

    def _extract_references_recursive(self, element: Optional[ET.Element], parent_ref: str, references: Dict[str, ET.Element]) -> None:
        """Recursively extract references from XML.

        Args:
            element: Current XML element
            parent_ref: Parent reference string
            references: Dictionary to store references
        """
        if element is None:
            return
            
        try:
            # First check for n attribute (common in TEI XML)
            n_value = element.get("n")
            
            # If no n attribute, check for xml:id 
            if not n_value:
                n_value = element.get("{http://www.w3.org/XML/1998/namespace}id")
            
            if n_value:
                ref = f"{parent_ref}.{n_value}" if parent_ref else n_value
                references[ref] = element
            else:
                ref = parent_ref

            # Process children recursively
            for child in element:
                self._extract_references_recursive(child, ref, references)
                
        except Exception as e:
            logger.error(f"Error in extract_references_recursive: {e}, parent_ref={parent_ref}")

    def get_passage_by_reference(self, xml_root: Optional[ET.Element], reference: Optional[str]) -> Optional[ET.Element]:
        """Get a passage by its reference.

        Args:
            xml_root: Root XML element
            reference: Reference string

        Returns:
            Element for the reference or None if not found
        """
        if not reference:
            logger.debug("No reference provided to get_passage_by_reference")
            return None
            
        if xml_root is None:
            logger.error(f"Cannot get passage from None XML root for reference: {reference}")
            return None

        # Extract all references
        references = self.extract_references(xml_root)
        
        # Find the requested reference
        if reference in references:
            return references[reference]
            
        # If not found directly, try a more flexible match
        logger.warning(f"Reference '{reference}' not found exactly, trying flexible match")
        
        # Split reference into parts
        ref_parts = reference.split(".")
        
        # Start from root
        current = xml_root

        # Follow reference path
        for part in ref_parts:
            found = False
            for child in current:
                n_value = child.get("n") or child.get("{http://www.w3.org/XML/1998/namespace}id")
                if n_value == part:
                    current = child
                    found = True
                    break
            if not found:
                logger.warning(f"Reference part '{part}' not found in path {reference}")
                return None

        logger.debug(f"Found passage for reference {reference}")
        return current

    def get_adjacent_references(self, xml_root: Optional[ET.Element], reference: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Get adjacent references for navigation.

        Args:
            xml_root: Root XML element
            reference: Current reference

        Returns:
            Dictionary with prev and next references
        """
        if not reference:
            return {"prev": None, "next": None}
            
        if xml_root is None:
            logger.error(f"Cannot get adjacent references from None XML root for reference: {reference}")
            return {"prev": None, "next": None}

        # Get all references
        references = self.extract_references(xml_root)
        if not references:
            logger.warning(f"No references found in document for reference: {reference}")
            return {"prev": None, "next": None}
            
        # Sort references for consistent navigation
        # Natural sort: numbers are sorted numerically, strings alphabetically
        sorted_refs = sorted(references.keys(), 
                            key=lambda x: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', x)])

        try:
            current_idx = sorted_refs.index(reference)
            prev_ref = sorted_refs[current_idx - 1] if current_idx > 0 else None
            next_ref = sorted_refs[current_idx + 1] if current_idx < len(sorted_refs) - 1 else None
            logger.debug(f"Adjacent references for {reference}: prev={prev_ref}, next={next_ref}")
        except ValueError:
            logger.warning(f"Reference {reference} not found in sorted references")
            prev_ref = None
            next_ref = None

        return {"prev": prev_ref, "next": next_ref}

    def transform_to_html(self, text_id: str, target_ref: Optional[str] = None) -> str:
        """Transform XML to HTML with reference attributes.

        Args:
            text_id: ID of the text to transform (full data path including filename)
            target_ref: Optional specific reference to display

        Returns:
            HTML string with reference attributes
            
        Raises:
            FileNotFoundError: If text not found
        """
        # Load document
        xml_root = self.load_document(text_id)
        
        # Check if document is None
        if xml_root is None:
            logger.error(f"Failed to load document for text_id: {text_id}")
            return "<div class='error'>Error: Failed to load document</div>"
            
        return self._transform_element_to_html(xml_root, target_ref)
    
    def _transform_element_to_html(self, xml_root: Optional[ET.Element], target_ref: Optional[str] = None) -> str:
        """Transform XML element to HTML with reference attributes.
        
        Args:
            xml_root: Root XML element
            target_ref: Optional specific reference to display
            
        Returns:
            HTML string with reference attributes
        """
        if xml_root is None:
            logger.error("Cannot transform None element to HTML")
            return "<div class='error'>Error: XML document could not be processed</div>"
            
        try:
            html = []

            if target_ref:
                element = self.get_passage_by_reference(xml_root, target_ref)
                if element is None:
                    logger.warning(f"Reference '{target_ref}' not found in document")
                    return f"<div class='error'>Reference '{target_ref}' not found in document.</div>"
                elements = [element]
            else:
                elements = [xml_root]

            logger.debug(f"Processing {len(elements)} elements for HTML transformation")
            
            for element in elements:
                if element is None:
                    logger.error("Cannot process None element to HTML")
                    html.append("<div class='error'>Error: Element is None</div>")
                    continue
                    
                processed_html = self._process_element_to_html(element)
                if not processed_html:
                    logger.error(f"Empty HTML returned for element {element.tag}")
                    processed_html = "<div class='error'>Error: Element processing returned empty content</div>"
                        
                html.append(processed_html)

            # Join the HTML parts
            result = "".join(html)
            
            # Final validation before returning
            if not result:
                logger.error("Empty string generated after joining HTML parts")
                return "<div class='error'>Error: Empty content generated</div>"
                
            return result
            
        except Exception as e:
            logger.exception(f"Unexpected error in _transform_element_to_html: {e}")
            return f"<div class='error'>Error transforming XML: {str(e)}</div>"

    def _process_element_to_html(self, element: Optional[ET.Element], parent_ref: str = "") -> str:
        """Process an XML element to HTML with reference attributes.

        Args:
            element: XML element to process
            parent_ref: Parent reference string

        Returns:
            HTML string representation of the element
        """
        if element is None:
            return "<div class='error'>Error: NULL element</div>"
            
        try:
            # Handle TEI namespace
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
            
            # Get reference attributes
            n_value = element.get("n")
            xml_id = element.get("{http://www.w3.org/XML/1998/namespace}id")
            
            # Determine CSS class based on tag
            css_class = f"tei-{tag}" if tag else "tei-element"
            
            # Handle different element types
            if n_value or xml_id:
                ref_value = n_value or xml_id
                ref = f"{parent_ref}.{ref_value}" if parent_ref else ref_value
                
                # Create div with reference data attributes
                html = f'<div class="{css_class}" data-reference="{ref}" id="ref-{ref}">'
                
                # Add reference number display
                html += f'<div class="section-num"><a href="#ref-{ref}">{ref_value}</a></div>'
                
                # Add content container
                html += '<div class="content">'
            else:
                ref = parent_ref
                html = f'<div class="{css_class}">'
            
            # Process text content
            if element.text and element.text.strip():
                text_content = element.text.strip()
                html += f'<span class="text">{text_content}</span>'

            # Process children
            for child in element:
                child_html = self._process_element_to_html(child, ref)
                html += child_html

                # Handle tail text after child
                if child.tail and child.tail.strip():
                    html += f'<span class="text">{child.tail}</span>'
            
            # Close any extra divs we opened
            if n_value or xml_id:
                html += '</div>'  # Close content div
            
            html += '</div>'  # Close main element div
            
            return html
            
        except Exception as e:
            logger.exception(f"Error in _process_element_to_html: {e}")
            return f"<div class='error'>Error processing element: {str(e)}</div>"

    def extract_metadata(self, document: Optional[ET.Element]) -> Dict[str, Any]:
        """Extract metadata from a TEI document.
        
        Args:
            document: XML document root element
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        if document is None:
            logger.error("Cannot extract metadata from None document")
            return metadata
            
        try:
            # Extract TEI header metadata
            header = document.find(f".//{{{TEI_NS}}}teiHeader")
            if header is not None:
                # Extract title
                title = header.find(f".//{{{TEI_NS}}}title")
                if title is not None and title.text:
                    metadata["title"] = title.text.strip()
                
                # Extract author
                author = header.find(f".//{{{TEI_NS}}}author")
                if author is not None and author.text:
                    metadata["author"] = author.text.strip()
                
                # Extract editor
                editor = header.find(f".//{{{TEI_NS}}}editor")
                if editor is not None and editor.text:
                    metadata["editor"] = editor.text.strip()
                
                # Extract language
                language = header.find(f".//{{{TEI_NS}}}language")
                if language is not None and language.text:
                    metadata["language"] = language.text.strip()
                
                # Extract date
                date = header.find(f".//{{{TEI_NS}}}date")
                if date is not None and date.text:
                    metadata["date"] = date.text.strip()
            
            logger.debug(f"Extracted metadata keys: {', '.join(metadata.keys())}")
            
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
            
        return metadata

    def get_document_statistics(self, document: Optional[ET.Element]) -> Dict[str, Any]:
        """Get statistics for a document.
        
        Args:
            document: XML document root element
            
        Returns:
            Dictionary of statistics
        """
        if document is None:
            return {"element_count": 0, "text_length": 0, "word_count": 0}
            
        try:
            text_content = "".join(document.itertext())
            
            # Calculate word count (split by whitespace and count)
            word_count = len(text_content.split())
            
            stats = {
                "element_count": self._count_elements(document),
                "text_length": len(text_content),
                "word_count": word_count,
                "reference_count": len(self.extract_references(document))
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating document statistics: {e}")
            return {"element_count": 0, "text_length": 0, "word_count": 0, "error": str(e)}
            
    def _count_elements(self, element: Optional[ET.Element]) -> int:
        """Count the number of elements in a document.
        
        Args:
            element: XML element
            
        Returns:
            Number of elements
        """
        if element is None:
            return 0
            
        try:
            count = 1  # Count the element itself
            for child in element:
                count += self._count_elements(child)
            return count
        except:
            return 0
