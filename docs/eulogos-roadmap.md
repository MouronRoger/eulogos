# Eulogos Project Implementation Roadmap (Updated)

## 1. Project Overview

Eulogos is a web application for accessing, searching, and studying ancient Greek texts from the First 1000 Years Project. The system provides scholars, students, and enthusiasts with tools to browse texts by author, read works with specialized viewing options, search across the corpus, and import new texts from external sources.

## 2. Technology Stack

### 2.1 Backend
- **Python 3.9+**
- **FastAPI** - Modern API framework with automatic documentation
- **Pydantic** - Data validation and settings management
- **lxml** - Efficient XML processing
- **Jinja2** - Template engine for HTML generation

### 2.2 Frontend
- **HTMX** - For dynamic interactions without complex JavaScript
- **Alpine.js** - Minimal JavaScript framework for more complex UI needs
- **Tailwind CSS** - Utility-first CSS framework for styling

### 2.3 Data Storage
#### Initial Phase
- Unified JSON catalog combining author and text metadata
- TEI XML files organized by CTS URN structure
#### Future Extensions
- PostgreSQL for relational data
- Vector database for embeddings (e.g., Pinecone or Qdrant)

## 3. Data Model

### 3.1 Unified Catalog Structure

```json
{
  "statistics": {
    "nodeCount": 275030,
    "greekWords": 25580179,
    "latinWords": 5245040,
    "arabicwords": 6034,
    "authorCount": 1024,
    "textCount": 10248
  },
  "authors": {
    "tlg0007": {
      "name": "Plutarch",
      "century": 1,
      "type": "Platonist"
    },
    "tlg0012": {
      "name": "Homer",
      "century": -8,
      "type": "Poet"
    }
    // more authors...
  },
  "catalog": [
    {
      "urn": "urn:cts:greekLit:tlg0007.tlg136.perseus-grc2",
      "group_name": "Plutarch",
      "work_name": "De Stoicorum Repugnantiis",
      "language": "grc",
      "wordcount": 8750,
      "scaife": "https://scaife.perseus.org/...",
      "author_id": "tlg0007"
    }
    // more catalog entries...
  ]
}
```

### 3.2 Core Pydantic Models

```python
class Author(BaseModel):
    """Author model."""
    name: str
    century: int  # Negative for BCE, positive for CE
    type: str

class Text(BaseModel):
    """Text model with author reference."""
    urn: str
    group_name: str
    work_name: str
    language: str
    wordcount: int
    scaife: Optional[str] = None
    author_id: Optional[str] = None
    
    # Derived fields (not stored in JSON)
    namespace: Optional[str] = Field(None, exclude=True)
    textgroup: Optional[str] = Field(None, exclude=True)
    work_id: Optional[str] = Field(None, exclude=True)
    version: Optional[str] = Field(None, exclude=True)
    
    @validator('urn')
    def parse_urn(cls, v, values):
        """Extract URN components."""
        # Parse URN implementation...
        
class CatalogStatistics(BaseModel):
    """Statistics about the catalog."""
    nodeCount: int = 0
    greekWords: int = 0
    latinWords: int = 0
    arabicwords: int = 0
    authorCount: int = 0
    textCount: int = 0

class UnifiedCatalog(BaseModel):
    """Unified catalog model combining author and text data."""
    statistics: CatalogStatistics
    authors: Dict[str, Author]
    catalog: List[Text]
```

## 4. Revised Implementation Phases

### 4.1 Phase 0: Data Validation and Unification (New)
- Validate synchronization between catalog data and actual XML files
- Check URN to file path mappings
- Verify author references between catalogs
- Create unified catalog JSON from author-index.json and catalog-index.json
- Implement data validation tools for ongoing catalog maintenance

### 4.2 Phase 1: Core Text Browser (Initial MVP)
- Set up project structure and environment
- Implement Pydantic models for unified catalog
- Create CatalogService for accessing unified catalog data
- Implement URN utilities for CTS URN parsing and manipulation
- Create XMLProcessorService for parsing TEI XML files referenced by URN
- Build API endpoints for browsing authors and viewing texts
- Develop basic UI templates with HTMX and Tailwind
- Implement text reader with URN-based navigation
- Add basic import functionality for new texts

### 4.3 Phase 2: Enhanced Features and Text Management
- Implement sorting, filtering, and text search capabilities
- Enhance UI for exploring texts by language, century, author type
- Create improved text reader with customization options
- Add user preferences with client-side storage
- Implement basic text editing and correction capabilities
- Add export functionality in multiple formats
- Improve UI with responsive design and accessibility

### 4.4 Phase 3: Relational Database Integration
- Design PostgreSQL schema based on unified catalog structure
- Create SQLAlchemy ORM models with appropriate relationships
- Implement migration utilities to transfer from file-based to database storage
- Add database versioning and migration tools (Alembic)
- Refactor services to use database repositories
- Optimize database queries for performance
- Implement proper transaction handling and error recovery

### 4.5 Phase 4: Vector Embeddings Implementation
- Research and select appropriate embedding models for multilingual ancient texts
- Implement text chunking strategy optimized for Greek, Latin, and other languages
- Create embedding generation pipeline with proper caching
- Integrate vector database (e.g., FAISS, Qdrant, or Pinecone)
- Implement similarity search API endpoints
- Create UI components for exploring similar texts
- Add embedding visualization tools
- Build incremental embedding update mechanism

### 4.6 Phase 5: BERT Semantic Mapping
- Integrate or fine-tune multilingual BERT models for ancient languages
- Implement semantic search functionality
- Create named entity recognition for people, places, and concepts
- Add semantic relationship visualization
- Implement cross-reference identification
- Create topic modeling and clustering capabilities
- Build semantic navigation interface
- Add contextual recommendations based on semantic similarity

## 5. Data Validation and Unification Implementation

### 5.1 Validation Utility
```python
def validate_catalog_files(catalog_path: str, author_path: str, data_dir: str):
    """Validate synchronization between catalog data and files."""
    import json
    from pathlib import Path
    
    # Load catalog
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)
    
    # Load authors
    with open(author_path, "r", encoding="utf-8") as f:
        author_data = json.load(f)
    
    # Statistics
    stats = {
        "total_catalog_entries": len(catalog_data.get("catalog", [])),
        "total_authors": len(author_data),
        "missing_files": 0,
        "missing_authors": 0,
        "unlisted_files": 0
    }
    
    # Track issues
    missing_files = []
    missing_authors = []
    textgroups_without_authors = set()
    
    # Check each catalog entry for corresponding file
    for entry in catalog_data.get("catalog", []):
        urn = entry.get("urn", "")
        if not urn:
            continue
        
        # Parse URN
        try:
            parts = urn.split(":")
            if len(parts) >= 4:
                namespace = parts[2]
                identifier = parts[3].split(":")[0]
                id_parts = identifier.split(".")
                
                if len(id_parts) >= 3:
                    textgroup = id_parts[0]
                    work = id_parts[1]
                    version = id_parts[2]
                    
                    # Check if author exists
                    if textgroup not in author_data:
                        textgroups_without_authors.add(textgroup)
                    
                    # Construct expected file path
                    file_path = Path(data_dir) / namespace / textgroup / work / f"{textgroup}.{work}.{version}.xml"
                    
                    # Check if file exists
                    if not file_path.exists():
                        missing_files.append((urn, str(file_path)))
        except Exception as e:
            print(f"Error parsing URN {urn}: {e}")
    
    # Check for unlisted files
    all_xml_files = list(Path(data_dir).glob("**/*.xml"))
    known_urns = [entry.get("urn", "") for entry in catalog_data.get("catalog", [])]
    
    for xml_file in all_xml_files:
        # Try to derive URN from file path
        try:
            relative_path = xml_file.relative_to(data_dir)
            parts = list(relative_path.parts)
            
            if len(parts) >= 4 and parts[3].endswith(".xml"):
                file_name = parts[3].replace(".xml", "")
                name_parts = file_name.split(".")
                
                if len(name_parts) >= 3:
                    textgroup = name_parts[0]
                    work = name_parts[1]
                    version = name_parts[2]
                    namespace = parts[0]
                    
                    # Construct URN
                    urn = f"urn:cts:{namespace}:{textgroup}.{work}.{version}"
                    
                    # Check if in catalog
                    if urn not in known_urns and not any(known_urn.startswith(urn + ":") for known_urn in known_urns):
                        # This file is not in the catalog
                        stats["unlisted_files"] += 1
        except Exception as e:
            print(f"Error processing file {xml_file}: {e}")
    
    # Update statistics
    stats["missing_files"] = len(missing_files)
    stats["missing_authors"] = len(textgroups_without_authors)
    
    # Return validation results
    return {
        "stats": stats,
        "missing_files": missing_files,
        "textgroups_without_authors": list(textgroups_without_authors),
        "validity": stats["missing_files"] == 0 and stats["missing_authors"] == 0
    }
```

### 5.2 Catalog Merger Utility

```python
def merge_indexes(author_path: str, catalog_path: str, output_path: str):
    """Merge author-index.json and catalog-index.json into a unified file."""
    import json
    from pathlib import Path
    
    # Load author index
    with open(author_path, "r", encoding="utf-8") as f:
        authors = json.load(f)
    
    # Load catalog index
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_data = json.load(f)
    
    # Create merged structure
    merged_data = {
        "statistics": {
            "nodeCount": catalog_data.get("nodeCount", 0),
            "greekWords": catalog_data.get("greekWords", 0),
            "latinWords": catalog_data.get("latinWords", 0),
            "arabicwords": catalog_data.get("arabicwords", 0),
            "authorCount": len(authors),
            "textCount": len(catalog_data.get("catalog", []))
        },
        "authors": authors,
        "catalog": []
    }
    
    # Process catalog entries and link to authors
    for item in catalog_data.get("catalog", []):
        # Extract textgroup from URN
        textgroup = None
        try:
            urn_parts = item["urn"].split(":")
            if len(urn_parts) >= 4:
                identifier = urn_parts[3].split(":")[0]
                id_parts = identifier.split(".")
                if len(id_parts) >= 1:
                    textgroup = id_parts[0]
        except Exception:
            pass
        
        # Add author_id reference if it exists in authors
        catalog_entry = item.copy()
        if textgroup and textgroup in authors:
            catalog_entry["author_id"] = textgroup
        
        merged_data["catalog"].append(catalog_entry)
    
    # Write merged file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print(f"Merged catalog written to {output_path}")
    print(f"Statistics: {merged_data['statistics']}")
    
    return merged_data
```

## 6. Core Services Implementation

### 6.1 CatalogService
```python
class CatalogService:
    """Service for accessing the unified catalog."""
    
    def __init__(self, catalog_path: str = "data/unified-catalog.json"):
        self.catalog_path = Path(catalog_path)
        
        # Primary data
        self._catalog: Optional[UnifiedCatalog] = None
        
        # Derived indexes
        self._texts_by_urn: Dict[str, Text] = {}
        self._texts_by_author: Dict[str, List[Text]] = {}
        self._texts_by_language: Dict[str, List[Text]] = {}
        self._authors_by_century: Dict[int, List[Author]] = {}
        self._authors_by_type: Dict[str, List[Author]] = {}
        self._available_languages: Set[str] = set()
        
        # Load data
        self._load_catalog()
    
    def _load_catalog(self):
        """Load the unified catalog and build indexes."""
        if not self.catalog_path.exists():
            logger.error(f"Unified catalog not found: {self.catalog_path}")
            raise FileNotFoundError(f"Unified catalog not found: {self.catalog_path}")
        
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._catalog = UnifiedCatalog.parse_obj(data)
            
            # Build text indexes
            for text in self._catalog.catalog:
                # Index by URN
                self._texts_by_urn[text.urn] = text
                
                # Index by author
                if text.author_id:
                    if text.author_id not in self._texts_by_author:
                        self._texts_by_author[text.author_id] = []
                    self._texts_by_author[text.author_id].append(text)
                
                # Index by language
                for lang in text.language.split(","):
                    lang = lang.strip()
                    if lang:
                        self._available_languages.add(lang)
                        if lang not in self._texts_by_language:
                            self._texts_by_language[lang] = []
                        self._texts_by_language[lang].append(text)
            
            # Build author indexes
            for author_id, author in self._catalog.authors.items():
                # Index by century
                if author.century not in self._authors_by_century:
                    self._authors_by_century[author.century] = []
                self._authors_by_century[author.century].append(author)
                
                # Index by type
                if author.type not in self._authors_by_type:
                    self._authors_by_type[author.type] = []
                self._authors_by_type[author.type].append(author)
            
            logger.info(f"Loaded unified catalog with {len(self._catalog.authors)} authors and {len(self._catalog.catalog)} texts")
            
        except Exception as e:
            logger.error(f"Error loading unified catalog: {e}")
            raise
```

### 6.2 URN Utilities
```python
class CtsUrn:
    """Utility class for CTS URN parsing and manipulation."""
    
    def __init__(self, urn_string: str):
        self.urn_string = urn_string
        self.namespace, self.textgroup, self.work, self.version, self.passage = self._parse()
    
    def _parse(self) -> Tuple[str, str, str, str, Optional[str]]:
        """Parse URN into components."""
        if not self.urn_string.startswith("urn:cts:"):
            raise ValueError(f"Invalid CTS URN: {self.urn_string}")
        
        parts = self.urn_string.split(":")
        if len(parts) < 4:
            raise ValueError(f"Incomplete CTS URN: {self.urn_string}")
        
        namespace = parts[2]
        
        # Handle passage reference if present
        work_parts = parts[3].split(":")
        identifier = work_parts[0]
        passage = work_parts[1] if len(work_parts) > 1 else None
        
        # Parse text identifier
        id_parts = identifier.split(".")
        if len(id_parts) < 2:
            raise ValueError(f"Invalid text identifier in URN: {identifier}")
            
        textgroup = id_parts[0]
        work = id_parts[1] if len(id_parts) > 1 else ""
        version = id_parts[2] if len(id_parts) > 2 else ""
        
        return namespace, textgroup, work, version, passage
    
    def get_file_path(self, base_dir: str = "data") -> Path:
        """Derive file path from CTS URN."""
        if not self.version:
            raise ValueError("Cannot derive file path without version information")
        
        return Path(base_dir) / self.namespace / self.textgroup / self.work / f"{self.textgroup}.{self.work}.{self.version}.xml"
    
    def get_textgroup_urn(self) -> str:
        """Get URN for the textgroup level."""
        return f"urn:cts:{self.namespace}:{self.textgroup}"
    
    def get_work_urn(self) -> str:
        """Get URN for the work level."""
        return f"urn:cts:{self.namespace}:{self.textgroup}.{self.work}"
    
    def get_version_urn(self) -> str:
        """Get URN for the version level without passage."""
        return f"urn:cts:{self.namespace}:{self.textgroup}.{self.work}.{self.version}"
    
    def __str__(self) -> str:
        return self.urn_string
```

## 7. Testing Strategy

Extend the testing strategy to include validation of the unified catalog:

```python
def test_unified_catalog_integrity():
    """Test that the unified catalog correctly links authors and texts."""
    service = CatalogService()
    
    # Check that all texts with author_id have a corresponding author
    for text in service.get_all_texts():
        if text.author_id:
            author = service.get_author(text.author_id)
            assert author is not None, f"Text {text.urn} references non-existent author {text.author_id}"
    
    # Check that textgroups derived from URNs match author_id when present
    for text in service.get_all_texts():
        if text.textgroup and text.author_id:
            assert text.textgroup == text.author_id, f"Text {text.urn} has textgroup {text.textgroup} but author_id {text.author_id}"
```

## 8. Next Steps and Priorities

1. **Data Validation**: Implement and run validation to ensure catalog and file synchronization
2. **Catalog Merger**: Create unified catalog from validated data sources
3. **Core Models**: Implement Pydantic models for the unified catalog
4. **URN Utilities**: Build CTS URN parsing and manipulation utilities
5. **Basic Services**: Develop CatalogService and XMLProcessorService
6. **API Endpoints**: Create initial browsing and viewing endpoints
7. **UI Templates**: Build basic UI with HTMX and Tailwind
8. **Text Reader**: Implement basic reader with navigation
9. **Search**: Add simple search functionality
10. **Import**: Set up initial import capability
