"""Service for processing XML files with reference handling capabilities."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from loguru import logger

from app.models.urn import URN
from app.services.catalog_service import CatalogService

# Define Element type for type annotations
# This allows using Element type in annotations without needing the internal _Element
Element = TypeVar("Element", bound=ET.Element)


class XMLProcessorService:
    """Service for processing XML files with reference handling."""

    def __init__(self, data_path: str = "data", catalog_service: CatalogService = None):
        """Initialize the XML processor service.

        Args:
            data_path: Path to the data directory
            catalog_service: Catalog service for path resolution. This MUST be provided
                as the catalog is the single source of truth for path resolution.

        Raises:
            ValueError: If no catalog service is provided
        """
        self.data_path = Path(data_path)
        self.catalog_service = catalog_service

        if not catalog_service:
            raise ValueError(
                "XMLProcessorService requires a catalog_service. "
                "The catalog is the single source of truth for path resolution."
            )

        logger.debug("Initialized XMLProcessorService with catalog_service and data_path={}", data_path)

    def resolve_urn_to_file_path(self, urn_obj: URN) -> Path:
        """Resolve URN to file path using catalog as source of truth.

        Args:
            urn_obj: URN object

        Returns:
            Path object for the XML file

        Raises:
            FileNotFoundError: If the catalog doesn't contain the URN or path is invalid
        """
        # Get text by URN
        text = self.catalog_service.get_text_by_urn(urn_obj.value)
        if text and hasattr(text, "path") and text.path:
            # Return absolute path
            return Path(self.data_path) / text.path

        # Try getting path directly from catalog service
        path = self.catalog_service.get_path_by_urn(urn_obj.value)
        if path:
            return Path(self.data_path) / path

        raise FileNotFoundError(
            f"URN {urn_obj.value} not found in catalog. All paths must be resolved through the catalog."
        )

    def load_xml(self, urn_obj: URN) -> Element:
        """Load XML file based on URN.

        Args:
            urn_obj: URN object

        Returns:
            Root XML element

        Raises:
            FileNotFoundError: If the XML file is not found
        """
        filepath = self.resolve_urn_to_file_path(urn_obj)
        if not filepath.exists():
            raise FileNotFoundError(f"XML file not found: {filepath}")
        return ET.parse(str(filepath)).getroot()

    def extract_references(self, element: Element, parent_ref: str = "") -> Dict[str, Element]:
        """Extract hierarchical references from TEI XML elements.

        Args:
            element: XML element to extract from
            parent_ref: Parent reference string

        Returns:
            Dictionary mapping reference strings to XML elements
        """
        references = {}
        n_value = element.get("n")

        if n_value:
            ref = f"{parent_ref}.{n_value}" if parent_ref else n_value
            references[ref] = element
        else:
            ref = parent_ref

        for child in element:
            child_refs = self.extract_references(child, ref)
            references.update(child_refs)

        return references

    def get_passage_by_reference(self, xml_root: Element, reference: str) -> Optional[Element]:
        """Retrieve a specific passage by its reference.

        Args:
            xml_root: Root XML element
            reference: Reference string (e.g., "1.1.5")

        Returns:
            XML element matching the reference or None if not found
        """
        references = self.extract_references(xml_root)
        return references.get(reference)

    def get_adjacent_references(self, xml_root: Element, current_ref: Optional[str]) -> Dict[str, Optional[str]]:
        """Get previous and next references relative to current reference.

        Args:
            xml_root: Root XML element
            current_ref: Current reference string

        Returns:
            Dictionary with 'prev' and 'next' reference strings
        """
        references = self.extract_references(xml_root)
        ref_keys = sorted(references.keys())

        if not current_ref or current_ref not in ref_keys:
            return {"prev": None, "next": None}

        current_idx = ref_keys.index(current_ref)
        prev_ref = ref_keys[current_idx - 1] if current_idx > 0 else None
        next_ref = ref_keys[current_idx + 1] if current_idx < len(ref_keys) - 1 else None

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

    def parse_urn(self, urn: str) -> Dict[str, str]:
        """Parse a URN into its components.

        Args:
            urn: The URN to parse

        Returns:
            A dictionary with the URN components
        """
        result = {"namespace": None, "textgroup": None, "work": None, "version": None, "reference": None}

        try:
            # Basic URN parsing
            parts = urn.split(":")
            if len(parts) >= 4:
                result["namespace"] = parts[2]
                identifier = parts[3].split(":")[0]
                id_parts = identifier.split(".")

                if len(id_parts) >= 1:
                    result["textgroup"] = id_parts[0]
                if len(id_parts) >= 2:
                    result["work"] = id_parts[1]
                if len(id_parts) >= 3:
                    result["version"] = id_parts[2]

                # Check for reference
                if len(parts) >= 5:
                    result["reference"] = parts[4]
                elif ":" in parts[3] and len(parts[3].split(":")) >= 2:
                    result["reference"] = parts[3].split(":")[1]
        except Exception:
            pass

        return result

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
