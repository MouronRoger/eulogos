"""Adapter for backward compatibility with the old XMLProcessorService."""

import logging
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from app.config import EulogosSettings
from app.models.enhanced_urn import EnhancedURN
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService

# Define Element type for type annotations
Element = TypeVar("Element", bound=ET.Element)

# Configure logger
logger = logging.getLogger(__name__)


class XMLProcessorServiceAdapter:
    """Adapter for backward compatibility with existing XMLProcessorService.

    This adapter provides the same interface as the original XMLProcessorService
    but delegates to the new EnhancedXMLService. This allows existing code to
    continue working without modification during the transition period.
    """

    def __init__(
        self,
        enhanced_service: Optional[EnhancedXMLService] = None,
        catalog_service: Optional[EnhancedCatalogService] = None,
        settings: Optional[EulogosSettings] = None,
    ):
        """Initialize the adapter.

        Args:
            enhanced_service: EnhancedXMLService instance to delegate to
            catalog_service: EnhancedCatalogService instance for path resolution
            settings: Optional settings for the adapter
        """
        # Import here to avoid circular imports
        from app.dependencies import get_catalog_service, get_xml_processor_service

        self.catalog_service = catalog_service or get_catalog_service()
        self.enhanced_service = enhanced_service or get_xml_processor_service()
        self.settings = settings or EulogosSettings()

        # Issue deprecation warning
        warnings.warn(
            "XMLProcessorServiceAdapter is deprecated. Use EnhancedXMLService directly.",
            DeprecationWarning,
            stacklevel=2,
        )

    def resolve_urn_to_file_path(self, urn_obj: Any) -> Path:
        """Resolve URN to file path.

        Args:
            urn_obj: URN object

        Returns:
            Path to the file
        """
        if not isinstance(urn_obj, EnhancedURN):
            urn_str = str(urn_obj)
            return self.catalog_service.resolve_file_path(urn_str)

        return self.catalog_service.resolve_file_path(urn_obj)

    def load_xml(self, urn_obj: Any) -> Element:
        """Load XML file based on URN.

        Args:
            urn_obj: URN object

        Returns:
            Root XML element
        """
        if not isinstance(urn_obj, EnhancedURN):
            urn_str = str(urn_obj)
            document = self.enhanced_service.load_document(urn_str)
        else:
            document = self.enhanced_service.load_document(urn_obj)

        return document.root_element

    def extract_references(self, element: Element) -> Dict[str, Element]:
        """Extract references from XML element.

        Args:
            element: XML element

        Returns:
            Dictionary mapping reference strings to elements
        """
        document = self.enhanced_service._create_document_from_element(element)
        return self.enhanced_service.extract_references(document)

    def get_passage_by_reference(self, element: Element, reference: str) -> Optional[Element]:
        """Get passage by reference.

        Args:
            element: XML element
            reference: Reference string

        Returns:
            Element for the passage or None if not found
        """
        document = self.enhanced_service._create_document_from_element(element)
        return self.enhanced_service.get_passage_element(document, reference)

    def get_passage(self, urn_or_element: Any, reference: Optional[str] = None) -> str:
        """Get passage text by URN and reference.

        Args:
            urn_or_element: URN or XML element
            reference: Optional reference string

        Returns:
            Text content of the passage
        """
        if isinstance(urn_or_element, (str, EnhancedURN)):
            return self.enhanced_service.get_passage(urn_or_element, reference)
        else:
            # It's an element, convert to document and get passage
            document = self.enhanced_service._create_document_from_element(urn_or_element)
            return self.enhanced_service.get_passage_text(document, reference)

    def get_adjacent_references(self, element_or_urn: Any, reference: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Get adjacent references.

        Args:
            element_or_urn: XML element or URN
            reference: Reference string

        Returns:
            Dictionary with "prev" and "next" references
        """
        if isinstance(element_or_urn, (str, EnhancedURN)):
            return self.enhanced_service.get_adjacent_references(element_or_urn, reference)
        else:
            # It's an element, convert to document and get adjacent references
            document = self.enhanced_service._create_document_from_element(element_or_urn)
            return self.enhanced_service.get_adjacent_references_from_document(document, reference)

    def tokenize_text(self, element: Element) -> List[Dict[str, Any]]:
        """Process XML element into tokens for word-level analysis.

        Args:
            element: XML element to tokenize

        Returns:
            List of token dictionaries with type, text, and index
        """
        if isinstance(element, str):
            # Handle case where element is actually a string
            return [{"type": "word", "text": word, "index": i} for i, word in enumerate(element.split())]

        document = self.enhanced_service._create_document_from_element(element)
        return self.enhanced_service.tokenize_document(document)

    def transform_to_html(self, element_or_urn: Any, reference: Optional[str] = None) -> str:
        """Transform XML to HTML.

        Args:
            element_or_urn: XML element or URN
            reference: Optional reference string

        Returns:
            HTML string
        """
        if isinstance(element_or_urn, (str, EnhancedURN)):
            return self.enhanced_service.transform_to_html(element_or_urn, reference)
        else:
            # It's an element, convert to document and transform
            document = self.enhanced_service._create_document_from_element(element_or_urn)
            if reference:
                return self.enhanced_service.transform_passage_to_html(document, reference)
            else:
                return self.enhanced_service.transform_document_to_html(document)

    def _process_element_to_html(self, element: Element, parent_ref: Optional[str] = None) -> str:
        """Process an element to HTML.

        Args:
            element: XML element
            parent_ref: Parent reference string

        Returns:
            HTML string
        """
        return self.enhanced_service._process_element_to_html(element, parent_ref)

    def parse_urn(self, urn_str: str) -> Dict[str, Any]:
        """Parse a URN string into components.

        Args:
            urn_str: URN string to parse

        Returns:
            Dictionary of URN components
        """
        urn_obj = EnhancedURN(value=urn_str)
        return urn_obj.get_id_components()

    def get_file_path(self, urn_str: str) -> Path:
        """Get file path for a URN string.

        Args:
            urn_str: URN string

        Returns:
            Path to the file
        """
        urn_obj = EnhancedURN(value=urn_str)
        return self.catalog_service.resolve_file_path(urn_obj)

    def extract_text_content(self, file_path: Path) -> str:
        """Extract text content from an XML file.

        Args:
            file_path: Path to the XML file

        Returns:
            Text content of the XML file
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            text = "".join(root.itertext())
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text content from {file_path}: {e}")
            return f"Error: {e}"
