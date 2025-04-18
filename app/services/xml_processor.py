"""Service for processing and formatting XML files."""
import os
import re
from typing import Any, Dict, List, Optional, TypeVar, Union, Tuple
import xml.etree.ElementTree as ET
from pathlib import Path

# Define Element type for type annotations
Element = TypeVar("Element", bound=ET.Element)


class XMLProcessorService:
    """Service class for handling XML file operations."""

    def __init__(self, data_path: str = "data") -> None:
        """Initialize the XML processor service.
        
        Args:
            data_path: Directory containing XML files, defaults to 'data'
        """
        self.data_path = data_path

    def load_xml_from_path(self, file_path: str) -> Element:
        """Load and parse XML from a file path.
        
        Args:
            file_path: Path to XML file relative to data directory
            
        Returns:
            Parsed XML element tree root
            
        Raises:
            FileNotFoundError: If XML file does not exist
            ET.ParseError: If XML is malformed
        """
        full_path = os.path.join(self.data_path, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"XML file not found: {full_path}")
            
        tree = ET.parse(full_path)
        return tree.getroot()

    def format_xml_for_display(self, root: Element) -> str:
        """Format XML content for display with sophisticated formatting.
        
        Args:
            root: XML element tree root
            
        Returns:
            Formatted HTML with academic markup preserved
        """
        return self.transform_to_html(root)

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
        subtype = element.get("subtype")
        rend = element.get("rend")
        type_attr = element.get("type")
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        
        # Initialize ref variable
        ref = parent_ref
        
        # Special handling for different element types
        if tag == "div" and n_value:
            ref = f"{parent_ref}.{n_value}" if parent_ref else n_value
            div_class = f"div {subtype}" if subtype else "div"
            html = f'<div class="{div_class}" data-reference="{ref}" id="ref-{ref}">'
            
            # Add section number for navigation
            html += f'<div class="section-num"><a href="#ref={ref}">{n_value}</a></div>'
            html += '<div class="content">'
        elif tag == "p":
            p_class = f"p {rend}" if rend else "p"
            html = f'<p class="{p_class}">'
        elif tag == "head":
            html = f'<h3 class="head {rend if rend else ""}">'
        elif tag == "l":
            html = f'<span class="line {rend if rend else ""}">'
        elif tag == "note":
            html = f'<div class="note">'
        elif tag == "quote":
            html = f'<blockquote class="quote {rend if rend else ""}">'
        elif tag == "foreign":
            lang = element.get("xml:lang", "")
            html = f'<em class="foreign" data-lang="{lang}">'
        elif tag == "bibl":
            html = f'<cite class="bibl">'
        elif tag == "ref":
            target = element.get("target", "")
            html = f'<a href="{target}" class="ref">'
        elif tag == "milestone":
            unit = element.get("unit", "")
            milestone_n = element.get("n", "")
            html = f'<span class="milestone {unit}" data-n="{milestone_n}"></span>'
        elif tag in ["TEI", "text", "body"]:
            html = f'<div class="{tag}">'
        else:
            html = f'<div class="{tag}">'

        # Process text content
        if element.text and element.text.strip():
            if tag in ["ref", "foreign", "bibl"]:
                html += element.text
            else:
                tokens = re.findall(r"(\w+|[^\w\s]|\s+)", element.text)
                for token in tokens:
                    if token.strip():
                        if re.match(r"^\w+$", token):
                            html += f'<span class="token" data-token="{token}">{token}</span>'
                        else:
                            html += f'<span class="punct">{token}</span>'
                    else:
                        html += token

        # Process children
        for child in element:
            html += self._process_element_to_html(child, ref)

            # Handle tail text after child
            if child.tail and child.tail.strip():
                tokens = re.findall(r"(\w+|[^\w\s]|\s+)", child.tail)
                for token in tokens:
                    if token.strip():
                        if re.match(r"^\w+$", token):
                            html += f'<span class="token" data-token="{token}">{token}</span>'
                        else:
                            html += f'<span class="punct">{token}</span>'
                    else:
                        html += token

        # Close tags
        if tag == "div" and n_value:
            html += '</div></div>'
        elif tag == "p":
            html += '</p>'
        elif tag == "head":
            html += '</h3>'
        elif tag == "l":
            html += '</span><br>'
        elif tag == "note":
            html += '</div>'
        elif tag == "quote":
            html += '</blockquote>'
        elif tag == "foreign":
            html += '</em>'
        elif tag == "bibl":
            html += '</cite>'
        elif tag == "ref":
            html += '</a>'
        else:
            html += '</div>'

        return html

    def extract_text_content(self, file_path: str) -> str:
        """Extract the text content from an XML file.

        Args:
            file_path: Path to the XML file

        Returns:
            The text content as HTML

        Raises:
            FileNotFoundError: If the file does not exist
            Exception: If there is an error parsing the XML
        """
        xml_root = self.load_xml_from_path(file_path)
        return self.transform_to_html(xml_root)

    def get_references(self, xml_root: Element) -> Dict[str, Dict[str, Optional[str]]]:
        """Get references with navigation options.

        Args:
            xml_root: XML root element

        Returns:
            Dictionary with references and navigation links
        """
        references = self.extract_references(xml_root)
        result = {}

        for ref, element in references.items():
            adjacent_refs = self.get_adjacent_references(xml_root, ref)
            result[ref] = {
                "prev": adjacent_refs["prev"],
                "next": adjacent_refs["next"],
                "element": element
            }

        return result 