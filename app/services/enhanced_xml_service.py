"""Enhanced service for XML document processing.

This service provides XML document handling with caching and reference extraction.
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Union

from loguru import logger

from app.config import EulogosSettings
from app.models.enhanced_urn import EnhancedURN
from app.models.xml_document import XMLDocument, XMLReference
from app.services.enhanced_catalog_service import EnhancedCatalogService

# Define Element type for type annotations
Element = TypeVar("Element", bound=ET.Element)


class EnhancedXMLService:
    """Enhanced service for XML document processing."""

    def __init__(self, catalog_service: EnhancedCatalogService, settings: Optional[EulogosSettings] = None):
        """Initialize the XML service.

        Args:
            catalog_service: Catalog service for path resolution
            settings: Optional settings object
        """
        self.catalog_service = catalog_service
        self.settings = settings or EulogosSettings()
        self._cache = OrderedDict()
        self._total_cache_size = 0  # Track total cache size in bytes

        # XML namespaces
        self.namespaces = {"ti": "http://chs.harvard.edu/xmlns/cts", "tei": "http://www.tei-c.org/ns/1.0"}

    def load_document(self, urn: Union[str, EnhancedURN, Any]) -> XMLDocument:
        """Load an XML document by URN.

        Args:
            urn: URN as string, EnhancedURN, or legacy URN object

        Returns:
            XMLDocument: Parsed XML document

        Raises:
            FileNotFoundError: If the XML file could not be found
            ValueError: If the URN is invalid
        """
        # Convert to EnhancedURN for unified handling
        if not isinstance(urn, EnhancedURN):
            try:
                urn_obj = EnhancedURN.from_original(urn)
            except ValueError as e:
                logger.error(f"Invalid URN format: {urn}")
                raise ValueError(f"Invalid URN format: {urn}") from e
        else:
            urn_obj = urn

        urn_str = urn_obj.value

        # Resolve file path from URN using catalog
        file_path = self.catalog_service.resolve_file_path(urn_obj)
        if not file_path or not file_path.exists():
            logger.error(f"XML file not found for URN {urn_str} at path {file_path}")
            raise FileNotFoundError(f"XML file not found for URN {urn_str}")

        # Get current file modification time
        current_mtime = os.path.getmtime(file_path)

        # Check cache if enabled
        if self.settings.enable_caching and urn_str in self._cache:
            document = self._cache[urn_str]

            # Check if cache is still valid
            if document.validate_cache(current_mtime):
                # Update access time and count
                document.last_accessed = datetime.utcnow()
                document.access_count += 1

                # Move to end of OrderedDict to maintain LRU order
                self._cache.move_to_end(urn_str)

                logger.debug(f"Cache hit for URN {urn_str}")
                return document
            else:
                # Cache is invalid, remove it
                logger.debug(f"Cache invalid for URN {urn_str}, reloading")
                self._remove_from_cache(urn_str)

        logger.debug(f"Cache miss for URN {urn_str}")

        try:
            logger.debug(f"Loading XML file from {file_path}")

            # Parse XML document
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Create document object
            document = XMLDocument(
                file_path=str(file_path),
                urn=urn_str,
                root_element=root,
                references={},
                metadata=self._extract_metadata(root),
                last_accessed=datetime.utcnow(),
                access_count=1,
            )

            # Extract references
            self._extract_references(document)

            # Update cache metadata
            document.update_cache_metadata(current_mtime)

            # Add to cache if enabled
            if self.settings.enable_caching:
                self._add_to_cache(urn_str, document)

            logger.debug(f"Loaded XML document with {len(document.references)} references")
            return document

        except Exception as e:
            logger.error(f"Error loading XML document {file_path} for URN {urn_str}: {e}")
            raise

    def _add_to_cache(self, urn: str, document: XMLDocument) -> None:
        """Add a document to the cache, managing size limits.

        Args:
            urn: URN string
            document: XMLDocument to cache
        """
        # Check if we need to make space
        while (
            self._total_cache_size + document.cache_size > self.settings.cache_max_size_bytes
            or len(self._cache) >= self.settings.xml_cache_size
        ):
            if not self._cache:
                break
            # Remove least recently used item
            self._remove_from_cache(next(iter(self._cache)))

        # Add new document
        self._cache[urn] = document
        self._total_cache_size += document.cache_size
        logger.debug(f"Added document to cache: {urn} (size: {document.cache_size} bytes)")

    def _remove_from_cache(self, urn: str) -> None:
        """Remove a document from the cache.

        Args:
            urn: URN string to remove
        """
        if urn in self._cache:
            document = self._cache[urn]
            self._total_cache_size -= document.cache_size
            del self._cache[urn]
            logger.debug(f"Removed document from cache: {urn}")

    def invalidate_cache(self, urn: Optional[str] = None) -> None:
        """Invalidate cache entries.

        Args:
            urn: Optional URN string to invalidate. If None, invalidates entire cache.
        """
        if urn is None:
            # Clear entire cache
            self._cache.clear()
            self._total_cache_size = 0
            logger.info("Cleared entire cache")
        elif urn in self._cache:
            # Remove specific entry
            self._remove_from_cache(urn)
            logger.info(f"Invalidated cache for URN: {urn}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache.

        Returns:
            Dictionary containing cache statistics
        """
        return {
            "total_entries": len(self._cache),
            "total_size_bytes": self._total_cache_size,
            "max_size_bytes": self.settings.cache_max_size_bytes,
            "max_entries": self.settings.xml_cache_size,
            "entries": [
                {
                    "urn": urn,
                    "size_bytes": doc.cache_size,
                    "access_count": doc.access_count,
                    "last_accessed": doc.last_accessed.isoformat(),
                    "valid": doc.cache_valid,
                }
                for urn, doc in self._cache.items()
            ],
        }

    def _extract_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """Extract metadata from an XML document.

        Args:
            root: XML root element

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        try:
            # Extract title
            title_elem = root.find(".//tei:title", self.namespaces)
            if title_elem is not None and title_elem.text:
                metadata["title"] = title_elem.text

            # Extract editor
            editor_elem = root.find(".//tei:editor", self.namespaces)
            if editor_elem is not None and editor_elem.text:
                metadata["editor"] = editor_elem.text

            # Extract translator
            translator_elem = root.find(".//tei:editor[@role='translator']", self.namespaces)
            if translator_elem is not None and translator_elem.text:
                metadata["translator"] = translator_elem.text

            # Extract language
            lang_attr = root.get("{http://www.w3.org/XML/1998/namespace}lang")
            if lang_attr:
                metadata["language"] = lang_attr

        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")

        return metadata

    def _extract_references(self, document: XMLDocument) -> Dict[str, XMLReference]:
        """Extract references from an XML document.

        Args:
            document: XML document object

        Returns:
            Dictionary of references
        """
        try:
            self._extract_references_recursive(document.root_element, document, "")
            logger.debug(f"Extracted {len(document.references)} references")
            return document.references
        except Exception as e:
            logger.error(f"Error extracting references: {e}")
            return {}

    def _extract_references_recursive(self, element: ET.Element, document: XMLDocument, parent_ref: str) -> None:
        """Recursively extract references from an element.

        Args:
            element: XML element
            document: XML document
            parent_ref: Parent reference string
        """
        # Check if this element has an 'n' attribute
        n_value = element.get("n")
        current_ref = ""

        if n_value:
            current_ref = f"{parent_ref}.{n_value}" if parent_ref else n_value

            # Create reference
            reference = XMLReference(
                reference=current_ref,
                element=element,
                text_content=self._get_element_text(element),
                parent_ref=parent_ref,
            )
            document.references[current_ref] = reference

            # Add this reference as a child of the parent
            if parent_ref and parent_ref in document.references:
                document.references[parent_ref].child_refs.append(current_ref)
        else:
            current_ref = parent_ref

        # Process children
        for child in element:
            self._extract_references_recursive(child, document, current_ref)

    def _get_element_text(self, element: ET.Element) -> str:
        """Get text content of an element, including children.

        Args:
            element: XML element

        Returns:
            Text content
        """
        text = element.text or ""
        for child in element:
            text += self._get_element_text(child)
            if child.tail:
                text += child.tail
        return text.strip()

    def get_passage(self, urn: Union[str, EnhancedURN, Any], reference: Optional[str] = None) -> Optional[str]:
        """Get a passage from an XML document by URN and reference.

        Args:
            urn: URN in any supported format
            reference: Optional reference string

        Returns:
            Text content or None if not found
        """
        try:
            document = self.load_document(urn)

            # If no reference, return the whole document text
            if not reference:
                return self._get_element_text(document.root_element)

            # Get the specific reference
            if reference in document.references:
                return document.references[reference].text_content

            logger.warning(f"Reference {reference} not found in {urn}")
            return None

        except Exception as e:
            logger.error(f"Error getting passage {reference} from {urn}: {e}")
            return None

    def get_adjacent_references(self, urn: Union[str, EnhancedURN, Any], current_ref: str) -> Dict[str, Optional[str]]:
        """Get previous and next references relative to current reference.

        Args:
            urn: URN in any supported format
            current_ref: Current reference string

        Returns:
            Dictionary with 'prev' and 'next' references
        """
        try:
            document = self.load_document(urn)

            # Get all reference keys
            ref_keys = list(document.references.keys())

            # If current reference not found or no references
            if not ref_keys or current_ref not in ref_keys:
                return {"prev": None, "next": None}

            # Sort references naturally
            ref_keys.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)])

            # Find current reference index
            current_idx = ref_keys.index(current_ref)

            # Get previous and next references
            prev_ref = ref_keys[current_idx - 1] if current_idx > 0 else None
            next_ref = ref_keys[current_idx + 1] if current_idx < len(ref_keys) - 1 else None

            return {"prev": prev_ref, "next": next_ref}

        except Exception as e:
            logger.error(f"Error getting adjacent references for {current_ref} in {urn}: {e}")
            return {"prev": None, "next": None}

    def transform_to_html(self, urn: Union[str, EnhancedURN, Any], reference: Optional[str] = None) -> str:
        """Transform a passage to HTML.

        Args:
            urn: URN in any supported format
            reference: Optional reference string

        Returns:
            HTML string
        """
        try:
            document = self.load_document(urn)

            # Get the root element or a specific reference
            element = document.root_element
            if reference and reference in document.references:
                element = document.references[reference].element

            # Transform to HTML
            return self._element_to_html(element)

        except Exception as e:
            logger.error(f"Error transforming {urn} to HTML: {e}")
            return f"<div class='error'>Error: {str(e)}</div>"

    def _element_to_html(self, element: ET.Element) -> str:
        """Convert an XML element to HTML.

        Args:
            element: XML element

        Returns:
            HTML string
        """
        try:
            # Handle different tag types
            tag = element.tag.split("}")[-1]  # Remove namespace
            attrs = element.attrib.copy()

            # Create HTML attributes string
            html_attrs = ""
            for k, v in attrs.items():
                # Handle namespace attributes
                if "}" in k:
                    k = k.split("}")[-1]
                html_attrs += f' data-{k}="{v}"'

            # Map TEI elements to HTML
            tag_map = {
                "div": "div",
                "p": "p",
                "head": "h3",
                "l": "span class='line'",
                "speaker": "b",
                "quote": "blockquote",
                "name": "em",
                "note": "span class='note'",
                "foreign": "em",
                "hi": "em",
                "ref": "a",
            }

            html_tag = tag_map.get(tag, "span")

            # Special handling for ref tags
            if tag == "ref" and "target" in attrs:
                html_tag = f"a href='{attrs['target']}'"

            # Start tag
            html = f"<{html_tag} data-tei='{tag}'{html_attrs}>"

            # Add text content
            if element.text:
                html += element.text

            # Process children
            for child in element:
                html += self._element_to_html(child)
                if child.tail:
                    html += child.tail

            # End tag
            tag_name = html_tag.split()[0]  # Get just the tag name, not attributes
            html += f"</{tag_name}>"

            return html
        except Exception as e:
            logger.error(f"Error converting element to HTML: {e}")
            return f"<span class='error'>Error processing element: {e}</span>"

    def _create_document_from_element(self, element: ET.Element) -> XMLDocument:
        """Create an XMLDocument instance from an element.

        This is used by the adapter for backward compatibility.

        Args:
            element: XML element to convert

        Returns:
            XMLDocument instance
        """
        from app.models.xml_document import XMLDocument

        # Create a basic document with the element
        document = XMLDocument(
            root_element=element, references={}, metadata={}, urn=None  # No URN associated with this document
        )

        # Extract references from the element
        references = self._extract_references(document)

        # Update the document with references
        document.references = references

        return document

    def tokenize_document(self, document: XMLDocument) -> List[Dict[str, Any]]:
        """Process XML document into tokens for word-level analysis.

        Args:
            document: XML document to tokenize

        Returns:
            List of token dictionaries with type, text, and index
        """
        tokens = []
        word_index = 0

        try:
            # Get all text from the document
            text = "".join(document.root_element.itertext())

            # Simple tokenization by spaces and punctuation
            import re

            words = re.findall(r"\w+", text)

            for word in words:
                tokens.append({"type": "word", "text": word, "index": word_index})
                word_index += 1

            return tokens
        except Exception as e:
            logger.error(f"Error tokenizing document: {e}")
            return []

    def transform_document_to_html(self, document: XMLDocument) -> str:
        """Transform an entire document to HTML.

        Args:
            document: XML document to transform

        Returns:
            HTML string
        """
        try:
            html_parts = []
            html_parts.append("<div>")

            # Transform the entire document
            for ref, element in document.references.items():
                html = self._process_element_to_html(element, ref)
                html_parts.append(html)

            html_parts.append("</div>")
            return "".join(html_parts)
        except Exception as e:
            logger.error(f"Error transforming document to HTML: {e}")
            return f"<div class='error'>Error: {e}</div>"

    def transform_passage_to_html(self, document: XMLDocument, reference: str) -> str:
        """Transform a specific passage to HTML.

        Args:
            document: XML document
            reference: Reference string

        Returns:
            HTML string
        """
        try:
            element = self.get_passage_element(document, reference)
            if element is None:
                return f"<div class='error'>Reference not found: {reference}</div>"

            return self._process_element_to_html(element, reference)
        except Exception as e:
            logger.error(f"Error transforming passage to HTML: {e}")
            return f"<div class='error'>Error: {e}</div>"

    def get_passage_element(self, document: XMLDocument, reference: str) -> Optional[Element]:
        """Get passage element by reference.

        Args:
            document: XML document
            reference: Reference string

        Returns:
            Element for the passage or None if not found
        """
        try:
            return document.references.get(reference)
        except Exception as e:
            logger.error(f"Error getting passage element: {e}")
            return None

    def get_passage_text(self, document: XMLDocument, reference: Optional[str] = None) -> str:
        """Get passage text.

        Args:
            document: XML document
            reference: Optional reference string

        Returns:
            Text content of the passage
        """
        try:
            if reference:
                element = self.get_passage_element(document, reference)
                if element is None:
                    return f"Reference not found: {reference}"
                return "".join(element.itertext())
            else:
                # Return the entire document text
                return "".join(document.root_element.itertext())
        except Exception as e:
            logger.error(f"Error getting passage text: {e}")
            return f"Error: {e}"

    def get_adjacent_references_from_document(
        self, document: XMLDocument, reference: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """Get adjacent references from a document.

        Args:
            document: XML document
            reference: Reference string

        Returns:
            Dictionary with "prev" and "next" references
        """
        try:
            refs = list(document.references.keys())
            if not refs:
                return {"prev": None, "next": None}

            # Sort references
            refs.sort(key=self._sort_reference_key)

            if reference is None:
                # Return first reference as next if no reference provided
                return {"prev": None, "next": refs[0] if refs else None}

            # Find the current reference index
            try:
                current_index = refs.index(reference)
            except ValueError:
                # Reference not found, return first as fallback
                return {"prev": None, "next": refs[0] if refs else None}

            # Get previous and next
            prev_ref = refs[current_index - 1] if current_index > 0 else None
            next_ref = refs[current_index + 1] if current_index < len(refs) - 1 else None

            return {"prev": prev_ref, "next": next_ref}
        except Exception as e:
            logger.error(f"Error getting adjacent references: {e}")
            return {"prev": None, "next": None}

    def _process_element_to_html(self, element: Element, parent_ref: Optional[str] = None) -> str:
        """Process an element to HTML.

        Args:
            element: Element to process
            parent_ref: Optional parent reference

        Returns:
            HTML string
        """
        try:
            # Handle different tag types
            attrs = element.attrib.copy()

            # Create HTML attributes string
            html_attrs = ""
            for k, v in attrs.items():
                # Handle namespace attributes
                if "}" in k:
                    k = k.split("}")[-1]

                # Use data-ref for n attribute to make it accessible in CSS
                if k == "n":
                    html_attrs += f' data-ref="{v}"'
                    html_attrs += f' id="ref-{parent_ref}.{v}" ' if parent_ref else f' id="ref-{v}" '
                else:
                    html_attrs += f' data-{k}="{v}"'

            # Add reference as class
            ref_attr = ""
            if "n" in attrs:
                ref = f"{parent_ref}.{attrs['n']}" if parent_ref else attrs["n"]
                ref_attr = f' class="ref" data-ref="{ref}"'

            # Start tag
            html = f"<div{ref_attr}{html_attrs}>"

            # Add reference number if this is a reference
            if "n" in attrs:
                html += f'<span class="ref-num">{attrs["n"]}</span>'

            # Add text content
            if element.text:
                html += f'<div><span class="text">{element.text}</span></div>'

            # Process children
            for child in element:
                html += self._process_element_to_html(
                    child, f"{parent_ref}.{attrs['n']}" if parent_ref and "n" in attrs else attrs.get("n", "")
                )
                if child.tail:
                    html += f'<span class="tail">{child.tail}</span>'

            # End tag
            html += "</div>"

            return html
        except Exception as e:
            logger.error(f"Error processing element to HTML: {e}")
            return f"<div class='error'>Error: {e}</div>"
