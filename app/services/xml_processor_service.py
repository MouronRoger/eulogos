"""Service for processing XML files."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict


class XMLProcessorService:
    """Service for processing XML files."""

    def __init__(self, data_path: str = "data"):
        """Initialize the XML processor service.

        Args:
            data_path: Path to the data directory containing XML files
        """
        self.data_path = Path(data_path)
        self.namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}

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
