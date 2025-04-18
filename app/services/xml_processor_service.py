"""Service for processing XML files with reference handling capabilities."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from loguru import logger

from app.services.catalog_service import CatalogService

# Define Element type for type annotations
Element = TypeVar("Element", bound=ET.Element)


class XMLProcessorService:
    """Service for processing XML files with reference handling."""

    def __init__(self, data_path: str = "data", catalog_service: CatalogService = None):
        """Initialize the XML processor service.

        Args:
            data_path: Path to the data directory
            catalog_service: Catalog service for path resolution
        """
        self.data_path = Path(data_path)
        self.catalog_service = catalog_service

    def load_xml_from_path(self, path: str) -> Element:
        """Load XML file from path.

        Args:
            path: Path to the XML file relative to data directory

        Returns:
            Root XML element

        Raises:
            FileNotFoundError: If the XML file is not found
        """
        filepath = self.data_path / path
        if not filepath.exists():
            raise FileNotFoundError(f"XML file not found: {filepath}")
        return ET.parse(str(filepath)).getroot()

    def extract_references(self, xml_root: Element) -> Dict[str, Element]:
        """Extract all references from XML.

        Args:
            xml_root: Root XML element

        Returns:
            Dictionary mapping reference strings to elements
        """
        references = {}
        self._extract_references_recursive(xml_root, "", references)
        return references

    def _extract_references_recursive(self, element: Element, parent_ref: str, references: Dict[str, Element]) -> None:
        """Recursively extract references from XML.

        Args:
            element: Current XML element
            parent_ref: Parent reference string
            references: Dictionary to store references
        """
        n_value = element.get("n")
        if n_value:
            ref = f"{parent_ref}.{n_value}" if parent_ref else n_value
            references[ref] = element
        else:
            ref = parent_ref

        for child in element:
            self._extract_references_recursive(child, ref, references)

    def get_passage_by_reference(self, xml_root: Element, reference: str) -> Optional[Element]:
        """Get a passage by its reference.

        Args:
            xml_root: Root XML element
            reference: Reference string

        Returns:
            Element for the reference or None if not found
        """
        if not reference:
            return None

        # Split reference into parts
        ref_parts = reference.split(".")

        # Start from root
        current = xml_root

        # Follow reference path
        for part in ref_parts:
            found = False
            for child in current:
                if child.get("n") == part:
                    current = child
                    found = True
                    break
            if not found:
                return None

        return current

    def get_adjacent_references(self, xml_root: Element, reference: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Get adjacent references for navigation.

        Args:
            xml_root: Root XML element
            reference: Current reference

        Returns:
            Dictionary with prev and next references
        """
        if not reference:
            return {"prev": None, "next": None}

        # Get all references
        references = self.extract_references(xml_root)
        sorted_refs = sorted(references.keys())

        try:
            current_idx = sorted_refs.index(reference)
            prev_ref = sorted_refs[current_idx - 1] if current_idx > 0 else None
            next_ref = sorted_refs[current_idx + 1] if current_idx < len(sorted_refs) - 1 else None
        except ValueError:
            prev_ref = None
            next_ref = None

        return {"prev": prev_ref, "next": next_ref}

    def tokenize_text(self, element: Element) -> List[Dict[str, Any]]:
        """Process XML element into tokens for word-level analysis.

        Args:
            element: XML element to tokenize

        Returns:
            List of token dictionaries with type, text, and index
        """
        tokens = []
        word_index = 0

        text = "".join(element.itertext())
        words = re.findall(r"\w+|\s+|[^\w\s]", text)

        for word in words:
            if word.strip():
                tokens.append({"type": "word", "text": word, "index": word_index})
                word_index += 1

        return tokens

    def transform_to_html(self, xml_root: Element, target_ref: Optional[str] = None) -> str:
        """Transform XML to HTML with reference attributes.

        Args:
            xml_root: Root XML element
            target_ref: Optional specific reference to display

        Returns:
            HTML string with reference attributes
        """
        html = []

        if target_ref:
            element = self.get_passage_by_reference(xml_root, target_ref)
            if element is None:
                return f"<p>Reference '{target_ref}' not found.</p>"
            elements = [element]
        else:
            elements = [xml_root]

        for element in elements:
            html.append(self._process_element_to_html(element))

        return "".join(html)

    def _process_element_to_html(self, element: Element, parent_ref: str = "") -> str:
        """Process an XML element to HTML with reference attributes.

        Args:
            element: XML element to process
            parent_ref: Parent reference string

        Returns:
            HTML string representation of the element
        """
        n_value = element.get("n")

        if n_value:
            ref = f"{parent_ref}.{n_value}" if parent_ref else n_value
            html = f'<div class="ref" data-ref="{ref}" id="ref-{ref}">'
            html += f'<span class="ref-num">{n_value}</span>'
        else:
            ref = parent_ref
            html = "<div>"

        # Process text content
        if element.text and element.text.strip():
            html += f'<span class="text">{element.text}</span>'

        # Process children
        for child in element:
            html += self._process_element_to_html(child, ref)

            # Handle tail text after child
            if child.tail and child.tail.strip():
                html += f'<span class="text">{child.tail}</span>'

        html += "</div>"
        return html

    def extract_text_content(self, file_path: Path) -> str:
        """Extract the text content from an XML file.

        Args:
            file_path: Path to the XML file

        Returns:
            The text content as HTML

        Raises:
            FileNotFoundError: If the file does not exist
            Exception: If there is an error parsing the XML
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extract text content
            content = ""

            # Try to find TEI text elements
            text_parts = root.findall(".//{http://www.tei-c.org/ns/1.0}text") or root.findall(".//text")

            for text_part in text_parts:
                # Convert element to string
                element_string = ET.tostring(text_part, encoding="unicode")

                # Simple cleaning of XML tags
                content += self._clean_xml_tags(element_string)

            # If no content found, try different approach
            if not content:
                # Try getting all paragraphs
                paragraphs = root.findall(".//{http://www.tei-c.org/ns/1.0}p") or root.findall(".//p")

                for p in paragraphs:
                    # Convert element to string
                    element_string = ET.tostring(p, encoding="unicode")

                    # Simple cleaning of XML tags
                    content += f"<p>{self._clean_xml_tags(element_string)}</p>"

            return content or f"<p><em>No text content found in {file_path.name}</em></p>"

        except Exception as e:
            return f"<p><em>Error parsing XML: {str(e)}</em></p>"

    def _clean_xml_tags(self, xml_string: str) -> str:
        """Clean XML tags from a string, leaving basic formatting.

        Args:
            xml_string: The XML string to clean

        Returns:
            The cleaned string with basic HTML formatting
        """
        # Replace common TEI elements with HTML equivalents
        xml_string = re.sub(r"<(tei:)?div[^>]*>", "<div>", xml_string)
        xml_string = re.sub(r"</(tei:)?div>", "</div>", xml_string)

        xml_string = re.sub(r"<(tei:)?p[^>]*>", "<p>", xml_string)
        xml_string = re.sub(r"</(tei:)?p>", "</p>", xml_string)

        xml_string = re.sub(r"<(tei:)?head[^>]*>", "<h3>", xml_string)
        xml_string = re.sub(r"</(tei:)?head>", "</h3>", xml_string)

        xml_string = re.sub(r"<(tei:)?l[^>]*>", '<span class="line">', xml_string)
        xml_string = re.sub(r"</(tei:)?l>", "</span><br>", xml_string)

        # Remove remaining XML tags
        xml_string = re.sub(r"<[^>]*>", "", xml_string)

        # Clean up whitespace
        xml_string = re.sub(r"\s+", " ", xml_string).strip()

        return xml_string
