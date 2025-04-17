"""Adapter for backward compatibility with existing XMLProcessorService.

This module provides a compatibility layer that allows existing code to use
the enhanced XML service without requiring changes.
"""

import re
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.config import EulogosSettings
from app.dependencies import get_enhanced_catalog_service
from app.models.enhanced_urn import EnhancedURN
from app.models.xml_document import XMLDocument
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService


class XMLProcessorServiceAdapter:
    """Adapter for backward compatibility with existing XMLProcessorService."""

    def __init__(
        self,
        enhanced_service: Optional[EnhancedXMLService] = None,
        catalog_service: Optional[EnhancedCatalogService] = None,
        settings: Optional[EulogosSettings] = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            enhanced_service: Optional EnhancedXMLService instance
            catalog_service: Optional EnhancedCatalogService instance
            settings: Optional settings object
        """
        self.catalog_service = catalog_service or get_enhanced_catalog_service()
        self.enhanced_service = enhanced_service or EnhancedXMLService(
            catalog_service=self.catalog_service, settings=settings
        )

        # Issue deprecation warning
        warnings.warn(
            "XMLProcessorServiceAdapter is deprecated. Use EnhancedXMLService directly.",
            DeprecationWarning,
            stacklevel=2,
        )

    def resolve_urn_to_file_path(self, urn_obj: Union[str, EnhancedURN]) -> Optional[Path]:
        """Resolve URN to file path.

        Args:
            urn_obj: URN object or string

        Returns:
            Path object if found, None otherwise
        """
        return self.catalog_service.resolve_file_path(urn_obj)

    def load_xml(self, urn_obj: Union[str, EnhancedURN]) -> ET.Element:
        """Load XML file based on URN.

        Args:
            urn_obj: URN object or string

        Returns:
            ElementTree root element
        """
        document = self.enhanced_service.load_document(urn_obj)
        return document.root_element

    def extract_references(self, element: ET.Element, parent_ref: str = "") -> Dict[str, ET.Element]:
        """Extract references from XML element.

        Args:
            element: XML element
            parent_ref: Parent reference string

        Returns:
            Dictionary mapping reference strings to XML elements
        """
        document = XMLDocument(file_path="", urn="", root_element=element, references={})
        self.enhanced_service._extract_references_recursive(element, document, parent_ref)
        return {ref: ref_obj.element for ref, ref_obj in document.references.items()}

    def get_passage_by_reference(self, xml_root: ET.Element, reference: str) -> Optional[ET.Element]:
        """Get a passage by reference.

        Args:
            xml_root: XML root element
            reference: Reference string

        Returns:
            XML element if found, None otherwise
        """
        document = XMLDocument(file_path="", urn="", root_element=xml_root, references={})
        self.enhanced_service._extract_references_recursive(xml_root, document, "")
        return document.references[reference].element if reference in document.references else None

    def get_adjacent_references(self, xml_root: ET.Element, current_ref: str) -> Dict[str, Optional[str]]:
        """Get previous and next references.

        Args:
            xml_root: XML root element
            current_ref: Current reference string

        Returns:
            Dictionary with prev and next references
        """
        document = XMLDocument(file_path="", urn="", root_element=xml_root, references={})
        self.enhanced_service._extract_references_recursive(xml_root, document, "")

        ref_keys = list(document.references.keys())
        if not ref_keys or current_ref not in ref_keys:
            return {"prev": None, "next": None}

        ref_keys.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)])
        current_idx = ref_keys.index(current_ref)

        prev_ref = ref_keys[current_idx - 1] if current_idx > 0 else None
        next_ref = ref_keys[current_idx + 1] if current_idx < len(ref_keys) - 1 else None

        return {"prev": prev_ref, "next": next_ref}

    def transform_to_html(self, xml_root: ET.Element, target_ref: Optional[str] = None) -> str:
        """Transform XML to HTML.

        Args:
            xml_root: XML root element
            target_ref: Optional target reference

        Returns:
            HTML string
        """
        if target_ref:
            element = self.get_passage_by_reference(xml_root, target_ref)
            if element is None:
                return f"<p>Reference '{target_ref}' not found.</p>"
        else:
            element = xml_root

        return self.enhanced_service._element_to_html(element)

    def tokenize_text(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Process XML element into tokens.

        Args:
            element: XML element

        Returns:
            List of token dictionaries
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

    def parse_urn(self, urn: str) -> Dict[str, str]:
        """Parse a URN into its components.

        Args:
            urn: URN string

        Returns:
            Dictionary of URN components
        """
        urn_obj = EnhancedURN(value=urn)
        return {
            "namespace": urn_obj.namespace,
            "textgroup": urn_obj.textgroup,
            "work": urn_obj.work,
            "version": urn_obj.version,
            "reference": urn_obj.reference,
        }

    def get_file_path(self, urn: str) -> Optional[Path]:
        """Get file path for a URN.

        Args:
            urn: URN string

        Returns:
            Path object if found, None otherwise
        """
        urn_obj = EnhancedURN(value=urn)
        return self.catalog_service.resolve_file_path(urn_obj)

    def extract_text_content(self, file_path: Union[str, Path]) -> str:
        """Extract text content from XML file.

        Args:
            file_path: Path to XML file

        Returns:
            HTML string

        Raises:
            FileNotFoundError: If the file does not exist
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            content = ""

            text_parts = root.findall(".//{http://www.tei-c.org/ns/1.0}text") or root.findall(".//text")
            for text_part in text_parts:
                element_string = ET.tostring(text_part, encoding="unicode")
                content += self._clean_xml_tags(element_string)

            if not content:
                paragraphs = root.findall(".//{http://www.tei-c.org/ns/1.0}p") or root.findall(".//p")
                for p in paragraphs:
                    element_string = ET.tostring(p, encoding="unicode")
                    content += f"<p>{self._clean_xml_tags(element_string)}</p>"

            return content or f"<p><em>No text content found in {Path(file_path).name}</em></p>"

        except Exception as e:
            return f"<p><em>Error parsing XML: {str(e)}</em></p>"

    def _clean_xml_tags(self, xml_string: str) -> str:
        """Clean XML tags from a string.

        Args:
            xml_string: XML string

        Returns:
            Cleaned HTML string
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
