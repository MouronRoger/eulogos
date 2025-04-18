"""Enhanced service for XML processing with additional functionality."""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from app.config import EulogosSettings
from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService


class EnhancedXMLService(XMLProcessorService):
    """Enhanced service for processing XML files with additional features."""

    def __init__(self, catalog_service: CatalogService, settings: EulogosSettings = None):
        """Initialize the enhanced XML service.

        Args:
            catalog_service: Catalog service instance for path resolution. Required
                as the catalog is the single source of truth for path resolution.
            settings: Application settings

        Raises:
            ValueError: If no catalog service is provided
        """
        data_dir = str(settings.data_dir) if settings else "data"

        if not catalog_service:
            raise ValueError(
                "EnhancedXMLService requires a catalog_service. "
                "The catalog is the single source of truth for path resolution."
            )

        super().__init__(data_path=data_dir, catalog_service=catalog_service)
        logger.debug("Initialized EnhancedXMLService with catalog_service and data_dir={}", data_dir)
        
    
        
    
        
    
        
    def extract_metadata(self, document: Any) -> Dict[str, Any]:
        """Extract metadata from a document.
        
        Args:
            document: XML document root element
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Extract basic document metadata - simple implementation
        # This could be expanded to extract more detailed metadata from the document
        try:
            # Try to get TEI header if present
            header = document.find(".//{http://www.tei-c.org/ns/1.0}teiHeader")
            if header is not None:
                # Extract title
                title = header.find(".//{http://www.tei-c.org/ns/1.0}title")
                if title is not None and title.text:
                    metadata["title"] = title.text.strip()
                
                # Extract author
                author = header.find(".//{http://www.tei-c.org/ns/1.0}author")
                if author is not None and author.text:
                    metadata["author"] = author.text.strip()
                
                # Extract publication info
                publisher = header.find(".//{http://www.tei-c.org/ns/1.0}publisher")
                if publisher is not None and publisher.text:
                    metadata["publisher"] = publisher.text.strip()
                
                # Extract date
                date = header.find(".//{http://www.tei-c.org/ns/1.0}date")
                if date is not None and date.text:
                    metadata["date"] = date.text.strip()
            
            # Get root element attributes
            for key, value in document.attrib.items():
                if key not in metadata:
                    metadata[key] = value
                    
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
            
        return metadata
        
    def get_document_statistics(self, document: Any) -> Dict[str, Any]:
        """Get statistics for a document.
        
        Args:
            document: XML document root element
            
        Returns:
            Dictionary of statistics
        """
        # Calculate basic statistics
        stats = {
            "element_count": self._count_elements(document),
            "text_length": len("".join(document.itertext())),
            "word_count": self._count_words(document),
            "reference_count": len(self.extract_references(document))
        }
        
        return stats
        
    def _count_elements(self, element: Any) -> int:
        """Count the number of elements in a document.
        
        Args:
            element: XML element
            
        Returns:
            Number of elements
        """
        count = 1  # Count the element itself
        for child in element:
            count += self._count_elements(child)
        return count
        
    def _count_words(self, element: Any) -> int:
        """Count the number of words in a document.
        
        Args:
            element: XML element
            
        Returns:
            Number of words
        """
        text = "".join(element.itertext())
        return len(text.split())
        
    def transform_element_to_html(self, element: Any) -> str:
        """Transform an XML element to HTML.
        
        Args:
            element: XML element
            
        Returns:
            HTML string
        """
        # Convert element to string
        return self._process_element_to_html(element)
        
    def extract_text_from_element(self, element: Any) -> str:
        """Extract text from an XML element.
        
        Args:
            element: XML element
            
        Returns:
            Text content
        """
        return "".join(element.itertext())
        
    def serialize_element(self, element: Any) -> str:
        """Serialize an XML element to string.
        
        Args:
            element: XML element
            
        Returns:
            XML string
        """
        return ET.tostring(element, encoding="unicode")
