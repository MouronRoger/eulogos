"""Service for processing XML files with reference handling capabilities."""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union

from loguru import logger

from app.config import EulogosSettings
from app.services.catalog_service import CatalogService

# Define Element type for type annotations
Element = TypeVar("Element", bound=ET.Element)


class XMLProcessorService:
    """Service for processing XML files with reference handling."""

    def __init__(self, catalog_service: CatalogService, data_path: str = "data", settings: Optional[EulogosSettings] = None):
        """Initialize the XML processor service.

        Args:
            catalog_service: Catalog service for path resolution. Required
                as the catalog is the single source of truth for path resolution.
            data_path: Path to the data directory
            settings: Optional application settings

        Raises:
            ValueError: If no catalog service is provided
        """
        if not catalog_service:
            raise ValueError(
                "XMLProcessorService requires a catalog_service. "
                "The catalog is the single source of truth for path resolution."
            )
            
        self.data_path = Path(data_path)
        self.catalog_service = catalog_service
        
        if settings:
            self.data_path = Path(str(settings.data_dir))
            
        logger.debug("Initialized XMLProcessorService with catalog_service and data_path={}", self.data_path)

    def load_xml_from_path(self, path: str) -> Optional[Element]:
        """Load XML file from path.

        Args:
            path: Path to the XML file relative to data directory

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
            # Check file size to avoid parsing extremely large files
            file_size = filepath.stat().st_size
            logger.debug(f"XML file size: {file_size} bytes")
            
            # Try to parse the XML file
            root = ET.parse(str(filepath)).getroot()
            # Log success with element details
            logger.debug(
                f"Successfully parsed XML file: {filepath}, "
                f"root tag: {root.tag if root is not None else 'None'}, "
                f"child count: {len(list(root)) if root is not None else 0}"
            )
            
            # Validate that we got a proper Element
            if root is None:
                logger.error(f"XML parsing returned None for file: {filepath}")
                return None
                
            return root
        except ET.ParseError as e:
            logger.exception(f"XML parse error for file {filepath}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error loading XML from {filepath}: {e}")
            raise
        
    def load_document(self, text_id: str) -> Optional[Element]:
        """Load document by text ID.
        
        Args:
            text_id: ID of the text to load
            
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
        
        # Validate path
        if not text.path:
            logger.error(f"Text has no path: {text_id}")
            raise FileNotFoundError(f"Text has no path: {text_id}")
            
        # Load XML from path
        try:
            xml_root = self.load_xml_from_path(text.path)
            logger.debug(
                f"load_document result: {'Success' if xml_root is not None else 'None'}, "
                f"type: {type(xml_root)}"
            )
            return xml_root
        except Exception as e:
            logger.exception(f"Error loading document for text_id {text_id}: {e}")
            return None

    def extract_references(self, xml_root: Optional[Element]) -> Dict[str, Element]:
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

    def _extract_references_recursive(self, element: Optional[Element], parent_ref: str, references: Dict[str, Element]) -> None:
        """Recursively extract references from XML.

        Args:
            element: Current XML element
            parent_ref: Parent reference string
            references: Dictionary to store references
        """
        if element is None:
            logger.debug(f"Skipping None element in reference extraction with parent_ref: {parent_ref}")
            return
            
        try:
            n_value = element.get("n")
            if n_value:
                ref = f"{parent_ref}.{n_value}" if parent_ref else n_value
                references[ref] = element
            else:
                ref = parent_ref

            for child in element:
                self._extract_references_recursive(child, ref, references)
        except AttributeError as e:
            logger.error(f"AttributeError in extract_references_recursive: {e}, parent_ref={parent_ref}")
        except Exception as e:
            logger.error(f"Unexpected error in extract_references_recursive: {e}, parent_ref={parent_ref}")

    def get_passage_by_reference(self, xml_root: Optional[Element], reference: Optional[str]) -> Optional[Element]:
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

        # Log the reference and xml_root details
        logger.debug(f"Getting passage for reference: {reference}, xml_root tag: {xml_root.tag}")
        
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
                logger.warning(f"Reference part '{part}' not found in path {reference}")
                return None

        logger.debug(f"Found passage for reference {reference}: {current.tag if current else 'None'}")
        return current

    def get_adjacent_references(self, xml_root: Optional[Element], reference: Optional[str] = None) -> Dict[str, Optional[str]]:
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
            
        sorted_refs = sorted(references.keys())

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

    def tokenize_text(self, element: Optional[Element]) -> List[Dict[str, Any]]:
        """Process XML element into tokens for word-level analysis.

        Args:
            element: XML element to tokenize

        Returns:
            List of token dictionaries with type, text, and index
        """
        tokens = []
        
        if element is None:
            logger.warning("Cannot tokenize None element")
            return tokens
            
        word_index = 0

        try:
            text = "".join(element.itertext())
            words = re.findall(r"\w+|\s+|[^\w\s]", text)

            for word in words:
                if word.strip():
                    tokens.append({"type": "word", "text": word, "index": word_index})
                    word_index += 1
                    
            logger.debug(f"Tokenized text: {len(tokens)} tokens generated")
            return tokens
        except Exception as e:
            logger.exception(f"Error tokenizing text: {e}")
            return tokens

    def transform_to_html(self, text_id: str, target_ref: Optional[str] = None) -> str:
        """Transform XML to HTML with reference attributes.

        Args:
            text_id: ID of the text to transform
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
    
    def _transform_element_to_html(self, xml_root: Optional[Element], target_ref: Optional[str] = None) -> str:
        """Transform XML element to HTML with reference attributes.
        
        Args:
            xml_root: Root XML element
            target_ref: Optional specific reference to display
            
        Returns:
            HTML string with reference attributes
        """
        # Add more detailed logging
        logger.debug(
            f"_transform_element_to_html called with xml_root type: {type(xml_root)}, "
            f"target_ref: {target_ref}"
        )
        
        # Add proper None checking
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

            # Log the number of elements to process
            logger.debug(f"Processing {len(elements)} elements for HTML transformation")
            
            for element in elements:
                # Validate each element before processing
                if element is None:
                    logger.error("Cannot process None element to HTML")
                    html.append("<div class='error'>Error: Element is None</div>")
                    continue
                    
                # Log element details
                logger.debug(f"Processing element with tag: {element.tag}, attributes: {element.attrib}")
                
                # Process the element to HTML
                try:
                    processed_html = self._process_element_to_html(element)
                    
                    # Validate processed HTML
                    if processed_html is None:
                        logger.error(f"_process_element_to_html returned None for element {element.tag}")
                        processed_html = "<div class='error'>Error: Element processing failed</div>"
                    elif not processed_html:
                        logger.error(f"_process_element_to_html returned empty string for element {element.tag}")
                        processed_html = "<div class='error'>Error: Element processing returned empty content</div>"
                        
                    html.append(processed_html)
                except Exception as element_error:
                    logger.exception(f"Error processing element to HTML: {element_error}")
                    html.append(f"<div class='error'>Error processing element: {str(element_error)}</div>")

            # Ensure we have content to return
            if not html:
                logger.error("No HTML content generated during transformation")
                return "<div class='error'>Error: No content could be generated</div>"
                
            # Join the HTML parts
            result = "".join(html)
            
            # Log the final result length
            logger.debug(f"Final HTML result length: {len(result) if result else 0}")
            
            # Final validation before returning
            if not result:
                logger.error("Empty string generated after joining HTML parts")
                return "<div class='error'>Error: Empty content generated</div>"
                
            return result
            
        except Exception as e:
            logger.exception(f"Unexpected error in _transform_element_to_html: {e}")
            return f"<div class='error'>Error transforming XML: {str(e)}</div>"

    def _process_element_to_html(self, element: Optional[Element], parent_ref: str = "") -> str:
        """Process an XML element to HTML with reference attributes.

        Args:
            element: XML element to process
            parent_ref: Parent reference string

        Returns:
            HTML string representation of the element
        """
        if element is None:
            logger.error(f"Cannot process None element to HTML for parent_ref: {parent_ref}")
            return "<div class='error'>Error: NULL element</div>"
            
        try:
            # Log element details for debugging
            logger.debug(f"Processing element: tag={element.tag}, attrib={element.attrib}, parent_ref={parent_ref}")
            
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
                text_content = element.text.strip()
                logger.debug(f"Element text: '{text_content[:20]}...' (truncated)")
                html += f'<span class="text">{element.text}</span>'

            # Process children
            child_count = 0
            for child in element:
                child_count += 1
                try:
                    child_html = self._process_element_to_html(child, ref)
                    if not child_html:
                        logger.warning(f"Empty HTML returned for child {child.tag}")
                        child_html = "<span class='processing-error'>Error processing child</span>"
                    html += child_html
                except Exception as child_error:
                    logger.exception(f"Error processing child element {child.tag}: {child_error}")
                    html += f"<div class='error'>Error processing child element: {str(child_error)}</div>"

                # Handle tail text after child
                try:
                    if child.tail and child.tail.strip():
                        html += f'<span class="text">{child.tail}</span>'
                except Exception as tail_error:
                    logger.exception(f"Error processing child tail: {tail_error}")
                    html += f"<div class='error'>Error processing tail: {str(tail_error)}</div>"
                    
            html += "</div>"
            
            # Log processing result summary
            logger.debug(f"Processed element {element.tag} with {child_count} children, HTML length: {len(html)}")
            
            return html
        except Exception as e:
            logger.exception(f"Error in _process_element_to_html for element {element.tag if hasattr(element, 'tag') else 'unknown'}: {e}")
            return f"<div class='error'>Error processing element: {str(e)}</div>"

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
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Log file details for debugging
            logger.debug(f"Extracting text content from file: {file_path}, size: {file_path.stat().st_size} bytes")
            
            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            if root is None:
                logger.error(f"XML parsing returned None root for file: {file_path}")
                return f"<p><em>Error: Failed to parse XML file {file_path.name}</em></p>"

            # Extract text content
            content = ""

            # Try to find TEI text elements
            text_parts = root.findall(".//{http://www.tei-c.org/ns/1.0}text") or root.findall(".//text")
            logger.debug(f"Found {len(text_parts)} text elements in XML")

            for text_part in text_parts:
                # Convert element to string
                try:
                    element_string = ET.tostring(text_part, encoding="unicode")
                    # Simple cleaning of XML tags
                    content += self._clean_xml_tags(element_string)
                except Exception as part_error:
                    logger.exception(f"Error processing text part: {part_error}")
                    content += f"<p><em>Error processing text part: {str(part_error)}</em></p>"

            # If no content found, try different approach
            if not content:
                logger.debug("No content found in text elements, trying paragraphs")
                # Try getting all paragraphs
                paragraphs = root.findall(".//{http://www.tei-c.org/ns/1.0}p") or root.findall(".//p")
                logger.debug(f"Found {len(paragraphs)} paragraph elements in XML")

                for p in paragraphs:
                    # Convert element to string
                    try:
                        element_string = ET.tostring(p, encoding="unicode")
                        # Simple cleaning of XML tags
                        content += f"<p>{self._clean_xml_tags(element_string)}</p>"
                    except Exception as p_error:
                        logger.exception(f"Error processing paragraph: {p_error}")
                        content += f"<p><em>Error processing paragraph: {str(p_error)}</em></p>"

            # If still no content, return a message
            if not content:
                logger.warning(f"No text content found in {file_path.name}")
                # Fallback: try to get any text content from the root
                try:
                    fallback_text = "".join(root.itertext())
                    if fallback_text:
                        content = f"<p>{fallback_text[:1000]}...</p>"
                        logger.debug(f"Using fallback text content, length: {len(fallback_text)}")
                    else:
                        content = f"<p><em>No text content found in {file_path.name}</em></p>"
                except Exception as fallback_error:
                    logger.exception(f"Error getting fallback text: {fallback_error}")
                    content = f"<p><em>No text content found in {file_path.name}</em></p>"

            logger.debug(f"Extracted content length: {len(content)}")
            return content

        except Exception as e:
            logger.exception(f"Error extracting text content: {e}")
            return f"<p><em>Error parsing XML: {str(e)}</em></p>"

    def _clean_xml_tags(self, xml_string: str) -> str:
        """Clean XML tags from a string, leaving basic formatting.

        Args:
            xml_string: The XML string to clean

        Returns:
            The cleaned string with basic HTML formatting
        """
        if not xml_string:
            logger.warning("Empty XML string passed to _clean_xml_tags")
            return ""
            
        try:
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
        except Exception as e:
            logger.exception(f"Error in _clean_xml_tags: {e}")
            return f"Error cleaning XML: {str(e)}"
        
    # Enhanced XML methods from EnhancedXMLService
    
    def extract_metadata(self, document: Optional[Any]) -> Dict[str, Any]:
        """Extract metadata from a document.
        
        Args:
            document: XML document root element
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        if document is None:
            logger.error("Cannot extract metadata from None document")
            return metadata
            
        # Extract basic document metadata - simple implementation
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
                    
            logger.debug(f"Extracted metadata keys: {', '.join(metadata.keys())}")
            
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
            
        return metadata
        
    def get_document_statistics(self, document: Optional[Any]) -> Dict[str, Any]:
        """Get statistics for a document.
        
        Args:
            document: XML document root element
            
        Returns:
            Dictionary of statistics
        """
        # Add proper None checking
        if document is None:
            logger.error("Cannot get statistics from None document")
            return {
                "element_count": 0,
                "text_length": 0,
                "word_count": 0,
                "reference_count": 0,
                "error": "Document is None"
            }
            
        # Calculate basic statistics
        try:
            stats = {
                "element_count": self._count_elements(document),
                "text_length": len("".join(document.itertext())),
                "word_count": self._count_words(document),
                "reference_count": len(self.extract_references(document))
            }
            logger.debug(f"Document statistics: {stats}")
            return stats
        except (AttributeError, TypeError) as e:
            logger.error(f"Error calculating document statistics: {e}")
            stats = {
                "element_count": 0,
                "text_length": 0,
                "word_count": 0,
                "reference_count": 0,
                "error": str(e)
            }
            return stats
        except Exception as e:
            logger.exception(f"Unexpected error in get_document_statistics: {e}")
            return {
                "element_count": 0,
                "text_length": 0,
                "word_count": 0,
                "reference_count": 0,
                "error": f"Unexpected error: {str(e)}"
            }
        
    def _count_elements(self, element: Optional[Any]) -> int:
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
        except (AttributeError, TypeError):
            return 0
        
    def _count_words(self, element: Optional[Any]) -> int:
        """Count the number of words in a document.
        
        Args:
            element: XML element
            
        Returns:
            Number of words
        """
        if element is None:
            return 0
            
        try:
            text = "".join(element.itertext())
            return len(text.split())
        except (AttributeError, TypeError):
            return 0
        
    def transform_element_to_html(self, element: Optional[Any]) -> str:
        """Transform an XML element to HTML.
        
        Args:
            element: XML element
            
        Returns:
            HTML string
        """
        if element is None:
            logger.error("Cannot transform None element to HTML in transform_element_to_html")
            return "<div class='error'>Error: Element is None</div>"
            
        # Convert element to string
        return self._process_element_to_html(element)
        
    def extract_text_from_element(self, element: Optional[Any]) -> str:
        """Extract text from an XML element.
        
        Args:
            element: XML element
            
        Returns:
            Text content
        """
        # Add proper None checking
        if element is None:
            logger.error("Cannot extract text from None element")
            return ""
            
        try:
            text = "".join(element.itertext())
            logger.debug(f"Extracted text from element: {len(text)} characters")
            return text
        except (AttributeError, TypeError) as e:
            logger.error(f"Error extracting text: {e}")
            return ""
        
    def serialize_element(self, element: Optional[Any]) -> str:
        """Serialize an XML element to string.
        
        Args:
            element: XML element
            
        Returns:
            XML string
        """
        # Add proper None checking
        if element is None:
            logger.error("Cannot serialize None element")
            return ""
            
        try:
            xml_string = ET.tostring(element, encoding="unicode")
            logger.debug(f"Serialized element to string: {len(xml_string)} characters")
            return xml_string
        except (TypeError, ValueError) as e:
            logger.error(f"Error serializing element: {e}")
            return ""
