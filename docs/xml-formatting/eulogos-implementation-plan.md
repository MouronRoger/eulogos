# Eulogos Text Export System Implementation Plan

## Overview

This document outlines the implementation plan for enhancing the Eulogos project with a robust text display and export system, focusing on proper XML processing and multi-format export capabilities. This implementation will ensure ancient Greek texts are both readable in the browser and exportable in various formats (PDF, ePub, Markdown, DOCX) for offline access.

## Background

The Eulogos project currently has limitations in its XML processing that affect the quality of text display and export capabilities. The project requires:

1. Enhanced XML formatting for proper text display in the browser
2. Export functionality for multiple document formats
3. Preservation of textual structure, references, and formatting

## Implementation Components

### 1. URN Model (app/models/urn.py)
**Timeline: 1 week**

- Create a Pydantic model for parsing and manipulating CTS URNs
- Implement methods:
  - `parse()`: Extract namespace, textgroup, work, version, and reference components
  - `up_to(level)`: Get URN up to specified hierarchy level
  - `replace(level, value)`: Replace a component of the URN
  - `get_file_path()`: Get file path from URN
  - `get_adjacent_references()`: Get previous/next references
- Add comprehensive validation for URN components
- Create unit tests with >90% coverage

### 2. Enhanced XMLProcessorService
**Timeline: 2-3 weeks**

- Update existing service with reference handling capabilities:
  - `extract_references()`: Extract hierarchical references from TEI XML elements
  - `get_passage_by_reference()`: Retrieve specific text passage by reference
  - `get_adjacent_references()`: Get previous/next references relative to current
  - `transform_to_html()`: Convert XML to HTML with reference attributes
  - `tokenize_text()`: Process text into word-level tokens for detailed analysis
- Implement token-level text processing
- Create integration tests simulating real XML documents
- Test with large documents to ensure performance

### 3. ExportService (app/services/export_service.py)
**Timeline: 2 weeks**

- Create service for multi-format exports with methods:
  - `export_to_pdf()`: Export to PDF using WeasyPrint
  - `export_to_epub()`: Export to ePub using ebooklib
  - `export_to_mobi()`: Export to MOBI using Calibre
  - `export_to_markdown()`: Export to Markdown
  - `export_to_docx()`: Export to DOCX using python-docx
  - `export_to_latex()`: Export to LaTeX with XeLaTeX support
  - `export_to_html()`: Export to standalone HTML
- Implement format-specific processing and options
- Add proper error handling and dependency checks
- Develop tests for each export format

### 4. Export API Endpoints (app/routers/export.py)
**Timeline: 1 week**

- Create router for export functionality:
  - `GET /export/{urn}`: Main export endpoint with format parameters
  - `GET /export/options`: Get available export options for UI
  - `GET /export/formats`: Get supported export formats
- Implement endpoints with option parsing and validation
- Add proper error handling and user feedback
- Develop integration tests for API endpoints

### 5. UI Integration
**Timeline: 1 week**

- Update reader template with export UI components:
  - Format selection dropdown
  - Option selection controls
  - Download button
  - Progress indicator
- Add client-side validation for export options
- Create user-friendly error messages
- Implement responsive design for various devices
- Test cross-browser compatibility

## Phased Implementation

### Phase 1: Core Reference Handling (3-4 weeks)
- Implement URN Model
- Enhance XMLProcessorService with reference handling
- Create basic reader interface with reference navigation
- Set up test infrastructure
- Implement documentation framework

### Phase 2: Export Service (2-3 weeks)
- Implement ExportService with all formats
- Create export API endpoints
- Add basic UI components for export
- Integrate external dependencies
- Develop format-specific transformations

### Phase 3: Enhancement and Optimization (1-2 weeks)
- Refine UI for better user experience
- Optimize performance for large texts
- Implement caching for frequent exports
- Enhance error handling and feedback
- Improve accessibility features
- Complete documentation
- Conduct cross-browser and device testing
- Implement usage analytics

## Implementation Details

### URN Model Implementation

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from pathlib import Path

class URN(BaseModel):
    """
    Model for Canonical Text Services URNs.

    Example: urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1-1.7
    """
    value: str
    urn_namespace: Optional[str] = None
    cts_namespace: Optional[str] = None
    text_group: Optional[str] = None
    work: Optional[str] = None
    version: Optional[str] = None
    reference: Optional[str] = None

    class Config:
        """Configure model behavior."""
        validate_assignment = True

    @validator('value')
    def validate_urn(cls, v: str) -> str:
        """Validate the URN string format."""
        if not v.startswith("urn:cts:"):
            raise ValueError(f"Invalid CTS URN format: {v}")
        return v

    def __init__(self, **data: Any) -> None:
        """Initialize and parse the URN components."""
        super().__init__(**data)
        self.parse()

    def parse(self) -> None:
        """Parse the URN string into components."""
        urn = self.value.split('#')[0]
        parts = urn.split(':')

        if len(parts) >= 3:
            self.urn_namespace = parts[0]
            self.cts_namespace = parts[1]

        if len(parts) >= 4:
            self.cts_namespace = parts[2]

            # Handle possible reference part
            id_ref = parts[3].split(':')
            identifier = id_ref[0]

            if len(id_ref) > 1:
                self.reference = id_ref[1]

            # Parse identifier
            id_parts = identifier.split('.')
            if len(id_parts) >= 1:
                self.text_group = id_parts[0]
            if len(id_parts) >= 2:
                self.work = id_parts[1]
            if len(id_parts) >= 3:
                self.version = id_parts[2]

    def up_to(self, level: str) -> str:
        """
        Return URN up to specified level.

        Args:
            level: One of 'urn_namespace', 'cts_namespace', 'text_group',
                  'work', 'version', 'reference'

        Returns:
            String URN truncated at specified level
        """
        if level not in ['urn_namespace', 'cts_namespace', 'text_group',
                         'work', 'version', 'reference']:
            raise ValueError(f"Invalid URN level: {level}")

        parts = ["urn"]

        if level in ['urn_namespace', 'cts_namespace', 'text_group',
                     'work', 'version', 'reference'] and self.urn_namespace:
            parts.append(self.urn_namespace)

        if level in ['cts_namespace', 'text_group', 'work',
                    'version', 'reference'] and self.cts_namespace:
            parts.append(self.cts_namespace)

        if level in ['text_group', 'work', 'version', 'reference'] and self.text_group:
            parts.append(self.text_group)

        if level in ['work', 'version', 'reference'] and self.work:
            parts.append(f"{self.text_group}.{self.work}")

        if level in ['version', 'reference'] and self.version:
            parts.append(f"{self.text_group}.{self.work}.{self.version}")

        if level == 'reference' and self.reference:
            parts.append(self.reference)

        return ":".join(parts)

    def replace(self, **kwargs: Dict[str, Any]) -> 'URN':
        """
        Create a new URN with replaced components.

        Args:
            **kwargs: Components to replace, e.g., reference='1.1'

        Returns:
            New URN instance with replaced components
        """
        data = self.dict()
        data.update(kwargs)

        # Keep the original value, will be reconstructed in new instance
        new_urn = URN(value=self.value)

        for key, val in kwargs.items():
            setattr(new_urn, key, val)

        # Reconstruct the URN string from components
        parts = ["urn"]

        if new_urn.urn_namespace:
            parts.append(new_urn.urn_namespace)

        if new_urn.cts_namespace:
            parts.append(new_urn.cts_namespace)

        # Build identifier part
        id_parts = []
        if new_urn.text_group:
            id_parts.append(new_urn.text_group)
        if new_urn.work:
            id_parts.append(new_urn.work)
        if new_urn.version:
            id_parts.append(new_urn.version)

        if id_parts:
            parts.append(".".join(id_parts))

        if new_urn.reference:
            parts.append(new_urn.reference)

        new_urn.value = ":".join(parts)
        return new_urn

    def get_file_path(self, base_dir: str = "data") -> Path:
        """
        Get file path corresponding to this URN.

        Args:
            base_dir: Base directory for data files

        Returns:
            Path object for the XML file

        Raises:
            ValueError: If URN has insufficient components for path
        """
        if not self.text_group or not self.work or not self.version:
            raise ValueError(f"URN missing components needed for file path: {self.value}")

        return Path(base_dir) / self.text_group / self.work / f"{self.text_group}.{self.work}.{self.version}.xml"

    def get_adjacent_references(self, xml_processor: Any) -> Dict[str, Optional[str]]:
        """
        Get previous and next references relative to current.

        Args:
            xml_processor: XMLProcessorService to use for reference lookup

        Returns:
            Dictionary with 'prev' and 'next' references
        """
        xml_root = xml_processor.load_xml(self)
        return xml_processor.get_adjacent_references(xml_root, self.reference)
```

### XMLProcessorService Enhancements

```python
class XMLProcessorService:
    """Service for processing TEI XML files with reference handling."""

    def __init__(self, data_path: str = "data"):
        """Initialize the XML processor service."""
        self.data_path = Path(data_path)
        self.namespaces = {
            "tei": "http://www.tei-c.org/ns/1.0",
            "xml": "http://www.w3.org/XML/1998/namespace"
        }

    def resolve_urn_to_file_path(self, urn_obj: URN) -> Path:
        """Resolve URN to file path."""
        return urn_obj.get_file_path(self.data_path)

    def load_xml(self, urn_obj: URN) -> ET._Element:
        """Load XML file based on URN."""
        filepath = self.resolve_urn_to_file_path(urn_obj)
        if not filepath.exists():
            raise FileNotFoundError(f"XML file not found: {filepath}")
        return ET.parse(str(filepath)).getroot()

    def extract_references(self, element: ET._Element, parent_ref: str = "") -> Dict[str, ET._Element]:
        """
        Extract hierarchical references from TEI XML elements.

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
        for child in element.xpath(".//tei:div[@type='textpart'] | .//tei:l", namespaces=self.namespaces):
            child_refs = self.extract_references(child, ref)
            references.update(child_refs)

        return references

    def get_passage_by_reference(self, xml_root: ET._Element, reference: str) -> Optional[ET._Element]:
        """
        Retrieve a specific passage by its reference.

        Args:
            xml_root: Root XML element
            reference: Reference string (e.g., "1.1.5")

        Returns:
            XML element matching the reference or None if not found
        """
        references = self.extract_references(xml_root)
        return references.get(reference)

    def get_adjacent_references(self, xml_root: ET._Element, current_ref: str) -> Dict[str, Optional[str]]:
        """
        Get previous and next references relative to current reference.

        Args:
            xml_root: Root XML element
            current_ref: Current reference string

        Returns:
            Dictionary with 'prev' and 'next' references
        """
        references = list(self.extract_references(xml_root).keys())
        references.sort(key=lambda x: [int(n) if n.isdigit() else n for n in x.split('.')])

        try:
            idx = references.index(current_ref)
            prev_ref = references[idx - 1] if idx > 0 else None
            next_ref = references[idx + 1] if idx < len(references) - 1 else None
            return {"prev": prev_ref, "next": next_ref}
        except ValueError:
            return {"prev": None, "next": None}

    def tokenize_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into tokens (words and punctuation).

        Args:
            text: Text to tokenize

        Returns:
            List of token dictionaries with type, text, and index
        """
        import re

        if not text or text.strip() == '':
            return []

        tokens = []
        words = text.split()

        for i, word in enumerate(words):
            # Extract punctuation from the end of words
            match = re.match(r'(\w+)([,.;:!?]*), word)
            if match:
                word_text, punct = match.groups()
                tokens.append({
                    'type': 'word',
                    'text': word_text,
                    'index': i + 1
                })

                if punct:
                    tokens.append({
                        'type': 'punct',
                        'text': punct
                    })
            else:
                tokens.append({
                    'type': 'word',
                    'text': word,
                    'index': i + 1
                })

        return tokens

    def transform_to_html(self, xml_root: ET._Element, target_ref: Optional[str] = None) -> str:
        """
        Transform XML to HTML with reference attributes.

        Args:
            xml_root: Root XML element
            target_ref: Optional specific reference to display

        Returns:
            HTML string with reference attributes
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
            elements = xml_root.xpath("//tei:div[@type='textpart' and not(parent::tei:div[@type='textpart'])] | //tei:l[not(parent::tei:div[@type='textpart'])]", namespaces=self.namespaces)

        html = []

        for element in elements:
            # Build reference for this element
            refs = []
            for ancestor in element.xpath("ancestor-or-self::tei:div[@type='textpart']", namespaces=self.namespaces):
                n_attr = ancestor.get("n")
                if n_attr:
                    refs.append(n_attr)

            ref = ".".join(refs)

            # Create HTML with data attributes
            html.append(f'<div class="text-part" data-reference="{ref}">')

            # Add section number as clickable element
            section_num = element.get("n", "")
            if section_num:
                html.append(f'<div class="section-num"><a href="#ref={ref}">{section_num}</a></div>')

            # Add content
            html.append('<div class="content">')

            # Process text content
            for text_node in element.xpath(".//text()", namespaces=self.namespaces):
                tokens = self.tokenize_text(text_node)
                for token in tokens:
                    if token['type'] == 'word':
                        html.append(f'<span class="token" data-token="{token["text"]}" data-token-index="{token["index"]}">{token["text"]}</span>')
                    else:
                        html.append(f'<span class="punct">{token["text"]}</span>')

            # Add nested elements
            for child in element.xpath("./tei:div[@type='textpart'] | ./tei:l", namespaces=self.namespaces):
                child_html = self.transform_to_html(child, None)
                html.append(child_html)

            # Close elements
            html.append('</div></div>')

        return ''.join(html)
