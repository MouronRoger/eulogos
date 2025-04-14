# Implementing Reference Handling for Ancient Texts in Eulogos

This document outlines how to implement a system for extracting and displaying references from TEI XML texts in Eulogos, comparable to the functionality in Scaife Viewer but using Eulogos's technology stack.

## 1. XML Processing Service

```python
from lxml import etree
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import BaseModel

class XMLProcessorService:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    
    def resolve_urn_to_file_path(self, urn_obj: 'URN') -> Path:
        """
        Convert a CTS URN to a file path.
        
        Example: 
        urn:cts:greekLit:tlg0012.tlg001.perseus-grc2 
        -> data/tlg0012/tlg001/perseus-grc2.xml
        """
        path = Path(self.data_path)
        if urn_obj.text_group:
            path = path / urn_obj.text_group
            if urn_obj.work:
                path = path / urn_obj.work
                if urn_obj.version:
                    return path / f"{urn_obj.version}.xml"
        raise ValueError(f"Could not resolve URN to file path: {urn_obj.value}")
    
    def load_xml(self, urn_obj: 'URN') -> etree._Element:
        """Load XML file based on URN."""
        filepath = self.resolve_urn_to_file_path(urn_obj)
        if not filepath.exists():
            raise FileNotFoundError(f"XML file not found: {filepath}")
        return etree.parse(str(filepath)).getroot()
    
    def extract_references(self, element: etree._Element, parent_ref: str = "") -> Dict[str, etree._Element]:
        """Extract hierarchical references from TEI XML elements."""
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
        """Retrieve a specific passage by its reference."""
        references = self.extract_references(xml_root)
        return references.get(reference)
    
    def get_adjacent_references(self, xml_root: etree._Element, current_ref: str) -> Dict[str, Optional[str]]:
        """Get previous and next references relative to the current one."""
        references = list(self.extract_references(xml_root).keys())
        try:
            idx = references.index(current_ref)
            prev_ref = references[idx - 1] if idx > 0 else None
            next_ref = references[idx + 1] if idx < len(references) - 1 else None
            return {"prev": prev_ref, "next": next_ref}
        except ValueError:
            return {"prev": None, "next": None}
    
    def _build_reference(self, element: etree._Element) -> str:
        """Build hierarchical reference from element and its ancestors."""
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
        """Split text into tokens (words and punctuation)."""
        import re
        
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
        """Process a text node, adding markup for words and tokens."""
        tokens = self.tokenize_text(text_node)
        html = []
        
        for token in tokens:
            if token['type'] == 'word':
                html.append(f'<span class="token" data-token="{token["text"]}" data-token-index="{token["index"]}">{token["text"]}</span>')
            elif token['type'] == 'punct':
                html.append(f'<span class="punct">{token["text"]}</span>')
        
        return ''.join(html)
    
    def transform_to_html(self, xml_root: etree._Element, target_ref: Optional[str] = None) -> str:
        """Transform XML to HTML with reference attributes."""
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
                html.append(f'<div class="section-num"><a href="/reader/{ref}">{section_num}</a></div>')
            
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

## 2. CTS URN Handling

```python
from pydantic import BaseModel
from typing import Optional

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
    
    def __init__(self, value: str, **kwargs):
        super().__init__(value=value, **kwargs)
        self.parse()
        
    def parse(self):
        """Parse the URN into its components."""
        urn = self.value.split('#')[0]
        bits = urn.split(':')[1:]
        if len(bits) > 2:
            self.urn_namespace = bits[0]
            self.cts_namespace = bits[1]
            work_identifier = bits[2]
            if len(bits) > 3:
                self.reference = bits[3]
                
            # Parse work identifier
            work_parts = work_identifier.split('.')
            if len(work_parts) >= 1:
                self.text_group = work_parts[0]
            if len(work_parts) >= 2:
                self.work = work_parts[1]
            if len(work_parts) >= 3:
                self.version = work_parts[2]
    
    def up_to(self, segment: str) -> str:
        """
        Return the URN up to a specific segment.
        
        Example: urn_obj.up_to("version") for urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:1.1
        Returns: urn:cts:greekLit:tlg0012.tlg001.perseus-grc2
        """
        segments = ["urn", self.urn_namespace, self.cts_namespace]
        
        if segment in ["text_group", "work", "version", "reference"] and self.text_group:
            segments.append(self.text_group)
            
        if segment in ["work", "version", "reference"] and self.work:
            segments.append(f"{self.text_group}.{self.work}")
            
        if segment in ["version", "reference"] and self.version:
            segments.append(f"{self.text_group}.{self.work}.{self.version}")
            
        if segment == "reference" and self.reference:
            segments.append(self.reference)
            
        return ":".join(segments)
    
    def replace(self, **kwargs) -> 'URN':
        """
        Return a new URN with replaced components.
        
        Example: urn_obj.replace(reference="1.2") 
        Creates a new URN with the same components but a different reference.
        """
        value = self.value
        new_obj = URN(value)
        
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
            new_obj.urn_namespace or self.urn_namespace,
            new_obj.cts_namespace or self.cts_namespace,
            work_part
        ]
        
        new_value = ":".join(urn_parts)
        
        if new_obj.reference:
            new_value += f":{new_obj.reference}"
            
        new_obj.value = new_value
        return new_obj
    
    def __str__(self):
        return self.value
```

## 3. FastAPI Endpoints

```python
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from .models import URN
from .services import XMLProcessorService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_xml_processor():
    """Dependency for XMLProcessorService."""
    return XMLProcessorService(settings.DATA_PATH)

@router.get("/reader/{urn}", response_class=HTMLResponse)
async def read_passage(request: Request, urn: str):
    """Render a passage for reading."""
    try:
        # Parse URN
        urn_obj = URN(urn)
        
        # Get XML processor
        xml_processor = get_xml_processor()
        
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
async def get_passage_content(urn: str):
    """API endpoint for HTMX to load passage content dynamically."""
    try:
        # Parse URN
        urn_obj = URN(urn)
        
        # Get XML processor
        xml_processor = get_xml_processor()
        
        # Load XML based on URN
        xml_root = xml_processor.load_xml(urn_obj)
        
        # Transform to HTML
        html_content = xml_processor.transform_to_html(xml_root, urn_obj.reference)
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/api/word-info/")
async def get_word_info(word: str, lang: str):
    """Get morphological information about a word."""
    # This would integrate with your morphology service
    # For now, return dummy data
    return {
        "word": word,
        "language": lang,
        "forms": [
            {"form": word, "lemma": word, "pos": "noun", "properties": "nominative singular"}
        ]
    }
```

## 4. HTML Templates

### Base Reader Template (reader.html)

```html
{% extends "base.html" %}

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
                x-text="textMode === 'normal' ? 'Normal Mode' : 'Highlight Mode'"
                class="btn btn-sm"
                :class="textMode === 'normal' ? 'btn-secondary' : 'btn-primary'">
        </button>
    </div>
    
    <!-- Reference navigation -->
    <div class="reference-nav">
        {% if prev_reference %}
            <a href="/reader/{{ urn_base }}:{{ prev_reference }}" class="prev-ref">
                ← Previous
            </a>
        {% endif %}
        <span class="current-ref">{{ urn_obj.reference }}</span>
        {% if next_reference %}
            <a href="/reader/{{ urn_base }}:{{ next_reference }}" class="next-ref">
                Next →
            </a>
        {% endif %}
    </div>
    
    <!-- Text content -->
    <div class="text-content"
         :class="{ 'mode-highlight': textMode === 'highlight' }"
         hx-trigger="revealed"
         hx-get="/api/reader/{{ urn }}/content"
         hx-swap="innerHTML">
        {{ html_content|safe }}
    </div>
    
    <!-- Token information (when selected) -->
    <div class="token-info" x-show="selectedToken" x-cloak>
        <h4>Selected Word</h4>
        <div x-text="selectedToken"></div>
        
        <div hx-get="/api/word-info/" 
             hx-trigger="selectedToken changed"
             hx-vals='{"word": selectedToken, "lang": "{{ language }}"}'
             hx-target="this">
            Loading word information...
        </div>
    </div>
</div>

<!-- Custom JavaScript to handle text interactions -->
<script>
document.addEventListener('alpine:init', () => {
    // Add event delegation for text parts
    document.querySelector('.text-content').addEventListener('click', (e) => {
        const token = e.target.closest('.token');
        if (token) {
            const alpineScope = Alpine.scope(e.target);
            if (alpineScope && alpineScope.textMode === 'highlight') {
                alpineScope.selectedToken = token.dataset.token;
                
                // Remove previous highlights
                document.querySelectorAll('.token-highlighted').forEach(el => {
                    el.classList.remove('token-highlighted');
                });
                
                // Add highlight to this token
                token.classList.add('token-highlighted');
                
                // Prevent default navigation if in highlight mode
                e.preventDefault();
            }
        }
    });
});
</script>
{% endblock %}
```

## 5. CSS Styling

```css
/* static/css/reader.css */

/* Reader Container */
.reader-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    font-family: 'Noto Serif', serif;
}

/* Controls */
.reader-controls {
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Reference Navigation */
.reference-nav {
    display: flex;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    padding: 0.5rem;
    background-color: #f3f4f6; /* Gray 100 */
    border-radius: 0.25rem;
}

.reference-nav .current-ref {
    font-weight: bold;
}

.reference-nav a {
    color: #4b5563; /* Gray 600 */
    text-decoration: none;
}

.reference-nav a:hover {
    color: #1f2937; /* Gray 800 */
    text-decoration: underline;
}

/* Text Parts */
.text-part {
    position: relative;
    display: flex;
    margin-bottom: 0.5rem;
    line-height: 1.5;
}

.text-part .section-num {
    min-width: 2.5rem;
    text-align: right;
    padding-right: 0.75rem;
    font-weight: bold;
    color: #6b7280; /* Gray 500 */
}

.text-part .section-num a {
    color: inherit;
    text-decoration: none;
}

.text-part .section-num a:hover {
    color: #1f2937; /* Gray 800 */
}

.text-part .content {
    flex: 1;
}

/* Tokens */
.token {
    display: inline-block;
    padding: 0 1px;
}

.punct {
    display: inline-block;
    margin-left: -1px;
}

/* Highlighting mode */
.mode-highlight .token:hover {
    background-color: rgba(254, 240, 138, 0.5); /* Light yellow */
    cursor: pointer;
    border-radius: 2px;
}

.token-highlighted {
    background-color: rgba(254, 240, 138, 1); /* Yellow */
    border-radius: 2px;
}

/* Token Info Panel */
.token-info {
    margin-top: 1.5rem;
    padding: 1rem;
    border-top: 1px solid #e5e7eb; /* Gray 200 */
}

.token-info h4 {
    margin-top: 0;
    color: #4b5563; /* Gray 600 */
}

/* Page breaks and milestones */
.pb, .milestone {
    text-align: center;
    font-style: italic;
    color: #9ca3af; /* Gray 400 */
    margin: 0.5rem 0;
    font-size: 0.875rem;
}

.pb:before {
    content: 'p. ';
}
```

## 6. Main Application Setup

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routers import reader

app = FastAPI(title="Eulogos", description="Ancient Greek text browser")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(reader.router)

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})
```

## Integration with Eulogos

This implementation provides a solid foundation for handling references in ancient texts within the Eulogos application. Key features include:

1. **XML Processing** - Parse TEI XML and extract hierarchical references
2. **CTS URN Support** - Handle Canonical Text Services URNs for precise text identification
3. **FastAPI Endpoints** - Serve passages with efficient API endpoints
4. **HTMX Integration** - Dynamic content loading without full page reloads
5. **Alpine.js Interactivity** - Client-side interaction handling

The implementation is designed to work within Eulogos's existing technology stack, providing functionality comparable to Scaife Viewer but adapted to your architectural choices. It handles references in a sophisticated manner, supporting hierarchical structures, navigation, and token-level interaction.

To integrate this into your existing Eulogos project:

1. Add the XMLProcessorService to your services module
2. Add the URN model to your models module
3. Add the reader router to your API endpoints
4. Create the templates and CSS for the reader interface
5. Connect to any existing morphology or lexical services you have

This implementation should provide a solid foundation that you can extend and customize to meet your specific requirements.
