# Revised Implementation Plan for Eulogos XML Processing Refactoring

## Project Overview

This plan outlines a comprehensive approach for refactoring the XML processing code in the Eulogos project, establishing `integrated_catalog.json` as the single source of truth while maintaining backward compatibility with existing code. The implementation focuses on a gradual transition to the new architecture without disrupting current functionality.

## Objectives

1. Establish integrated_catalog.json as the sole source of truth for catalog data
2. Create a clean, modular architecture with clear separation of concerns
3. Implement proper error handling and logging
4. Improve performance through caching and efficient indexing
5. Maintain backward compatibility during the transition
6. Provide a smooth migration path to the new architecture

## Implementation Phases

### Phase 1: Core Models and Infrastructure (Week 1)

#### 1. Enhanced Catalog Models

Create `app/models/enhanced_catalog.py` with Pydantic models that are compatible with existing structures:

```python
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime

class ModelVersion(BaseModel):
    """Version information for models."""

    version: str = "1.0.0"
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class TextVersion(BaseModel):
    """A version of a text (edition or translation)."""

    urn: str
    label: str
    description: Optional[str] = None
    language: str
    path: Optional[str] = None
    word_count: int = 0
    editor: Optional[str] = None
    translator: Optional[str] = None
    archived: bool = False  # Maintain compatibility with existing feature
    favorite: bool = False  # Maintain compatibility with existing feature

    # Methods to convert between old and new models
    @classmethod
    def from_original(cls, original_model: Any) -> "TextVersion":
        """Convert from original model to new model."""
        return cls(
            urn=original_model.urn,
            label=getattr(original_model, "label", ""),
            description=getattr(original_model, "description", None),
            language=getattr(original_model, "language", ""),
            path=getattr(original_model, "path", None),
            word_count=getattr(original_model, "wordcount", 0),
            editor=getattr(original_model, "editor", None),
            translator=getattr(original_model, "translator", None),
            archived=getattr(original_model, "archived", False),
            favorite=getattr(original_model, "favorite", False)
        )

    def to_original(self, original_class: Any) -> Any:
        """Convert to original model."""
        return original_class(
            urn=self.urn,
            group_name=getattr(self, "group_name", ""),
            work_name=getattr(self, "work_name", ""),
            language=self.language,
            wordcount=self.word_count,
            path=self.path,
            archived=self.archived,
            favorite=self.favorite
        )

class Work(BaseModel):
    """A work with editions and translations."""

    id: str  # Work ID (e.g., tlg001)
    title: str
    urn: str
    language: str
    editions: Dict[str, TextVersion] = {}
    translations: Dict[str, TextVersion] = {}
    archived: bool = False

class Author(BaseModel):
    """An author with works."""

    id: str  # Author ID (e.g., tlg0004)
    name: str
    century: Optional[int] = None
    type: Optional[str] = None
    works: Dict[str, Work] = {}
    archived: bool = False

class CatalogStatistics(BaseModel):
    """Statistics about the catalog."""

    author_count: int = 0
    work_count: int = 0
    edition_count: int = 0
    translation_count: int = 0
    greek_word_count: int = 0
    latin_word_count: int = 0
    arabic_word_count: int = 0

class Catalog(BaseModel):
    """The integrated catalog."""

    statistics: CatalogStatistics = Field(default_factory=CatalogStatistics)
    authors: Dict[str, Author] = {}

    model_version: ModelVersion = Field(default_factory=ModelVersion)
```

#### 2. Enhanced XML Document Models

Create `app/models/xml_document.py` with models for XML document representation:

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class XMLReference(BaseModel):
    """A reference to a section in an XML document."""

    reference: str
    element: Any  # ElementTree element
    text_content: Optional[str] = None
    parent_ref: Optional[str] = None
    child_refs: List[str] = []

    class Config:
        arbitrary_types_allowed = True

class XMLDocument(BaseModel):
    """A parsed XML document with references."""

    file_path: str
    urn: str
    root_element: Any  # ElementTree root element
    references: Dict[str, XMLReference] = {}
    metadata: Dict[str, Any] = {}

    # Cache information
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0

    class Config:
        arbitrary_types_allowed = True
```

#### 3. Enhanced URN Model

Create `app/models/enhanced_urn.py` that extends the existing URN model but maintains compatibility:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from pathlib import Path

class EnhancedURN(BaseModel):
    """Enhanced model for Canonical Text Services URNs."""

    value: str
    namespace: Optional[str] = None
    textgroup: Optional[str] = None
    work: Optional[str] = None
    version: Optional[str] = None
    reference: Optional[str] = None

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
        urn = self.value.split("#")[0]
        parts = urn.split(":")

        if len(parts) >= 3:
            self.namespace = parts[2]

        if len(parts) >= 4:
            id_part = parts[3].split(":", 1)
            identifier = id_part[0]

            if len(id_part) > 1:
                self.reference = id_part[1]

            id_parts = identifier.split(".")
            if len(id_parts) >= 1:
                self.textgroup = id_parts[0]
            if len(id_parts) >= 2:
                self.work = id_parts[1]
            if len(id_parts) >= 3:
                self.version = id_parts[2]

        if len(parts) >= 5:
            self.reference = parts[4]

    def get_id_components(self) -> Dict[str, Optional[str]]:
        """Get the ID components of the URN."""
        return {
            "namespace": self.namespace,
            "textgroup": self.textgroup,
            "work": self.work,
            "version": self.version,
            "reference": self.reference
        }

    def is_valid_for_path(self) -> bool:
        """Check if the URN has all components needed for path resolution."""
        return bool(self.textgroup and self.work and self.version)

    def get_file_path(self, base_dir: str = "data") -> Path:
        """Derive file path from URN components."""
        if not self.is_valid_for_path():
            raise ValueError(f"URN missing components needed for path: {self.value}")

        # Compatibility with existing structure: don't include namespace in path
        return (
            Path(base_dir) /
            f"{self.textgroup}/{self.work}/{self.textgroup}.{self.work}.{self.version}.xml"
        )

    @classmethod
    def from_original(cls, original_urn: Any) -> "EnhancedURN":
        """Convert from original URN model."""
        if hasattr(original_urn, "value"):
            # It's already a Pydantic model
            return cls(value=original_urn.value)
        elif hasattr(original_urn, "urn_string"):
            # It's a CtsUrn
            return cls(value=original_urn.urn_string)
        else:
            # Assume it's a string
            return cls(value=str(original_urn))

    def to_original_urn(self, original_class: Any) -> Any:
        """Convert to original URN model if needed."""
        if hasattr(original_class, "value"):
            # It's a Pydantic model
            return original_class(value=self.value)
        elif hasattr(original_class, "urn_string"):
            # It's the old CtsUrn
            return original_class(self.value)
        else:
            # Return self
            return self
```

#### 4. Configuration Management

Create `app/config.py` for centralized settings:

```python
from pydantic import BaseSettings, Field, validator
from pathlib import Path
from typing import Optional, Dict, Any
import os

class EulogosSettings(BaseSettings):
    """Configuration settings for Eulogos application."""

    # Catalog paths
    catalog_path: Path = Field(
        default=Path("integrated_catalog.json"),
        description="Path to the integrated catalog JSON file"
    )

    # Data directories
    data_dir: Path = Field(
        default=Path("data"),
        description="Base directory for text data files"
    )

    # Cache settings
    xml_cache_size: int = Field(
        default=100,
        description="Maximum number of XML documents to cache"
    )
    xml_cache_ttl: int = Field(
        default=3600,
        description="Time to live for cached XML documents in seconds"
    )

    # Performance settings
    enable_caching: bool = Field(
        default=True,
        description="Enable caching for XML documents"
    )

    # Compatibility settings
    compatibility_mode: bool = Field(
        default=True,
        description="Enable compatibility with existing code"
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Optional[Path] = Field(
        default=Path("logs/eulogos.log"),
        description="Log file path"
    )

    @validator('catalog_path', 'data_dir', pre=True)
    def validate_paths(cls, v):
        """Validate paths and convert to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    def as_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {k: str(v) if isinstance(v, Path) else v for k, v in self.dict().items()}

    class Config:
        env_prefix = "EULOGOS_"
        env_file = ".env"
```

#### 5. Logging Framework

Create `app/utils/logging.py` for comprehensive logging:

```python
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import os

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    app_name: str = "eulogos"
) -> logging.Logger:
    """Set up application logging.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        app_name: Application name for logger

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatters
    verbose_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
    )

    simple_formatter = logging.Formatter(
        "%(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10_485_760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(verbose_formatter)
        logger.addHandler(file_handler)

    return logger
```

#### 6. Test Infrastructure

Create `tests/conftest.py` for shared test fixtures:

```python
import pytest
import tempfile
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, Any

from app.config import EulogosSettings
from app.models.enhanced_catalog import Catalog, Author, Work, TextVersion

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_catalog_data() -> Dict[str, Any]:
    """Create sample catalog data for tests."""
    return {
        "statistics": {
            "author_count": 1,
            "work_count": 1,
            "edition_count": 1,
            "translation_count": 0,
            "greek_word_count": 100,
            "latin_word_count": 0,
            "arabic_word_count": 0
        },
        "authors": {
            "tlg0012": {
                "id": "tlg0012",
                "name": "Homer",
                "century": -8,
                "type": "Author",
                "works": {
                    "tlg001": {
                        "id": "tlg001",
                        "title": "Iliad",
                        "urn": "urn:cts:greekLit:tlg0012.tlg001",
                        "language": "grc",
                        "editions": {
                            "perseus-grc1": {
                                "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
                                "label": "Homeri Ilias",
                                "language": "grc",
                                "path": "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml",
                                "word_count": 100
                            }
                        },
                        "translations": {}
                    }
                }
            }
        }
    }

@pytest.fixture
def sample_catalog_file(temp_dir, sample_catalog_data):
    """Create a sample catalog file for tests."""
    catalog_path = temp_dir / "integrated_catalog.json"

    with open(catalog_path, "w") as f:
        json.dump(sample_catalog_data, f)

    return catalog_path

@pytest.fixture
def sample_xml_file(temp_dir):
    """Create a sample XML file for tests."""
    # Create directory structure
    xml_dir = temp_dir / "data" / "tlg0012" / "tlg001"
    os.makedirs(xml_dir, exist_ok=True)

    # Create XML file
    xml_path = xml_dir / "tlg0012.tlg001.perseus-grc1.xml"

    # Create simple TEI XML
    root = ET.Element("{http://www.tei-c.org/ns/1.0}TEI")
    header = ET.SubElement(root, "{http://www.tei-c.org/ns/1.0}teiHeader")
    file_desc = ET.SubElement(header, "{http://www.tei-c.org/ns/1.0}fileDesc")
    title_stmt = ET.SubElement(file_desc, "{http://www.tei-c.org/ns/1.0}titleStmt")
    title = ET.SubElement(title_stmt, "{http://www.tei-c.org/ns/1.0}title")
    title.text = "Homeri Ilias"

    # Add text element with book and lines
    text_elem = ET.SubElement(root, "{http://www.tei-c.org/ns/1.0}text")
    body = ET.SubElement(text_elem, "{http://www.tei-c.org/ns/1.0}body")

    # Add book 1
    book = ET.SubElement(body, "{http://www.tei-c.org/ns/1.0}div", n="1", type="book")
    book_title = ET.SubElement(book, "{http://www.tei-c.org/ns/1.0}head")
    book_title.text = "Book 1"

    # Add some lines
    for i in range(1, 5):
        line = ET.SubElement(book, "{http://www.tei-c.org/ns/1.0}l", n=str(i))
        line.text = f"This is line {i} of Book 1"

    # Write to file
    tree = ET.ElementTree(root)
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    return xml_path

@pytest.fixture
def test_settings(sample_catalog_file, temp_dir):
    """Create test settings with temp paths."""
    return EulogosSettings(
        catalog_path=sample_catalog_file,
        data_dir=temp_dir / "data",
        xml_cache_size=10,
        enable_caching=True,
        compatibility_mode=True
    )
```

Create `tests/test_enhanced_urn.py` for testing the enhanced URN model:

```python
import pytest
from pathlib import Path

from app.models.enhanced_urn import EnhancedURN

def test_urn_parsing():
    """Test URN parsing."""
    # Basic URN
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert urn.namespace == "greekLit"
    assert urn.textgroup == "tlg0012"
    assert urn.work == "tlg001"
    assert urn.version == "perseus-grc1"
    assert urn.reference is None

    # URN with reference
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1:1.1-1.10")
    assert urn.namespace == "greekLit"
    assert urn.textgroup == "tlg0012"
    assert urn.work == "tlg001"
    assert urn.version == "perseus-grc1"
    assert urn.reference == "1.1-1.10"

    # URN with colon-separated reference
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1:1.1")
    assert urn.reference == "1.1"

def test_urn_validation():
    """Test URN validation."""
    # Valid URN
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert urn.is_valid_for_path()

    # Invalid URN (missing version)
    with pytest.raises(ValueError):
        EnhancedURN(value="not-a-urn")

    # Invalid for path (missing components)
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012")
    assert not urn.is_valid_for_path()

def test_get_file_path():
    """Test file path generation."""
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    path = urn.get_file_path("test_data")

    # Path should not include namespace
    expected_path = Path("test_data/tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml")
    assert path == expected_path

    # Invalid URN for path
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012")
    with pytest.raises(ValueError):
        urn.get_file_path()

def test_compatibility():
    """Test compatibility with original URN models."""
    # Create a mock original URN
    class MockOriginalURN:
        def __init__(self, value):
            self.value = value

    # Test conversion from original
    original = MockOriginalURN("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    enhanced = EnhancedURN.from_original(original)
    assert enhanced.value == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test conversion to original
    converted = enhanced.to_original_urn(MockOriginalURN)
    assert isinstance(converted, MockOriginalURN)
    assert converted.value == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test with CtsUrn-like interface
    class MockCtsUrn:
        def __init__(self, urn_string):
            self.urn_string = urn_string

    original_cts = MockCtsUrn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    enhanced = EnhancedURN.from_original(original_cts)
    assert enhanced.value == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
```

### Phase 2: CatalogService Enhancement (Week 2)

#### 1. Enhanced CatalogService

Create `app/services/enhanced_catalog_service.py`:

```python
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union, Type
from functools import lru_cache

from app.models.enhanced_catalog import Catalog, Author, Work, TextVersion
from app.models.enhanced_urn import EnhancedURN
from app.config import EulogosSettings

logger = logging.getLogger(__name__)

class EnhancedCatalogService:
    """Enhanced service for accessing the integrated catalog."""

    def __init__(self, settings: Optional[EulogosSettings] = None):
        """Initialize the catalog service."""
        self.settings = settings or EulogosSettings()
        self._catalog: Optional[Catalog] = None
        self._last_loaded: float = 0

        # Indexes for efficient lookups
        self._text_path_by_urn: Dict[str, str] = {}
        self._urn_by_path: Dict[str, str] = {}
        self._texts_by_author: Dict[str, List[str]] = {}
        self._texts_by_language: Dict[str, List[str]] = {}
        self._original_models: Dict[str, Any] = {}

        # Import here to avoid circular imports
        try:
            from app.models.catalog import Text
            self._original_text_class = Text
        except ImportError:
            self._original_text_class = None

    def load_catalog(self, force_reload: bool = False) -> Catalog:
        """Load the catalog from file."""
        if not force_reload and self._catalog and time.time() - self._last_loaded < 60:
            # Use cached catalog if it's less than 1 minute old
            return self._catalog

        if not self.settings.catalog_path.exists():
            logger.error(f"Catalog file not found: {self.settings.catalog_path}")
            raise FileNotFoundError(f"Catalog file not found: {self.settings.catalog_path}")

        try:
            logger.info(f"Loading catalog from {self.settings.catalog_path}")
            with open(self.settings.catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._catalog = Catalog.model_validate(data)
                self._last_loaded = time.time()

                # Build indexes
                self._build_indexes()

                logger.info(f"Loaded catalog with {len(self._catalog.authors)} authors")
                return self._catalog
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            raise

    def _build_indexes(self) -> None:
        """Build lookup indexes for efficiency."""
        if not self._catalog:
            return

        logger.debug("Building catalog indexes")

        # Clear existing indexes
        self._text_path_by_urn = {}
        self._urn_by_path = {}
        self._texts_by_author = {}
        self._texts_by_language = {}

        # Build indexes from catalog entries
        for author_id, author in self._catalog.authors.items():
            if author_id not in self._texts_by_author:
                self._texts_by_author[author_id] = []

            for work_id, work in author.works.items():
                # Process editions
                for edition_id, edition in work.editions.items():
                    urn = edition.urn

                    # Add to indexes
                    if edition.path:
                        self._text_path_by_urn[urn] = edition.path
                        self._urn_by_path[edition.path] = urn

                    self._texts_by_author[author_id].append(urn)

                    # Add to language index
                    if edition.language not in self._texts_by_language:
                        self._texts_by_language[edition.language] = []
                    self._texts_by_language[edition.language].append(urn)

                # Process translations
                for translation_id, translation in work.translations.items():
                    urn = translation.urn

                    # Add to indexes
                    if translation.path:
                        self._text_path_by_urn[urn] = translation.path
                        self._urn_by_path[translation.path] = urn

                    self._texts_by_author[author_id].append(urn)

                    # Add to language index
                    if translation.language not in self._texts_by_language:
                        self._texts_by_language[translation.language] = []
                    self._texts_by_language[translation.language].append(urn)

        logger.debug(f"Built catalog indexes with {len(self._text_path_by_urn)} paths")

    def get_path_by_urn(self, urn: Union[str, EnhancedURN]) -> Optional[str]:
        """Get the file path for a text by URN."""
        if not self._catalog:
            self.load_catalog()

        # Convert to string if it's an EnhancedURN
        urn_str = urn.value if isinstance(urn, EnhancedURN) else str(urn)

        return self._text_path_by_urn.get(urn_str)

    def resolve_file_path(self, urn: Union[str, EnhancedURN, Any]) -> Optional[Path]:
        """Resolve a URN to a full file path.

        This method handles different URN formats for backward compatibility:
        - EnhancedURN instance
        - URN string
        - Legacy URN objects (with urn_string attribute)
        """
        if not self._catalog:
            self.load_catalog()

        # Handle different URN types for backward compatibility
        urn_str = ""
        if isinstance(urn, EnhancedURN):
            urn_str = urn.value
        elif hasattr(urn, "value"):
            # Original URN model
            urn_str = urn.value
        elif hasattr(urn, "urn_string"):
            # Legacy CtsUrn
            urn_str = urn.urn_string
        else:
            # Assume string
            urn_str = str(urn)

        # Look up path in catalog
        relative_path = self.get_path_by_urn(urn_str)
        if relative_path:
            full_path = self.settings.data_dir / relative_path
            logger.debug(f"Resolved URN {urn_str} to path {full_path}")
            return full_path

        logger.warning(f"No path found in catalog for URN: {urn_str}")

        # Fallback to direct path construction for backward compatibility
        try:
            if self.settings.compatibility_mode:
                enhanced_urn = EnhancedURN(value=urn_str)
                if enhanced_urn.is_valid_for_path():
                    fallback_path = enhanced_urn.get_file_path(str(self.settings.data_dir))
                    logger.warning(f"Using fallback path resolution for {urn_str}: {fallback_path}")
                    return fallback_path
        except Exception as e:
            logger.error(f"Error in fallback path resolution: {e}")

        return None

    def get_text_by_urn(self, urn: Union[str, EnhancedURN, Any]) -> Optional[Union[TextVersion, Any]]:
        """Get a text by URN, with backward compatibility support."""
        if not self._catalog:
            self.load_catalog()

        # Handle different URN types
        urn_str = ""
        if isinstance(urn, EnhancedURN):
            urn_str = urn.value
        elif hasattr(urn, "value"):
            urn_str = urn.value
        elif hasattr(urn, "urn_string"):
            urn_str = urn.urn_string
        else:
            urn_str = str(urn)

        # Parse URN to navigate catalog
        try:
            enhanced_urn = EnhancedURN(value=urn_str)

            # Navigate through the catalog structure
            author = self._catalog.authors.get(enhanced_urn.textgroup)
            if not author:
                return None

            work = author.works.get(enhanced_urn.work)
            if not work:
                return None

            # Look in editions and translations
            text = None
            if enhanced_urn.version in work.editions:
                text = work.editions[enhanced_urn.version]
            elif enhanced_urn.version in work.translations:
                text = work.translations[enhanced_urn.version]

            if not text:
                return None

            # For compatibility, convert to original model if needed
            if self.settings.compatibility_mode and self._original_text_class:
                # Cache original model to avoid recreating it
                if urn_str not in self._original_models:
                    # Create original model with required fields
                    original = self._original_text_class(
                        urn=text.urn,
                        group_name=author.name,
                        work_name=work.title,
                        language=text.language,
                        wordcount=text.word_count,
                        path=text.path,
                        archived=getattr(text, "archived", False),
                        favorite=getattr(text, "favorite", False)
                    )
                    self._original_models[urn_str] = original

                return self._original_models[urn_str]

            return text

        except Exception as e:
            logger.error(f"Error getting text for URN {urn_str}: {e}")
            return None

    def get_authors(self, include_archived: bool = False) -> List[Author]:
        """Get all authors."""
        if not self._catalog:
            self.load_catalog()

        authors = list(self._catalog.authors.values())

        if not include_archived:
            # Filter out archived authors
            authors = [a for a in authors if not getattr(a, "archived", False)]

        return authors

    def get_texts_by_author(self, author_id: str, include_archived: bool = False) -> List[Any]:
        """Get all texts by an author."""
        if not self._catalog:
            self.load_catalog()

        if author_id not in self._texts_by_author:
            return []

        texts = []
        for urn in self._texts_by_author[author_id]:
            text = self.get_text_by_urn(urn)
            if text and (include_archived or not getattr(text, "archived", False)):
                texts.append(text)

        return texts

    def validate_path_consistency(self) -> Dict[str, Any]:
        """Validate that all URNs in the catalog have valid paths."""
        if not self._catalog:
            self.load_catalog()

        results = {
            "total_urns": 0,
            "urns_with_path": 0,
            "urns_without_path": 0,
            "existing_files": 0,
            "missing_files": 0,
            "urns_without_path_list": [],
            "missing_files_list": []
        }

        # Check each URN in the catalog
        for author_id, author in self._catalog.authors.items():
            for work_id, work in author.works.items():
                # Check editions
                for edition_id, edition in work.editions.items():
                    results["total_urns"] += 1

                    if edition.path:
                        results["urns_with_path"] += 1
                        file_path = self.settings.data_dir / edition.path

                        if file_path.exists():
                            results["existing_files"] += 1
                        else:
                            results["missing_files"] += 1
                            results["missing_files_list"].append((edition.urn, str(file_path)))
                    else:
                        results["urns_without_path"] += 1
                        results["urns_without_path_list"].append(edition.urn)

                # Check translations
                for translation_id, translation in work.translations.items():
                    results["total_urns"] += 1

                    if translation.path:
                        results["urns_with_path"] += 1
                        file_path = self.settings.data_dir / translation.path

                        if file_path.exists():
                            results["existing_files"] += 1
                        else:
                            results["missing_files"] += 1
                            results["missing_files_list"].append((translation.urn, str(file_path)))
                    else:
                        results["urns_without_path"] += 1
                        results["urns_without_path_list"].append(translation.urn)

        return results

    def archive_text(self, urn: Union[str, EnhancedURN, Any], archive: bool = True) -> bool:
        """Archive or unarchive a text."""
        text = self.get_text_by_urn(urn)
        if not text:
            return False

        # Set archived status
        if hasattr(text, "archived"):
            text.archived = archive

        return True

    def toggle_favorite(self, urn: Union[str, EnhancedURN, Any]) -> bool:
        """Toggle favorite status for a text."""
        text = self.get_text_by_urn(urn)
        if not text:
            return False

        # Toggle favorite status
        if hasattr(text, "favorite"):
            text.favorite = not text.favorite

        return True
```

#### 2. Compatibility Layer

Create `app/services/catalog_service_adapter.py` for backward compatibility:

```python
import warnings
from typing import Any, Optional, List, Dict, Union
from pathlib import Path

from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.config import EulogosSettings
from app.models.enhanced_urn import EnhancedURN

class CatalogServiceAdapter:
    """Adapter for backward compatibility with existing CatalogService."""

    def __init__(self, enhanced_service: Optional[EnhancedCatalogService] = None, settings: Optional[EulogosSettings] = None):
        """Initialize the adapter."""
        self.enhanced_service = enhanced_service or EnhancedCatalogService(settings=settings)
        # Issue deprecation warning
        warnings.warn(
            "CatalogServiceAdapter is deprecated. Use EnhancedCatalogService directly.",
            DeprecationWarning,
            stacklevel=2
        )

    def load_catalog(self):
        """Load the catalog from file."""
        return self.enhanced_service.load_catalog()

    def get_text_by_urn(self, urn):
        """Get a text by URN."""
        return self.enhanced_service.get_text_by_urn(urn)

    def get_path_by_urn(self, urn):
        """Get the file path for a text by URN."""
        return self.enhanced_service.get_path_by_urn(urn)

    def resolve_file_path(self, urn):
        """Resolve a URN to a full file path."""
        return self.enhanced_service.resolve_file_path(urn)

    def get_authors(self, include_archived=False):
        """Get all authors."""
        return self.enhanced_service.get_authors(include_archived)

    def get_texts_by_author(self, author_id, include_archived=False):
        """Get all texts by an author."""
        return self.enhanced_service.get_texts_by_author(author_id, include_archived)

    def archive_text(self, urn, archive=True):
        """Archive or unarchive a text."""
        return self.enhanced_service.archive_text(urn, archive)

    def toggle_text_favorite(self, urn):
        """Toggle favorite status for a text."""
        return self.enhanced_service.toggle_favorite(urn)

    # Implement other methods as needed
```

#### 3. Catalog Service Tests

Create `tests/test_enhanced_catalog_service.py`:

```python
import pytest
import json
from pathlib import Path
import os

from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.models.enhanced_urn import EnhancedURN

def test_load_catalog(test_settings, sample_catalog_file):
    """Test loading the catalog."""
    service = EnhancedCatalogService(settings=test_settings)
    catalog = service.load_catalog()

    # Check that catalog loaded successfully
    assert catalog is not None
    assert len(catalog.authors) == 1
    assert "tlg0012" in catalog.authors

    # Check author data
    homer = catalog.authors["tlg0012"]
    assert homer.name == "Homer"
    assert homer.century == -8

    # Check works
    assert "tlg001" in homer.works
    iliad = homer.works["tlg001"]
    assert iliad.title == "Iliad"

    # Check editions
    assert "perseus-grc1" in iliad.editions
    edition = iliad.editions["perseus-grc1"]
    assert edition.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
    assert edition.path == "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml"

def test_get_path_by_urn(test_settings):
    """Test getting path by URN."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    # Test with string URN
    path = service.get_path_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert path == "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml"

    # Test with EnhancedURN object
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    path = service.get_path_by_urn(urn)
    assert path == "tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml"

    # Test non-existent URN
    path = service.get_path_by_urn("urn:cts:greekLit:tlg0012.tlg002.perseus-grc1")
    assert path is None

def test_resolve_file_path(test_settings, sample_xml_file):
    """Test resolving URN to file path."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    # Test with string URN
    path = service.resolve_file_path("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert path is not None
    assert path.name == "tlg0012.tlg001.perseus-grc1.xml"

    # Test with EnhancedURN object
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    path = service.resolve_file_path(urn)
    assert path is not None
    assert path.name == "tlg0012.tlg001.perseus-grc1.xml"

    # Test fallback for non-existent URN in compatibility mode
    path = service.resolve_file_path("urn:cts:greekLit:tlg0013.tlg001.perseus-grc1")
    assert path is not None  # Should use fallback path
    assert path.name == "tlg0013.tlg001.perseus-grc1.xml"

    # Test fallback disabled
    service.settings.compatibility_mode = False
    path = service.resolve_file_path("urn:cts:greekLit:tlg0013.tlg001.perseus-grc1")
    assert path is None  # Should not use fallback path

def test_get_text_by_urn(test_settings):
    """Test getting text by URN."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    # Test with string URN
    text = service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert text is not None
    assert text.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test compatibility mode with original model
    service._original_text_class = type("Text", (), {})
    text = service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert text is not None
    assert hasattr(text, "urn")
    assert text.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

def test_validate_path_consistency(test_settings, sample_xml_file):
    """Test path consistency validation."""
    service = EnhancedCatalogService(settings=test_settings)
    service.load_catalog()

    results = service.validate_path_consistency()

    assert results["total_urns"] == 1
    assert results["urns_with_path"] == 1
    assert results["existing_files"] == 1
    assert results["missing_files"] == 0
```

#### 4. Update Dependencies

Create `app/dependencies.py` for dependency injection:

```python
from functools import lru_cache
import logging

from app.config import EulogosSettings
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.catalog_service_adapter import CatalogServiceAdapter

logger = logging.getLogger(__name__)

@lru_cache()
def get_settings() -> EulogosSettings:
    """Get application settings, cached for performance."""
    logger.debug("Creating EulogosSettings instance")
    return EulogosSettings()

@lru_cache()
def get_enhanced_catalog_service() -> EnhancedCatalogService:
    """Get an EnhancedCatalogService instance, cached for performance."""
    logger.debug("Creating EnhancedCatalogService instance")
    settings = get_settings()
    service = EnhancedCatalogService(settings=settings)

    # Eagerly load the catalog
    service.load_catalog()

    return service

@lru_cache()
def get_catalog_service() -> CatalogServiceAdapter:
    """Get a CatalogServiceAdapter instance, cached for performance.

    This provides backward compatibility with the old CatalogService.
    """
    logger.debug("Creating CatalogServiceAdapter instance")
    enhanced_service = get_enhanced_catalog_service()
    return CatalogServiceAdapter(enhanced_service=enhanced_service)
```

### Phase 3: XMLService Implementation (Week 3)

#### 1. Enhanced XMLService

Create `app/services/enhanced_xml_service.py`:

```python
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import re
from functools import lru_cache
import logging
from collections import OrderedDict
import warnings

from app.models.xml_document import XMLDocument, XMLReference
from app.models.enhanced_urn import EnhancedURN
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.config import EulogosSettings

logger = logging.getLogger(__name__)

class EnhancedXMLService:
    """Enhanced service for XML document processing."""

    def __init__(self, catalog_service: EnhancedCatalogService, settings: Optional[EulogosSettings] = None):
        """Initialize the XML service."""
        self.catalog_service = catalog_service
        self.settings = settings or EulogosSettings()
        self._cache = OrderedDict()

        # XML namespaces
        self.namespaces = {
            "ti": "http://chs.harvard.edu/xmlns/cts",
            "tei": "http://www.tei-c.org/ns/1.0"
        }

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

        # Check cache if enabled
        if self.settings.enable_caching and urn_str in self._cache:
            document = self._cache[urn_str]
            # Update access time and count
            document.last_accessed = datetime.utcnow()
            document.access_count += 1

            # Move to end of OrderedDict to maintain LRU order
            self._cache.move_to_end(urn_str)

            logger.debug(f"Cache hit for URN {urn_str}")
            return document

        logger.debug(f"Cache miss for URN {urn_str}")

        # Manage cache size
        self._manage_cache()

        # Resolve file path from URN using catalog
        file_path = self.catalog_service.resolve_file_path(urn_obj)
        if not file_path or not file_path.exists():
            logger.error(f"XML file not found for URN {urn_str} at path {file_path}")
            raise FileNotFoundError(f"XML file not found for URN {urn_str}")

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
                access_count=1
            )

            # Extract references
            self._extract_references(document)

            # Add to cache if enabled
            if self.settings.enable_caching:
                self._cache[urn_str] = document

            logger.debug(f"Loaded XML document with {len(document.references)} references")
            return document

        except Exception as e:
            logger.error(f"Error loading XML document {file_path} for URN {urn_str}: {e}")
            raise

    def _manage_cache(self) -> None:
        """Manage the document cache size."""
        # If cache is at limit, remove oldest entries
        while self.settings.enable_caching and len(self._cache) >= self.settings.xml_cache_size:
            # OrderedDict will remove in FIFO order by default
            self._cache.popitem(last=False)
            logger.debug("Removed oldest item from XML cache")

    def _extract_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """Extract metadata from an XML document."""
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

    def _extract_references(self, document: XMLDocument) -> None:
        """Extract references from an XML document."""
        try:
            self._extract_references_recursive(document.root_element, document, "")
            logger.debug(f"Extracted {len(document.references)} references")
        except Exception as e:
            logger.error(f"Error extracting references: {e}")

    def _extract_references_recursive(
        self, element: ET.Element, document: XMLDocument, parent_ref: str
    ) -> None:
        """Recursively extract references from an element."""
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
                parent_ref=parent_ref
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
        """Get text content of an element, including children."""
        text = element.text or ""
        for child in element:
            text += self._get_element_text(child)
            if child.tail:
                text += child.tail
        return text.strip()

    def get_passage(self, urn: Union[str, EnhancedURN, Any], reference: Optional[str] = None) -> Optional[str]:
        """Get a passage from an XML document by URN and reference."""
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
        """Get previous and next references relative to current reference."""
        try:
            document = self.load_document(urn)

            # Get all reference keys
            ref_keys = list(document.references.keys())

            # If current reference not found or no references
            if not ref_keys or current_ref not in ref_keys:
                return {"prev": None, "next": None}

            # Sort references naturally
            ref_keys.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)])

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
        """Transform a passage to HTML."""
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
        """Convert an XML element to HTML."""
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
                "ref": "a"
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
```

#### 2. XMLProcessorService Adapter

Create `app/services/xml_processor_adapter.py` for backward compatibility:

```python
import warnings
from typing import Any, Optional, Dict
from pathlib import Path

from app.services.enhanced_xml_service import EnhancedXMLService
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.config import EulogosSettings

class XMLProcessorServiceAdapter:
    """Adapter for backward compatibility with existing XMLProcessorService."""

    def __init__(
        self,
        enhanced_service: Optional[EnhancedXMLService] = None,
        catalog_service: Optional[EnhancedCatalogService] = None,
        settings: Optional[EulogosSettings] = None
    ):
        """Initialize the adapter."""
        # Import here to avoid circular imports
        from app.dependencies import get_enhanced_catalog_service

        self.catalog_service = catalog_service or get_enhanced_catalog_service()
        self.enhanced_service = enhanced_service or EnhancedXMLService(
            catalog_service=self.catalog_service,
            settings=settings
        )

        # Issue deprecation warning
        warnings.warn(
            "XMLProcessorServiceAdapter is deprecated. Use EnhancedXMLService directly.",
            DeprecationWarning,
            stacklevel=2
        )

    def resolve_urn_to_file_path(self, urn_obj):
        """Resolve URN to file path."""
        return self.catalog_service.resolve_file_path(urn_obj)

    def load_xml(self, urn_obj):
        """Load XML file based on URN."""
        document = self.enhanced_service.load_document(urn_obj)
        return document.root_element

    def extract_references(self, element, parent_ref=""):
        """Extract references from XML element."""
        # Create a temporary document to hold references
        import xml.etree.ElementTree as ET
        from app.models.xml_document import XMLDocument

        document = XMLDocument(
            file_path="",
            urn="",
            root_element=element,
            references={}
        )

        # Extract references
        self.enhanced_service._extract_references_recursive(element, document, parent_ref)

        # Return references in the expected format
        return {ref: ref_obj.element for ref, ref_obj in document.references.items()}

    def get_passage_by_reference(self, xml_root, reference):
        """Get a passage by reference."""
        # Create a temporary document
        from app.models.xml_document import XMLDocument

        document = XMLDocument(
            file_path="",
            urn="",
            root_element=xml_root,
            references={}
        )

        # Extract references
        self.enhanced_service._extract_references_recursive(xml_root, document, "")

        # Return the element for the reference
        if reference in document.references:
            return document.references[reference].element

        return None

    def get_adjacent_references(self, xml_root, current_ref):
        """Get previous and next references."""
        # Create a temporary document
        from app.models.xml_document import XMLDocument

        document = XMLDocument(
            file_path="",
            urn="",
            root_element=xml_root,
            references={}
        )

        # Extract references
        self.enhanced_service._extract_references_recursive(xml_root, document, "")

        # Get adjacent references
        import re

        # Get all reference keys
        ref_keys = list(document.references.keys())

        # If current reference not found or no references
        if not ref_keys or current_ref not in ref_keys:
            return {"prev": None, "next": None}

        # Sort references naturally
        ref_keys.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)])

        # Find current reference index
        current_idx = ref_keys.index(current_ref)

        # Get previous and next references
        prev_ref = ref_keys[current_idx - 1] if current_idx > 0 else None
        next_ref = ref_keys[current_idx + 1] if current_idx < len(ref_keys) - 1 else None

        return {"prev": prev_ref, "next": next_ref}

    def transform_to_html(self, xml_root, target_ref=None):
        """Transform XML to HTML."""
        if target_ref:
            element = self.get_passage_by_reference(xml_root, target_ref)
            if element is None:
                return f"<p>Reference '{target_ref}' not found.</p>"
        else:
            element = xml_root

        return self.enhanced_service._element_to_html(element)
```

#### 3. XMLService Tests

Create `tests/test_enhanced_xml_service.py`:

```python
import pytest
import xml.etree.ElementTree as ET
from pathlib import Path

from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService
from app.models.enhanced_urn import EnhancedURN

def test_load_document(test_settings, sample_xml_file):
    """Test loading an XML document."""
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    # Test with string URN
    document = xml_service.load_document("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert document is not None
    assert document.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
    assert document.file_path == str(sample_xml_file)

    # Test with EnhancedURN
    urn = EnhancedURN(value="urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    document = xml_service.load_document(urn)
    assert document is not None

    # Test caching
    assert "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1" in xml_service._cache

    # Test with non-existent URN
    with pytest.raises(FileNotFoundError):
        xml_service.load_document("urn:cts:greekLit:tlg0013.tlg001.perseus-grc1")

def test_extract_references(test_settings, sample_xml_file):
    """Test extracting references from an XML document."""
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    document = xml_service.load_document("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")

    # Check that references were extracted
    assert len(document.references) > 0

    # Check specific references (book and lines)
    assert "1" in document.references  # Book 1
    assert "1.1" in document.references  # Line 1 of Book 1
    assert "1.2" in document.references  # Line 2 of Book 1

    # Check parent-child relationships
    assert document.references["1"].child_refs == ["1.1", "1.2", "1.3", "1.4"]
    assert document.references["1.1"].parent_ref == "1"

def test_get_passage(test_settings, sample_xml_file):
    """Test getting a passage by reference."""
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    # Test with specific reference
    text = xml_service.get_passage(
        "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
        reference="1.1"
    )
    assert text is not None
    assert "This is line 1 of Book 1" in text

    # Test with non-existent reference
    text = xml_service.get_passage(
        "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
        reference="2.1"
    )
    assert text is None

def test_get_adjacent_references(test_settings, sample_xml_file):
    """Test getting adjacent references."""
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    # Test middle reference
    adjacent = xml_service.get_adjacent_references(
        "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
        current_ref="1.2"
    )
    assert adjacent["prev"] == "1.1"
    assert adjacent["next"] == "1.3"

    # Test first reference
    adjacent = xml_service.get_adjacent_references(
        "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
        current_ref="1"
    )
    assert adjacent["prev"] is None
    assert adjacent["next"] == "1.1"

    # Test last reference
    adjacent = xml_service.get_adjacent_references(
        "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
        current_ref="1.4"
    )
    assert adjacent["prev"] == "1.3"
    assert adjacent["next"] is None

def test_transform_to_html(test_settings, sample_xml_file):
    """Test transforming XML to HTML."""
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    # Test full document
    html = xml_service.transform_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert html is not None
    assert "<div" in html
    assert "Book 1" in html

    # Test specific reference
    html = xml_service.transform_to_html(
        "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
        reference="1.1"
    )
    assert html is not None
    assert "<span" in html
    assert "This is line 1 of Book 1" in html
```

### Phase 4: Integration and Export (Week 4)

#### 1. Update Dependencies

Update `app/dependencies.py` to include the XML service:

```python
from functools import lru_cache
import logging

from app.config import EulogosSettings
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService
from app.services.catalog_service_adapter import CatalogServiceAdapter
from app.services.xml_processor_adapter import XMLProcessorServiceAdapter

logger = logging.getLogger(__name__)

@lru_cache()
def get_settings() -> EulogosSettings:
    """Get application settings, cached for performance."""
    logger.debug("Creating EulogosSettings instance")
    return EulogosSettings()

@lru_cache()
def get_enhanced_catalog_service() -> EnhancedCatalogService:
    """Get an EnhancedCatalogService instance, cached for performance."""
    logger.debug("Creating EnhancedCatalogService instance")
    settings = get_settings()
    service = EnhancedCatalogService(settings=settings)

    # Eagerly load the catalog
    service.load_catalog()

    return service

@lru_cache()
def get_enhanced_xml_service() -> EnhancedXMLService:
    """Get an EnhancedXMLService instance, cached for performance."""
    logger.debug("Creating EnhancedXMLService instance")
    catalog_service = get_enhanced_catalog_service()
    settings = get_settings()
    return EnhancedXMLService(catalog_service=catalog_service, settings=settings)

@lru_cache()
def get_catalog_service() -> CatalogServiceAdapter:
    """Get a CatalogServiceAdapter instance for backward compatibility."""
    logger.debug("Creating CatalogServiceAdapter instance")
    enhanced_service = get_enhanced_catalog_service()
    return CatalogServiceAdapter(enhanced_service=enhanced_service)

@lru_cache()
def get_xml_processor_service() -> XMLProcessorServiceAdapter:
    """Get a XMLProcessorServiceAdapter instance for backward compatibility."""
    logger.debug("Creating XMLProcessorServiceAdapter instance")
    catalog_service = get_enhanced_catalog_service()
    xml_service = get_enhanced_xml_service()
    return XMLProcessorServiceAdapter(
        enhanced_service=xml_service,
        catalog_service=catalog_service
    )
```

#### 2. Update Reader Router

Update `app/routers/reader.py` to use the enhanced services:

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging

from app.dependencies import get_enhanced_catalog_service, get_enhanced_xml_service
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService
from app.models.enhanced_urn import EnhancedURN

logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["reader"])

@router.get("/read/{urn}", response_class=HTMLResponse, response_model=None)
async def read_text(
    request: Request,
    urn: str,
    reference: Optional[str] = None,
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
):
    """Read a text with optional reference navigation."""
    logger.info(f"Reading text: {urn}, reference: {reference}")

    # Parse URN
    try:
        urn_obj = EnhancedURN(value=urn)
    except ValueError as e:
        logger.error(f"Invalid URN format: {urn}, error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid URN: {e}")

    # Get text from catalog
    text = catalog_service.get_text_by_urn(urn)
    if not text:
        logger.error(f"Text not found: {urn}")
        raise HTTPException(status_code=404, detail=f"Text not found: {urn}")

    try:
        # Transform to HTML with reference highlighting
        html_content = xml_service.transform_to_html(urn, reference)

        # Get adjacent references for navigation
        adjacent_refs = {"prev": None, "next": None}
        if reference:
            adjacent_refs = xml_service.get_adjacent_references(urn, reference)

        # Render template
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "content": html_content,
                "urn": urn,
                "current_ref": reference,
                "prev_ref": adjacent_refs["prev"],
                "next_ref": adjacent_refs["next"],
            },
        )
    except Exception as e:
        logger.error(f"Error processing text: {urn}, error: {e}")
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "content": f"<div class='error'><p>Error processing text: {str(e)}</p></div>",
                "urn": urn,
            },
            status_code=500,
        )

@router.get("/api/references/{urn}", response_class=HTMLResponse, response_model=None)
async def get_references(
    urn: str,
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service)
):
    """Get references for a text."""
    logger.info(f"Getting references for: {urn}")

    try:
        # Load document
        document = xml_service.load_document(urn)

        # Get all references
        references = document.references

        # Sort references naturally
        import re
        sorted_refs = sorted(
            references.keys(),
            key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
        )

        # Build HTML
        html = ['<ul class="space-y-1">']

        for ref in sorted_refs:
            html.append('<li class="hover:bg-gray-100 rounded">')
            html.append(f'<a href="/read/{urn}?reference={ref}" class="block px-2 py-1">')
            html.append(f'<span class="font-medium">{ref}</span>')
            html.append('</a>')
            html.append('</li>')

        html.append('</ul>')

        return HTMLResponse(content="".join(html))

    except Exception as e:
        logger.error(f"Error loading references for {urn}: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error loading references: {str(e)}</div>',
            status_code=500
        )
```

#### 3. Update Export Service

Create `app/services/enhanced_export_service.py`:

```python
import tempfile
from pathlib import Path
from typing import Dict, Optional, Any, Union
import logging
import re
import os

from app.models.enhanced_urn import EnhancedURN
from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService
from app.config import EulogosSettings

logger = logging.getLogger(__name__)

class EnhancedExportService:
    """Service for exporting texts in various formats."""

    def __init__(
        self,
        catalog_service: EnhancedCatalogService,
        xml_service: EnhancedXMLService,
        settings: Optional[EulogosSettings] = None,
        output_dir: Optional[str] = None
    ):
        """Initialize the export service."""
        self.catalog_service = catalog_service
        self.xml_service = xml_service
        self.settings = settings or EulogosSettings()
        self.output_dir = output_dir or tempfile.gettempdir()

    def export_to_html(self, urn: Union[str, EnhancedURN], options: Dict[str, Any] = None) -> Path:
        """Export text to standalone HTML.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated HTML file
        """
        options = options or {}

        # Get metadata
        metadata = self._get_metadata(urn)

        # Get HTML content
        html_content = self.xml_service.transform_to_html(urn, options.get("reference"))

        # Add HTML boilerplate
        standalone_html = [
            "<!DOCTYPE html>",
            '<html lang="grc">',
            "<head>",
            f"<title>{metadata.get('title', 'Untitled')}</title>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "<style>",
            self._get_html_css(options),
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{metadata.get('title', 'Untitled')}</h1>",
        ]

        # Add creators if available
        if metadata.get("creators"):
            standalone_html.append("<h2>By " + ", ".join(metadata.get("creators", [])) + "</h2>")

        # Add content
        standalone_html.append(html_content)

        # Close HTML
        standalone_html.extend(["</body>", "</html>"])

        # Define output HTML path
        html_path = self._get_output_path(urn, "html", options)

        # Write HTML file
        with open(html_path, "w", encoding="utf-8") as f:
            f.write("\n".join(standalone_html))

        return Path(html_path)

    def export_to_markdown(self, urn: Union[str, EnhancedURN], options: Dict[str, Any] = None) -> Path:
        """Export text to Markdown.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated Markdown file
        """
        try:
            import html2text
        except ImportError:
            logger.error("html2text is required for Markdown export")
            raise ImportError("html2text is required for Markdown export. Install with: pip install html2text")

        options = options or {}

        # Get HTML content
        html_content = self.xml_service.transform_to_html(urn, options.get("reference"))

        # Convert HTML to Markdown
        h2t = html2text.HTML2Text()
        h2t.unicode_snob = True  # Preserve unicode characters
        h2t.body_width = 0  # No wrapping
        markdown_content = h2t.handle(html_content)

        # Get metadata
        metadata = self._get_metadata(urn)

        # Add title and metadata
        if options.get("include_metadata", True):
            markdown_header = f"# {metadata.get('title', 'Untitled')}\n\n"
            if metadata.get("creators"):
                markdown_header += "By " + ", ".join(metadata.get("creators", [])) + "\n\n"
            markdown_content = markdown_header + markdown_content

        # Define output Markdown path
        md_path = self._get_output_path(urn, "md", options)

        # Write Markdown file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return Path(md_path)

    def export_to_latex(self, urn: Union[str, EnhancedURN], options: Dict[str, Any] = None) -> Path:
        """Export text to LaTeX.

        Args:
            urn: URN of the text to export
            options: Dictionary of export options

        Returns:
            Path to the generated LaTeX file
        """
        options = options or {}

        # Get metadata
        metadata = self._get_metadata(urn)

        # Start building LaTeX document
        latex_content = [
            "\\documentclass{article}",
            "\\usepackage{fontspec}",
            "\\usepackage{polyglossia}",
            "\\setmainlanguage{english}",
            "\\setotherlanguage{greek}",
            "\\setmainfont{Times New Roman}",
            "\\newfontfamily\\greekfont[Script=Greek]{Times New Roman}",
            f"\\title{{{metadata.get('title', 'Untitled')}}}",
        ]

        # Add authors if available
        if metadata.get("creators"):
            latex_content.append(f"\\author{{{' \\and '.join(metadata.get('creators', []))}}}")

        # Begin document
        latex_content.extend([
            "\\begin{document}",
            "\\maketitle",
        ])

        # Load document
        document = self.xml_service.load_document(urn)

        # If reference specified, limit to that section
        if options.get("reference") and options.get("reference") in document.references:
            root = document.references[options.get("reference")].element
        else:
            root = document.root_element

        # Sort references in document
        import re
        sorted_refs = sorted(
            document.references.keys(),
            key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
        )

        # Process sections
        if options.get("reference"):
            # Just process the specified reference
            reference = options.get("reference")
            ref_obj = document.references.get(reference)
            if ref_obj:
                text = ref_obj.text_content
                latex_content.append(f"\\section*{{Section {reference}}}")
                latex_content.append(self._clean_for_latex(text))
                latex_content.append("")
        else:
            # Process all references
            for ref in sorted_refs:
                ref_obj = document.references[ref]

                # Skip if it has a parent (to avoid duplicate content)
                if ref_obj.parent_ref:
                    continue

                # Add section heading
                heading_level = len(ref.split("."))
                if heading_level == 1:
                    latex_content.append(f"\\section*{{Section {ref}}}")
                elif heading_level == 2:
                    latex_content.append(f"\\subsection*{{Section {ref}}}")
                else:
                    latex_content.append(f"\\subsubsection*{{Section {ref}}}")

                # Add text content
                text = ref_obj.text_content
                if text:
                    latex_content.append(self._clean_for_latex(text))
                    latex_content.append("")  # Empty line

        # End document
        latex_content.append("\\end{document}")

        # Define output LaTeX path
        latex_path = self._get_output_path(urn, "tex", options)

        # Write LaTeX file
        with open(latex_path, "w", encoding="utf-8") as f:
            f.write("\n".join(latex_content))

        return Path(latex_path)

    def _get_metadata(self, urn: Union[str, EnhancedURN]) -> Dict[str, Any]:
        """Get metadata for export.

        Args:
            urn: URN of the text

        Returns:
            Dictionary of metadata
        """
        # Get text metadata from catalog
        text = self.catalog_service.get_text_by_urn(urn)

        # Parse URN to get components
        if isinstance(urn, EnhancedURN):
            urn_obj = urn
        else:
            urn_obj = EnhancedURN(value=str(urn))

        # Get author information
        author = None
        if urn_obj.textgroup:
            author_id = urn_obj.textgroup
            authors = self.catalog_service.get_authors()
            for a in authors:
                if a.id == author_id:
                    author = a
                    break

        # Build metadata
        metadata = {
            "title": getattr(text, "work_name", f"Text {urn_obj.textgroup}.{urn_obj.work}"),
            "creators": [getattr(author, "name", "Unknown Author")] if author else [],
            "language": getattr(text, "language", "grc"),
            "urn": str(urn_obj.value),
        }

        # Try to load document to get more metadata
        try:
            document = self.xml_service.load_document(urn_obj)

            # Add document metadata
            if "title" in document.metadata and document.metadata["title"]:
                metadata["title"] = document.metadata["title"]

            if "editor" in document.metadata and document.metadata["editor"]:
                metadata["editor"] = document.metadata["editor"]

            if "translator" in document.metadata and document.metadata["translator"]:
                metadata["translator"] = document.metadata["translator"]

            if "language" in document.metadata and document.metadata["language"]:
                metadata["language"] = document.metadata["language"]

            # Add translator and editor to creators if available
            if "translator" in metadata:
                metadata["creators"].append(f"{metadata['translator']} (trans.)")

            if "editor" in metadata and metadata.get("editor") != metadata.get("translator"):
                metadata["creators"].append(f"{metadata['editor']} (ed.)")
        except Exception as e:
            logger.warning(f"Error loading document metadata: {e}")

        return metadata

    def _get_output_path(self, urn: Union[str, EnhancedURN], extension: str, options: Dict[str, Any] = None) -> str:
        """Get output path for export.

        Args:
            urn: URN of the text
            extension: File extension (without dot)
            options: Dictionary of export options

        Returns:
            Path as string
        """
        options = options or {}

        # Convert URN to EnhancedURN if needed
        if not isinstance(urn, EnhancedURN):
            urn_obj = EnhancedURN(value=str(urn))
        else:
            urn_obj = urn

        # Use custom filename if provided
        if options.get("filename"):
            filename = options.get("filename")
            if not filename.endswith(f".{extension}"):
                filename = f"{filename}.{extension}"
        else:
            # Generate filename from URN
            filename = f"{urn_obj.textgroup}_{urn_obj.work}_{urn_obj.version}.{extension}"

        # Custom output directory or default
        output_dir = options.get("output_dir", self.output_dir)

        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        return os.path.join(output_dir, filename)

    def _get_html_css(self, options: Dict[str, Any] = None) -> str:
        """Get CSS for HTML export.

        Args:
            options: Dictionary of export options

        Returns:
            CSS as string
        """
        options = options or {}

        css = """
        body {
            font-family: "Times New Roman", Times, serif;
            font-size: 16px;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 1em;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: "Times New Roman", Times, serif;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        .reference {
            margin-bottom: 1em;
            position: relative;
        }
        [data-n] {
            font-weight: bold;
            margin-right: 0.5em;
            display: inline-block;
        }
        .line {
            display: block;
            margin-left: 2em;
        }
        """

        # Add custom CSS if provided
        if options.get("custom_css"):
            css += options.get("custom_css")

        return css

    def _clean_for_latex(self, text: str) -> str:
        """Clean text for LaTeX.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Replace LaTeX special characters
        replacements = {
            "&": "\\&",
            "%": "\\%",
            "$": "\\$",
            "#": "\\#",
            "_": "\\_",
            "{": "\\{",
            "}": "\\}",
            "~": "\\textasciitilde{}",
            "^": "\\textasciicircum{}",
            "\\": "\\textbackslash{}",
            "<": "\\textless{}",
            ">": "\\textgreater{}"
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        # Handle Greek text
        # Simplified approach: wrap all text in textgreek as it's a Greek text
        if re.search(r'[Α-Ωα-ω]', text):
            return f"\\textgreek{{{text}}}"

        return text
```

#### 4. Integration Tests

Create `tests/test_integration.py`:

```python
import pytest
from pathlib import Path
import tempfile
import os

from app.services.enhanced_catalog_service import EnhancedCatalogService
from app.services.enhanced_xml_service import EnhancedXMLService
from app.services.enhanced_export_service import EnhancedExportService
from app.models.enhanced_urn import EnhancedURN

def test_end_to_end_export(test_settings, sample_xml_file):
    """Test an end-to-end export workflow."""
    # Set up services
    catalog_service = EnhancedCatalogService(settings=test_settings)
    xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)

    # Create temporary directory for exports
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up export service
        export_service = EnhancedExportService(
            catalog_service=catalog_service,
            xml_service=xml_service,
            settings=test_settings,
            output_dir=temp_dir
        )

        # Export to different formats
        html_path = export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        md_path = export_service.export_to_markdown("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
        latex_path = export_service.export_to_latex("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")

        # Verify files exist
        assert html_path.exists()
        assert md_path.exists()
        assert latex_path.exists()

        # Verify file contents
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            assert "<!DOCTYPE html>" in html_content
            assert "Homeri Ilias" in html_content
            assert "Book 1" in html_content

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            assert "# Homeri Ilias" in md_content
            assert "Book 1" in md_content

        with open(latex_path, "r", encoding="utf-8") as f:
            latex_content = f.read()
            assert "\\documentclass{article}" in latex_content
            assert "Homeri Ilias" in latex_content
            assert "\\section" in latex_content

def test_backward_compatibility(test_settings, sample_xml_file):
    """Test backward compatibility with existing code."""
    from app.services.catalog_service_adapter import CatalogServiceAdapter
    from app.services.xml_processor_adapter import XMLProcessorServiceAdapter

    # Set up services
    enhanced_catalog_service = EnhancedCatalogService(settings=test_settings)
    enhanced_xml_service = EnhancedXMLService(
        catalog_service=enhanced_catalog_service,
        settings=test_settings
    )

    # Create adapters
    catalog_adapter = CatalogServiceAdapter(enhanced_service=enhanced_catalog_service)
    xml_adapter = XMLProcessorServiceAdapter(
        enhanced_service=enhanced_xml_service,
        catalog_service=enhanced_catalog_service
    )

    # Use adapter methods
    # Test catalog adapter
    text = catalog_adapter.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert text is not None
    assert text.urn == "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"

    # Test XML adapter
    root = xml_adapter.load_xml("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
    assert root is not None

    # Test reference extraction
    refs = xml_adapter.extract_references(root)
    assert refs is not None
    assert len(refs) > 0

    # Test HTML transformation
    html = xml_adapter.transform_to_html(root)
    assert html is not None
    assert "Book 1" in html
```

### Phase 5: Documentation and Implementation Guide (Week 5)

#### 1. API Documentation

Create `docs/API.md`:

```markdown
# Eulogos API Documentation

## Core Services

### EnhancedCatalogService

The `EnhancedCatalogService` provides access to the integrated catalog data. It uses the `integrated_catalog.json` file as the single source of truth for all text metadata.

#### Key Methods

- `load_catalog(force_reload=False)` - Load the catalog from file
- `get_text_by_urn(urn)` - Get a text by URN
- `get_path_by_urn(urn)` - Get the file path for a text by URN
- `resolve_file_path(urn)` - Resolve a URN to a full file path
- `get_authors(include_archived=False)` - Get all authors
- `get_texts_by_author(author_id, include_archived=False)` - Get all texts by an author
- `validate_path_consistency()` - Validate that all URNs have valid paths
- `archive_text(urn, archive=True)` - Archive or unarchive a text
- `toggle_favorite(urn)` - Toggle favorite status for a text

### EnhancedXMLService

The `EnhancedXMLService` handles XML document processing. It uses the `EnhancedCatalogService` for path resolution and implements caching for performance.

#### Key Methods

- `load_document(urn)` - Load an XML document by URN
- `get_passage(urn, reference=None)` - Get a passage from an XML document
- `transform_to_html(urn, reference=None)` - Transform a passage to HTML
- `get_adjacent_references(urn, current_ref)` - Get previous and next references

### EnhancedExportService

The `EnhancedExportService` provides export functionality for various formats. It uses the `EnhancedCatalogService` and `EnhancedXMLService` to access and process texts.

#### Key Methods

- `export_to_html(urn, options=None)` - Export text to HTML
- `export_to_markdown(urn, options=None)` - Export text to Markdown
- `export_to_latex(urn, options=None)` - Export text to LaTeX

## Compatibility Adapters

### CatalogServiceAdapter

A compatibility adapter for the old `CatalogService` interface. It delegates to `EnhancedCatalogService` while maintaining the old interface.

### XMLProcessorServiceAdapter

A compatibility adapter for the old `XMLProcessorService` interface. It delegates to `EnhancedXMLService` while maintaining the old interface.

## Models

### EnhancedURN

Enhanced Pydantic model for CTS URNs. It provides methods for parsing, validating, and manipulating URNs.

#### Key Methods

- `parse()` - Parse the URN string into components
- `is_valid_for_path()` - Check if the URN has all components needed for path resolution
- `get_file_path(base_dir="data")` - Derive file path from URN components

### Catalog Models

- `TextVersion` - Represents a version of a text (edition or translation)
- `Work` - Represents a work with editions and translations
- `Author` - Represents an author with works
- `Catalog` - Represents the entire catalog

### XML Document Models

- `XMLReference` - Represents a reference to a section in an XML document
- `XMLDocument` - Represents a parsed XML document with references

## Configuration

The `EulogosSettings` class provides configuration for the application. It supports environment variables with the `EULOGOS_` prefix and a `.env` file.

### Key Settings

- `catalog_path` - Path to the integrated catalog JSON file
- `data_dir` - Base directory for text data files
- `xml_cache_size` - Maximum number of XML documents to cache
- `enable_caching` - Enable caching for XML documents
- `compatibility_mode` - Enable compatibility with existing code
```

#### 2. Implementation Guide

Create `docs/Implementation.md`:

```markdown
# Eulogos Implementation Guide

## Core Architecture

The Eulogos XML processing system follows a clean, modular architecture with the following components:

1. **Configuration Management** - Centralized configuration with Pydantic settings
2. **Catalog Models** - Represent catalog data with Pydantic models
3. **XML Document Models** - Represent parsed XML documents and references
4. **EnhancedCatalogService** - Provides access to the integrated catalog
5. **EnhancedXMLService** - Handles XML document processing
6. **EnhancedExportService** - Provides export functionality
7. **Compatibility Adapters** - Maintain backward compatibility

## Key Architectural Principles

1. **Single Source of Truth** - The integrated_catalog.json file is the sole source of truth for all text metadata and file paths.
2. **Separation of Concerns** - Clear separation between catalog data management and XML processing.
3. **Efficient Caching** - XML documents are cached for performance.
4. **Error Handling** - Comprehensive error handling with detailed logging.
5. **Type Safety** - Strong typing with Pydantic models.
6. **Backward Compatibility** - Compatibility adapters for gradual migration.

## Implementation Details

### Configuration Management

```python
from app.config import EulogosSettings

# Get settings from environment variables or .env file
settings = EulogosSettings()

# Override specific settings
settings = EulogosSettings(
    catalog_path="custom_catalog.json",
    data_dir="custom_data",
    xml_cache_size=50
)
```

### Catalog Processing

```python
from app.services.enhanced_catalog_service import EnhancedCatalogService

# Create service
catalog_service = EnhancedCatalogService(settings=settings)

# Load catalog
catalog = catalog_service.load_catalog()

# Get text by URN
text = catalog_service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")

# Get authors
authors = catalog_service.get_authors(include_archived=False)

# Resolve file path
file_path = catalog_service.resolve_file_path("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
```

### XML Processing

```python
from app.services.enhanced_xml_service import EnhancedXMLService

# Create service
xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=settings)

# Load document
document = xml_service.load_document("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")

# Get passage by reference
text = xml_service.get_passage("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1", reference="1.1")

# Transform to HTML
html = xml_service.transform_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1", reference="1.1")

# Get adjacent references
adjacent = xml_service.get_adjacent_references("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1", current_ref="1.1")
```

### Export Functionality

```python
from app.services.enhanced_export_service import EnhancedExportService

# Create service
export_service = EnhancedExportService(
    catalog_service=catalog_service,
    xml_service=xml_service,
    settings=settings,
    output_dir="exports"
)

# Export to different formats
html_path = export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
md_path = export_service.export_to_markdown("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
latex_path = export_service.export_to_latex("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")

# Export with options
options = {
    "reference": "1.1",
    "filename": "iliad_book1",
    "include_metadata": True,
    "custom_css": "body { font-size: 14px; }"
}
html_path = export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1", options=options)
```

### Using Dependency Injection

```python
from fastapi import Depends
from app.dependencies import get_enhanced_catalog_service, get_enhanced_xml_service

@app.get("/api/text/{urn}")
async def get_text(
    urn: str,
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service)
):
    text = catalog_service.get_text_by_urn(urn)
    document = xml_service.load_document(urn)
    return {"text": text, "content": xml_service.get_passage(urn)}
```

### Using Compatibility Adapters

```python
from app.services.catalog_service_adapter import CatalogServiceAdapter
from app.services.xml_processor_adapter import XMLProcessorServiceAdapter

# Create adapters
catalog_adapter = CatalogServiceAdapter(enhanced_service=catalog_service)
xml_adapter = XMLProcessorServiceAdapter(
    enhanced_service=xml_service,
    catalog_service=catalog_service
)

# Use with existing code
text = catalog_adapter.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
root = xml_adapter.load_xml("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
html = xml_adapter.transform_to_html(root)
```

## Performance Optimization

1. **Caching** - XML documents are cached to avoid repeated parsing:
   ```python
   # Configure cache size
   settings = EulogosSettings(xml_cache_size=100)

   # Disable caching if needed
   settings = EulogosSettings(enable_caching=False)
   ```

2. **Indexes** - Catalog data is indexed for efficient lookups:
   ```python
   # The service automatically builds indexes
   catalog_service = EnhancedCatalogService(settings=settings)
   catalog_service.load_catalog()

   # These indexes are used internally
   text_path = catalog_service._text_path_by_urn.get(urn)
   texts = catalog_service._texts_by_author.get(author_id, [])
   ```

3. **Lazy Loading** - Optional future enhancement for large catalogs:
   ```python
   # Enable lazy loading
   settings = EulogosSettings(lazy_loading=True)
   ```

## Error Handling

1. **Comprehensive Logging**:
   ```python
   import logging
   from app.utils.logging import setup_logging

   # Set up logging
   logger = setup_logging(log_level="INFO", log_file="logs/eulogos.log")

   # Log messages at different levels
   logger.debug("Debug message")
   logger.info("Info message")
   logger.warning("Warning message")
   logger.error("Error message")
   ```

2. **Exception Handling**:
   ```python
   try:
       document = xml_service.load_document(urn)
   except FileNotFoundError:
       logger.error(f"XML file not found for {urn}")
       return {"error": "File not found"}
   except ValueError:
       logger.error(f"Invalid URN format: {urn}")
       return {"error": "Invalid URN"}
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       return {"error": "An unexpected error occurred"}
   ```

## Testing

1. **Unit Tests**:
   ```python
   def test_load_catalog(test_settings, sample_catalog_file):
       service = EnhancedCatalogService(settings=test_settings)
       catalog = service.load_catalog()
       assert catalog is not None
       assert len(catalog.authors) == 1
   ```

2. **Integration Tests**:
   ```python
   def test_end_to_end_export(test_settings, sample_xml_file):
       catalog_service = EnhancedCatalogService(settings=test_settings)
       xml_service = EnhancedXMLService(catalog_service=catalog_service, settings=test_settings)
       export_service = EnhancedExportService(
           catalog_service=catalog_service,
           xml_service=xml_service,
           settings=test_settings,
           output_dir=temp_dir
       )

       html_path = export_service.export_to_html("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
       assert html_path.exists()
   ```

## Migration Guide

### Phase 1: Start Using Enhanced Services

1. Set up dependencies:
   ```python
   # app/dependencies.py
   @lru_cache()
   def get_enhanced_catalog_service() -> EnhancedCatalogService:
       return EnhancedCatalogService()

   @lru_cache()
   def get_enhanced_xml_service() -> EnhancedXMLService:
       catalog_service = get_enhanced_catalog_service()
       return EnhancedXMLService(catalog_service=catalog_service)
   ```

2. Update new endpoints to use enhanced services:
   ```python
   @router.get("/api/v2/text/{urn}")
   async def get_text_v2(
       urn: str,
       catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
       xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service)
   ):
       # Use enhanced services
   ```

### Phase 2: Use Compatibility Adapters

1. Set up adapter dependencies:
   ```python
   @lru_cache()
   def get_catalog_service() -> CatalogServiceAdapter:
       enhanced_service = get_enhanced_catalog_service()
       return CatalogServiceAdapter(enhanced_service=enhanced_service)

   @lru_cache()
   def get_xml_processor_service() -> XMLProcessorServiceAdapter:
       catalog_service = get_enhanced_catalog_service()
       xml_service = get_enhanced_xml_service()
       return XMLProcessorServiceAdapter(
           enhanced_service=xml_service,
           catalog_service=catalog_service
       )
   ```

2. Update existing endpoints to use adapters:
   ```python
   @router.get("/api/text/{urn}")
   async def get_text(
       urn: str,
       catalog_service: CatalogServiceAdapter = Depends(get_catalog_service),
       xml_processor: XMLProcessorServiceAdapter = Depends(get_xml_processor_service)
   ):
       # Existing code remains unchanged
   ```

### Phase 3: Complete Migration

1. Update all endpoints to use enhanced services directly
2. Remove compatibility adapters
3. Update configuration:
   ```python
   # Disable compatibility mode
   settings = EulogosSettings(compatibility_mode=False)
   ```
```

## Project Timeline

This revised implementation plan will be completed in a 5-week timeline:

### Week 1: Core Models and Infrastructure
- Create enhanced catalog and XML document models
- Implement EnhancedURN model with backward compatibility
- Set up configuration with EulogosSettings
- Implement logging framework
- Create test infrastructure

### Week 2: CatalogService Enhancement
- Implement EnhancedCatalogService
- Create CatalogServiceAdapter for backward compatibility
- Add efficient indexing for path resolution
- Implement caching and validation

### Week 3: XMLService Implementation
- Implement EnhancedXMLService
- Create XMLProcessorServiceAdapter for backward compatibility
- Add reference extraction and HTML transformation
- Implement caching for XML documents

### Week 4: Integration and Export
- Integrate services with dependencies
- Implement EnhancedExportService
- Update router files
- Create integration tests

### Week 5: Documentation and Implementation Guide
- Create comprehensive API documentation
- Write detailed implementation guide
- Finalize tests and fix any issues
- Create migration guide for existing code

This plan maintains all the architectural improvements while providing backward compatibility for a smooth transition from the existing system.
