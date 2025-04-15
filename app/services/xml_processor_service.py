"""Service for processing XML files with reference handling capabilities."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.models.urn import URN


class XMLProcessorService:
    """Service for processing XML files with reference handling."""

    def __init__(self, data_path: str = "data"):
        """Initialize the XML processor service.

        Args:
            data_path: Path to the data directory containing XML files
        """
        self.data_path = Path(data_path)
        self.namespaces = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace"}

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

    def get_file_path(self, urn: str) -> Path:
        """Get the file path for a URN.

        Args:
            urn: The URN to get the file path for

        Returns:
            A Path object for the file

        Raises:
            ValueError: If the URN cannot be parsed
        """
        parsed = self.parse_urn(urn)

        if not parsed["textgroup"] or not parsed["work"] or not parsed["version"]:
            raise ValueError(f"Invalid URN format: {urn}")

        # Construct file path based on the actual file structure
        # The file path should be: data/tlg0532/tlg001/tlg0532.tlg001.perseus-grc2.xml
        return (
            self.data_path
            / parsed["textgroup"]
            / parsed["work"]
            / f"{parsed['textgroup']}.{parsed['work']}.{parsed['version']}.xml"
        )

    def resolve_urn_to_file_path(self, urn_obj: URN) -> Path:
        """Resolve URN to file path.

        Args:
            urn_obj: URN object

        Returns:
            Path object for the XML file
        """
        return urn_obj.get_file_path(self.data_path)

    def load_xml(self, urn_obj: URN) -> ET._Element:
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

    def extract_references(self, element: ET._Element, parent_ref: str = "") -> Dict[str, ET._Element]:
        """Extract hierarchical references from TEI XML elements.

        Args:
            element: XML element to extract from
            parent_ref: Parent reference string

        Returns:
            Dictionary of reference strings to XML elements
        """
        references = {}
        n_attr = element.get("n")

        if n_attr:
            ref = f"{parent_ref}.{n_attr}" if parent_ref else n_attr
            references[ref] = element
        else:
            ref = parent_ref

        # Process child textparts and lines recursively
        for child in element.findall(
            ".//{http://www.tei-c.org/ns/1.0}div[@type='textpart']", self.namespaces
        ) or element.findall(".//{http://www.tei-c.org/ns/1.0}l", self.namespaces):
            child_refs = self.extract_references(child, ref)
            references.update(child_refs)

        return references

    def get_passage_by_reference(self, xml_root: ET._Element, reference: str) -> Optional[ET._Element]:
        """Retrieve a specific passage by its reference.

        Args:
            xml_root: Root XML element
            reference: Reference string (e.g., "1.1.5")

        Returns:
            XML element matching the reference or None if not found
        """
        references = self.extract_references(xml_root)
        return references.get(reference)

    def get_adjacent_references(self, xml_root: ET._Element, current_ref: Optional[str]) -> Dict[str, Optional[str]]:
        """Get previous and next references relative to current reference.

        Args:
            xml_root: Root XML element
            current_ref: Current reference string

        Returns:
            Dictionary with 'prev' and 'next' references
        """
        references = list(self.extract_references(xml_root).keys())
        if not references:
            return {"prev": None, "next": None}

        # Sort references naturally (1.1, 1.2, 1.10 instead of 1.1, 1.10, 1.2)
        references.sort(key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])

        if current_ref is None:
            return {"prev": None, "next": references[0] if references else None}

        try:
            idx = references.index(current_ref)
            prev_ref = references[idx - 1] if idx > 0 else None
            next_ref = references[idx + 1] if idx < len(references) - 1 else None
            return {"prev": prev_ref, "next": next_ref}
        except ValueError:
            return {"prev": None, "next": references[0] if references else None}

    def tokenize_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into tokens (words and punctuation).

        Args:
            text: Text to tokenize

        Returns:
            List of token dictionaries with type, text, and index
        """
        if not text or text.strip() == "":
            return []

        tokens = []
        word_index = 1
        words = text.split()

        for word in words:
            # Extract punctuation from the end of words
            match = re.match(r"(\w+)([,.;:!?]*)", word)
            if match:
                word_text, punct = match.groups()
                tokens.append({"type": "word", "text": word_text, "index": word_index})
                word_index += 1

                if punct:
                    tokens.append({"type": "punct", "text": punct})
            else:
                tokens.append({"type": "word", "text": word, "index": word_index})
                word_index += 1

        return tokens

    def transform_to_html(self, xml_root: ET._Element, target_ref: Optional[str] = None) -> str:
        """Transform XML to HTML with reference attributes.

        Args:
            xml_root: Root XML element
            target_ref: Optional specific reference to display

        Returns:
            HTML string with reference attributes

        Raises:
            ValueError: If target_ref is provided but not found
        """
        # If a specific reference is targeted, find that element
        if target_ref:
            element = self.get_passage_by_reference(xml_root, target_ref)
            if not element:
                raise ValueError(f"Reference not found: {target_ref}")
            # Include only the specified element and its children
            elements = [element]
        else:
            # Include all top-level textparts
            elements = xml_root.findall(
                ".//tei:div[@type='textpart' and not(parent::tei:div[@type='textpart'])]", self.namespaces
            ) or xml_root.findall(".//tei:l[not(parent::tei:div[@type='textpart'])]", self.namespaces)

            # If no textparts found, try finding any text divisions
            if not elements:
                elements = xml_root.findall(".//tei:div[@type='text']", self.namespaces) or xml_root.findall(
                    ".//tei:text", self.namespaces
                )

        html = []

        for element in elements:
            html.append(self._process_element_to_html(element))

        return "".join(html)

    def _process_element_to_html(self, element: ET._Element, parent_ref: str = "") -> str:
        """Process an XML element to HTML with reference attributes.

        Args:
            element: XML element to process
            parent_ref: Parent reference string

        Returns:
            HTML string for the element
        """
        html = []
        element_type = element.tag.split("}")[-1]  # Remove namespace
        n_attr = element.get("n")

        # Build reference for this element
        ref = f"{parent_ref}.{n_attr}" if parent_ref and n_attr else (n_attr or parent_ref)

        # Create HTML with data attributes
        html.append(f'<div class="text-part {element_type}" data-reference="{ref}">')

        # Add section number as clickable element
        if n_attr:
            html.append(f'<div class="section-num"><a href="#ref={ref}">{n_attr}</a></div>')

        # Add content
        html.append('<div class="content">')

        # Process text content
        for text_node in element.itertext():
            if text_node.strip():
                tokens = self.tokenize_text(text_node)
                for token in tokens:
                    if token["type"] == "word":
                        token_text = token["text"]
                        token_index = token["index"]
                        html.append(
                            '<span class="token" '
                            f'data-token="{token_text}" '
                            f'data-token-index="{token_index}">'
                            f"{token_text}</span>"
                        )
                    else:
                        html.append(f'<span class="punct">{token["text"]}</span>')
                html.append(" ")

        # Process nested elements
        div_elements = element.findall("./tei:div[@type='textpart']", self.namespaces)
        l_elements = element.findall("./tei:l", self.namespaces)

        for child in div_elements or l_elements:
            child_html = self._process_element_to_html(child, ref)
            html.append(child_html)

        # Close elements
        html.append("</div></div>")

        return "".join(html)

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
