# Implementing XML Reference Handling for Eulogos

This document outlines the implementation of reference handling capabilities for the Eulogos project, focused on extracting and displaying hierarchical references from TEI XML texts, similar to what's available in Scaife Viewer but utilizing the Eulogos technology stack.

## 1. Enhanced XMLProcessorService

```python
# app/services/xml_processor_service.py

from lxml import etree
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

class XMLProcessorService:
    """Service for processing TEI XML files with enhanced reference handling."""
    
    def __init__(self, data_path: str):
        """Initialize the XML processor.
        
        Args:
            data_path: Base path to TEI XML files
        """
        self.data_path = Path(data_path)
        self.namespaces = {
            "tei": "http://www.tei-c.org/ns/1.0",
            "xml": "http://www.w3.org/XML/1998/namespace"
        }
    
    def resolve_urn_to_file_path(self, urn_obj: 'URN') -> Path:
        """Convert a CTS URN to a file path.
        
        Args:
            urn_obj: URN object to resolve
            
        Returns:
            Path to the XML file
            
        Raises:
            ValueError: If the URN cannot be resolved to a file path
        """
        path = self.data_path
        
        if urn_obj.namespace:
            path = path / urn_obj.namespace
            
            if urn_obj.text_group:
                path = path / urn_obj.text_group
                
                if urn_obj.work:
                    path = path / urn_obj.work
                    
                    if urn_obj.version:
                        return path / f"{urn_obj.text_group}.{urn_obj.work}.{urn_obj.version}.xml"
        
        raise ValueError(f"Could not resolve URN to file path: {urn_obj.value}")
    
    def load_xml(self, urn_obj: 'URN') -> etree._Element:
        """Load XML file based on URN.
        
        Args:
            urn_obj: URN object to load
            
        Returns:
            Root element of the XML document
            
        Raises:
            FileNotFoundError: If the XML file doesn't exist
        """
        filepath = self.resolve_urn_to_file_path(urn_obj)
        if not filepath.exists():
            raise FileNotFoundError(f"XML file not found: {filepath}")
        
        return etree.parse(str(filepath)).getroot()
    
    def extract_references(self, element: etree._Element, parent_ref: str = "") -> Dict[str, etree._Element]:
        """Extract hierarchical references from TEI XML elements.
        
        Args:
            element: XML element to process
            parent_ref: Parent reference string
            
        Returns:
            Dictionary mapping reference strings to XML elements
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
    
    def get_passage_by_reference(self, xml_root: etree._Element, reference: str) -> Optional[etree._Element]:
        """Retrieve a specific passage by its reference.
        
        Args:
            xml_root: Root XML element
            reference: Reference string (e.g., "1.1.5")
            
        Returns:
            XML element for the passage, or None if not found
        """
        references = self.extract_references(xml_root)
        return references.get(reference)
    
    def get_adjacent_references(self, xml_root: etree._Element, current_ref: str) -> Dict[str, Optional[str]]:
        """Get previous and next references relative to the current one.
        
        Args:
            xml_root: Root XML element
            current_ref: Current reference string
            
        Returns:
            Dictionary with "prev" and "next" keys containing reference strings
        """
        references = list(self.extract_references(xml_root).keys())
        try:
            idx = references.index(current_ref)
            prev_ref = references[idx - 1] if idx > 0 else None
            next_ref = references[idx + 1] if idx < len(references) - 1 else None
            return {"prev": prev_ref, "next": next_ref}
        except ValueError:
            return {"prev": None, "next": None}
    
    def _build_reference(self, element: etree._Element) -> str:
        """Build hierarchical reference from element and its ancestors.
        
        Args:
            element: XML element
            
        Returns:
            Reference string (e.g., "1.1.5")
        """
        refs = []
        
        # Add current element's n attribute if present
        if "n" in element.attrib:
            refs.append(element.get("n"))
            
        # Add ancestor references
        for ancestor in element.xpath("ancestor::tei:div[@type='textpart']", namespaces=self.namespaces):
            if "n" in ancestor.attrib:
                refs.insert(0, ancestor.get("n"))
                
        return ".".join(refs)
    
    def tokenize_text(self, text: str) -> List[Dict]:
        """Split text into tokens (words and punctuation).
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of token dictionaries
        """
        if not text or text.strip() == '':
            return []
        
        tokens = []
        words = text.split()
        
        for i, word in enumerate(words):
            # Extract punctuation from the end of words
            match = re.match(r'(\w+)([,.;:!?]*)$', word)
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
    
    def process_text_node(self, text_node: etree._ElementUnicodeResult) -> str:
        """Process a text node, adding markup for words and tokens.
        
        Args:
            text_node: Text node to process
            
        Returns:
            HTML string with token markup
        """
        tokens = self.tokenize_text(text_node)
        html = []
        
        for token in tokens:
            if token['type'] == 'word':
                html.append(f'<span class="token" data-token="{token["text"]}" data-token-index="{token["index"]}">{token["text"]}</span>')
            elif token['type'] == 'punct':
                html.append(f'<span class="punct">{token["text"]}</span>')
        
        return ''.join(html)
    
    def transform_to_html(self, xml_root: etree._Element, target_ref: Optional[str] = None) -> str:
        """Transform XML to HTML with reference attributes.
        
        Args:
            xml_root: Root XML element
            target_ref: Optional target reference to focus on
            
        Returns:
            HTML string
        
        Raises:
            ValueError: If the target reference is not found
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
            ref = self._build_reference(element)
            
            # Create HTML with data attributes
            html.append(f'<div class="text-part" data-reference="{ref}">')
            
            # Add section number as clickable element
            section_num = element.get("n", "")
            if section_num:
                html.append(f'<div class="section-num"><a href="#/reader/{ref}">{section_num}</a></div>')
            
            # Add content
            html.append('<div class="content">')
            
            # Process text content
            for node in element.xpath(".//text()", namespaces=self.namespaces):
                if node.is_text:
                    html.append(self.process_text_node(node))
            
            # Add nested elements
            for child in element.xpath("./tei:div[@type='textpart'] | ./tei:l", namespaces=self.namespaces):
                child_html = self.transform_to_html(child, None)
                html.append(child_html)
            
            # Close elements
            html.append('</div></div>')
            
        return ''.join(html)
```

## 2. CTS URN Model

```python
# app/models/urn.py

from pydantic import BaseModel, Field
from typing import Optional

class URN(BaseModel):
    """Model for Canonical Text Services URNs."""
    
    value: str
    urn_namespace: Optional[str] = Field(None, description="Usually 'cts'")
    namespace: Optional[str] = Field(None, description="e.g., 'greekLit'")
    text_group: Optional[str] = Field(None, description="e.g., 'tlg0012'")
    work: Optional[str] = Field(None, description="e.g., 'tlg001'")
    version: Optional[str] = Field(None, description="e.g., 'perseus-grc2'")
    reference: Optional[str] = Field(None, description="e.g., '1.1-1.7'")
    
    def __init__(self, value: str, **kwargs):
        """Initialize and parse a URN.
        
        Args:
            value: The URN string
            **kwargs: Additional fields
        """
        super().__init__(value=value, **kwargs)
        self.parse()
        
    def parse(self):
        """Parse the URN into its components."""
        urn = self.value.split('#')[0]
        bits = urn.split(':')
        
        if len(bits) < 2:
            return
            
        self.urn_namespace = bits[1] if len(bits) > 1 else None
        self.namespace = bits[2] if len(bits) > 2 else None
        
        if len(bits) > 3:
            work_identifier = bits[3]
            
            # Extract reference if present
            if ':' in work_identifier:
                work_part, self.reference = work_identifier.split(':', 1)
            else:
                work_part, self.reference = work_identifier, None
                
            # Parse work identifier
            work_parts = work_part.split('.')
            if len(work_parts) >= 1:
                self.text_group = work_parts[0]
            if len(work_parts) >= 2:
                self.work = work_parts[1]
            if len(work_parts) >= 3:
                self.version = work_parts[2]
    
    def up_to(self, segment: str) -> str:
        """Return the URN up to a specific segment.
        
        Args:
            segment: The segment to include ('text_group', 'work', 'version', 'reference')
            
        Returns:
            URN string up to the specified segment
        """
        segments = ["urn", self.urn_namespace, self.namespace]
        
        if self.text_group and segment in ["text_group", "work", "version", "reference"]:
            work_parts = [self.text_group]
            
            if self.work and segment in ["work", "version", "reference"]:
                work_parts.append(self.work)
                
                if self.version and segment in ["version", "reference"]:
                    work_parts.append(self.version)
            
            segments.append(".".join(work_parts))
            
            if segment == "reference" and self.reference:
                segments.append(self.reference)
            
        return ":".join(filter(None, segments))
    
    def replace(self, **kwargs) -> 'URN':
        """Create a new URN with replaced components.
        
        Args:
            **kwargs: Components to replace
            
        Returns:
            A new URN object
        """
        new_obj = URN(self.value)
        
        for key, val in kwargs.items():
            setattr(new_obj, key, val)
            
        # Rebuild the URN value
        work_part = ""
        if new_obj.text_group:
            work_part = new_obj.text_group
            if new_obj.work:
                work_part += f".{new_obj.work}"
                if new_obj.version:
                    work_part += f".{new_obj.version}"
                    
        urn_parts = [
            "urn",
            new_obj.urn_namespace,
            new_obj.namespace,
            work_part
        ]
        
        new_value = ":".join(filter(None, urn_parts))
        
        if new_obj.reference:
            new_value += f":{new_obj.reference}"
            
        new_obj.value = new_value
        return new_obj
    
    def __str__(self) -> str:
        """String representation of the URN.
        
        Returns:
            The URN string
        """
        return self.value
```

## 3. FastAPI Endpoints

```python
# app/routers/reader.py

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.config import settings
from app.models.urn import URN
from app.services.xml_processor_service import XMLProcessorService

router = APIRouter(tags=["reader"])
templates = Jinja2Templates(directory="app/templates")

def get_xml_processor():
    """Dependency for XMLProcessorService."""
    return XMLProcessorService(settings.DATA_PATH)

@router.get("/reader/{urn}", response_class=HTMLResponse)
async def read_passage(
    request: Request, 
    urn: str,
    xml_processor: XMLProcessorService = Depends(get_xml_processor)
):
    """Render a passage for reading.
    
    Args:
        request: FastAPI request object
        urn: CTS URN of the passage
        xml_processor: XMLProcessorService dependency
        
    Returns:
        HTML Template response
        
    Raises:
        HTTPException: If the passage is not found
    """
    try:
        # Parse URN
        urn_obj = URN(urn)
        
        # Load XML based on URN
        xml_root = xml_processor.load_xml(urn_obj)
        
        # Get adjacent references
        adjacent_refs = {}
        if urn_obj.reference:
            adjacent_refs = xml_processor.get_adjacent_references(xml_root, urn_obj.reference)
        
        # Transform to HTML
        html_content = xml_processor.transform_to_html(xml_root, urn_obj.reference)
        
        # Calculate base URN (without reference)
        urn_base = urn_obj.up_to("version")
        
        # Get language from metadata
        language = xml_root.xpath("string(//tei:text/@xml:lang)", namespaces=xml_processor.namespaces)
        
        # Return template with HTML content
        return templates.TemplateResponse(
            "reader.html", 
            {
                "request": request,
                "urn": urn,
                "urn_obj": urn_obj,
                "urn_base": urn_base,
                "html_content": html_content,
                "language": language,
                "prev_reference": adjacent_refs.get("prev"),
                "next_reference": adjacent_refs.get("next")
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/api/reader/{urn}/content", response_class=HTMLResponse)
async def get_passage_content(
    urn: str,
    xml_processor: XMLProcessorService = Depends(get_xml_processor)
):
    """API endpoint for HTMX to load passage content dynamically.
    
    Args:
        urn: CTS URN of the passage
        xml_processor: XMLProcessorService dependency
        
    Returns:
        HTML content of the passage
        
    Raises:
        HTTPException: If the passage is not found
    """
    try:
        # Parse URN
        urn_obj = URN(urn)
        
        # Load XML based on URN
        xml_root = xml_processor.load_xml(urn_obj)
        
        # Transform to HTML
        html_content = xml_processor.transform_to_html(xml_root, urn_obj.reference)
        
        return html_content
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/api/word-info/")
async def get_word_info(word: str, lang: str = Query("grc")):
    """Get morphological information about a word.
    
    Args:
        word: The word to analyze
        lang: Language code (default: "grc" for Greek)
        
    Returns:
        JSON response with word information
    """
    # This would integrate with your morphology service
    # For now, return dummy data
    return {
        "word": word,
        "language": lang,
        "forms": [
            {"form": word, "lemma": word, "pos": "noun", "properties": "nominative singular"}
        ]
    }

@router.get("/api/references/{urn}/tree")
async def get_reference_tree(
    urn: str,
    xml_processor: XMLProcessorService = Depends(get_xml_processor)
):
    """Get the reference tree for a text.
    
    Args:
        urn: CTS URN of the text
        xml_processor: XMLProcessorService dependency
        
    Returns:
        JSON response with reference tree
        
    Raises:
        HTTPException: If the text is not found
    """
    try:
        # Parse URN
        urn_obj = URN(urn)
        
        # Load XML based on URN
        xml_root = xml_processor.load_xml(urn_obj)
        
        # Extract references
        references = xml_processor.extract_references(xml_root)
        
        # Build tree from flat references
        tree = {}
        
        for ref in references.keys():
            parts = ref.split('.')
            current = tree
            
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"children": {}, "ref": '.'.join(parts[:i+1])}
                
                current = current[part]["children"]
        
        return tree
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
```

## 4. HTML Templates

### Reader Template (app/templates/reader.html)

```html
{% extends "base.html" %}

{% block title %}{{ urn_obj.work }} | Eulogos Reader{% endblock %}

{% block content %}
<div class="reader-container" 
     x-data="{ 
       textMode: 'normal', 
       selectedToken: null,
       toggleTextMode() { 
         this.textMode = this.textMode === 'normal' ? 'highlight' : 'normal';
         this.selectedToken = null;
       },
       selectToken(token) {
         if (this.textMode === 'highlight') {
           this.selectedToken = token;
         }
       }
     }">
    
    <!-- Controls -->
    <div class="reader-controls">
        <button @click="toggleTextMode()" 
                x-text="textMode === 'normal' ? 'Enable Word Analysis' : 'Normal Reading'"
                class="px-3 py-1 rounded text-white"
                :class="textMode === 'normal' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-green-600 hover:bg-green-700'">
        </button>
        
        <span class="text-gray-500 text-sm ml-2" x-show="textMode === 'highlight'">
            Click on words to analyze them
        </span>
    </div>
    
    <!-- Reference navigation -->
    <div class="reference-nav mt-4 mb-4 flex justify-between items-center p-2 bg-gray-100 rounded">
        {% if prev_reference %}
            <a href="/reader/{{ urn_base }}:{{ prev_reference }}" class="text-blue-600 hover:text-blue-800">
                ← Previous ({{ prev_reference }})
            </a>
        {% else %}
            <span class="text-gray-400">← Previous</span>
        {% endif %}
        
        <span class="font-medium">{{ urn_obj.reference }}</span>
        
        {% if next_reference %}
            <a href="/reader/{{ urn_base }}:{{ next_reference }}" class="text-blue-600 hover:text-blue-800">
                Next ({{ next_reference }}) →
            </a>
        {% else %}
            <span class="text-gray-400">Next →</span>
        {% endif %}
    </div>
    
    <!-- Text content -->
    <div class="text-content p-4 bg-white rounded shadow"
         :class="{ 'mode-highlight': textMode === 'highlight' }"
         hx-trigger="revealed"
         hx-get="/api/reader/{{ urn }}/content"
         hx-swap="innerHTML">
        {{ html_content|safe }}
    </div>
    
    <!-- Token information (when selected) -->
    <div class="token-info mt-4 p-4 bg-white rounded shadow" x-show="selectedToken" x-cloak>
        <h4 class="text-lg font-medium mb-2">Word Analysis</h4>
        <p class="mb-2">Selected word: <span class="font-medium" x-text="selectedToken"></span></p>
        
        <div hx-get="/api/word-info/" 
             hx-trigger="load, selectedToken changed"
             hx-vals='{"word": selectedToken, "lang": "{{ language }}"}'
             hx-target="this">
            <div class="animate-pulse">
                <div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div class="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            </div>
        </div>
    </div>
</div>

<!-- Custom JavaScript to handle text interactions -->
<script>
document.addEventListener('alpine:init', () => {
    // Add event delegation for text parts
    document.addEventListener('click', (e) => {
        const token = e.target.closest('.token');
        if (token) {
            const alpineEl = document.querySelector('.reader-container');
            if (alpineEl && alpineEl.__x) {
                const scope = alpineEl.__x.getUnobservedData();
                
                if (scope.textMode === 'highlight') {
                    scope.selectedToken = token.dataset.token;
                    
                    // Remove previous highlights
                    document.querySelectorAll('.token-highlighted').forEach(el => {
                        el.classList.remove('token-highlighted');
                    });
                    
                    // Add highlight to this token
                    token.classList.add('token-highlighted');
                    
                    // Let Alpine know we changed data
                    alpineEl.__x.updateElement(alpineEl);
                    
                    // Prevent default navigation if in highlight mode
                    e.preventDefault();
                }
            }
        }
    });
});
</script>
{% endblock %}
```

## 5. CSS Styling

```css
/* app/static/css/reader.css */

/* Reader Container */
.reader-container {
    max-width: 900px;
    margin: 0 auto;
    font-family: 'Noto Serif', serif;
}

/* Reader Controls */
.reader-controls {
    display: flex;
    align-items: center;
    margin-bottom: 1rem;
}

/* Text Parts */
.text-part {
    display: flex;
    margin-bottom: 0.75rem;
}

.text-part .section-num {
    flex: 0 0 2rem;
    font-weight: bold;
    color: #6b7280; /* Gray 500 */
    text-align: right;
    padding-right: 0.75rem;
}

.text-part .section-num a {
    color: inherit;
    text-decoration: none;
}

.text-part .section-num a:hover {
    color: #1d4ed8; /* Blue 700 */
}

.text-part .content {
    flex: 1;
    line-height: 1.7;
}

/* Token styling */
.token {
    display: inline-block;
    padding: 0 1px;
}

.mode-highlight .token {
    cursor: pointer;
}

.mode-highlight .token:hover {
    background-color: rgba(254, 243, 199, 0.5); /* Amber 100 with opacity */
    border-radius: 2px;
}

.token-highlighted {
    background-color: rgba(254, 243, 199, 0.9); /* Amber 100 with opacity */
    border-radius: 2px;
}

.punct {
    display: inline-block;
    margin-left: -1px;
}

/* Token info panel */
.token-info {
    border-top: 1px solid #e5e7eb; /* Gray 200 */
}
```

## 6. Integration with Eulogos

To integrate this reference handling system with the Eulogos project:

### 1. Update app/main.py

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import reader, browse  # Import the reader router

app = FastAPI(title="Eulogos", description="Ancient Greek texts browser")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(browse.router)
app.include_router(reader.router)  # Add the reader router

# Setup templates
templates = Jinja2Templates(directory="app/templates")
```

### 2. Add CSS to base template (app/templates/base.html)

```html
<head>
    <!-- Other head elements -->
    <link href="/static/css/reader.css" rel="stylesheet">
</head>
```

### 3. Update URN handling in app/utils/urn.py

Enhance the existing CtsUrn utility to use the new URN model:

```python
from app.models.urn import URN

class CtsUrn:
    """Utility class for CTS URN parsing and manipulation."""
    
    @staticmethod
    def from_string(urn_string: str) -> URN:
        """Create a URN object from a string.
        
        Args:
            urn_string: The URN string
            
        Returns:
            A URN object
        """
        return URN(urn_string)
```

## 7. Key Benefits

This implementation:

1. **Enhances Navigation:** Provides precise navigation between referenced sections
2. **Supports Analysis:** Enables token-level interactions for word analysis
3. **Improves Citations:** Makes it easy to reference specific passages
4. **Preserves Context:** Shows the hierarchical context of references
5. **Integrates with Existing UI:** Works with the Text Reader component
6. **Uses Eulogos Tech Stack:** Built with HTMX, Alpine.js, and FastAPI

## 8. Future Enhancements

1. **Reference Sharing:** Add ability to share specific passage references via URL
2. **Advanced Navigation:** Implement a collapsible reference tree for easy browsing
3. **Parallel Text View:** Show original and translation side by side with aligned references
4. **Reference Search:** Allow searching within specific reference sections
5. **Export Citations:** Generate formatted citations for academic use
