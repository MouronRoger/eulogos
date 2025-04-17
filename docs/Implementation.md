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

## Performance Benchmarking

When migrating from the old to the new system, it's important to benchmark performance to ensure the new system is at least as fast as the old one. Here's a simple way to benchmark:

```python
import time

# Benchmark old service
start_time = time.time()
for i in range(100):
    old_service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
old_duration = time.time() - start_time

# Benchmark new service
start_time = time.time()
for i in range(100):
    enhanced_service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
new_duration = time.time() - start_time

print(f"Old service: {old_duration:.4f}s")
print(f"New service: {new_duration:.4f}s")
print(f"Performance difference: {(old_duration/new_duration - 1)*100:.2f}%")
```

## Troubleshooting Common Issues

### Missing Catalog Path

**Issue**: `FileNotFoundError: Catalog file not found`

**Solution**:
```python
# Check if catalog path exists
if not os.path.exists(settings.catalog_path):
    # Create default catalog
    create_default_catalog(settings.catalog_path)
```

### Invalid URN Format

**Issue**: `ValueError: Invalid URN format`

**Solution**:
```python
# Validate URN before use
try:
    urn_obj = EnhancedURN(value=urn)
except ValueError:
    # Handle invalid URN
    return {"error": "Invalid URN format"}
```

### XML File Not Found

**Issue**: `FileNotFoundError: XML file not found`

**Solution**:
```python
# Check path validity before access
file_path = catalog_service.resolve_file_path(urn)
if not file_path or not file_path.exists():
    # Handle missing file
    return {"error": "XML file not found"}
```

### Caching Issues

**Issue**: Memory usage grows too large with caching

**Solution**:
```python
# Adjust cache size based on available memory
settings = EulogosSettings(xml_cache_size=50)
```

## Future Enhancements

1. **Lazy Loading** - Implement lazy loading for large catalogs
2. **Background Processing** - Add background tasks for long-running operations
3. **WebSocket Updates** - Real-time updates for catalog changes
4. **Advanced Caching** - Implement multi-level caching with Redis
5. **Custom Error Pages** - Improve error handling with custom error pages
6. **API Rate Limiting** - Add rate limiting for API endpoints
7. **Comprehensive Metrics** - Add metrics for performance monitoring
