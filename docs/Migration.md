# Eulogos XML Processing Migration Guide

This guide outlines a step-by-step approach for migrating from the original XML processing architecture to the new enhanced architecture with `integrated_catalog.json` as the single source of truth.

## Migration Overview

The migration is designed to be gradual, with built-in compatibility features that allow the old and new systems to coexist during the transition. The process involves these key phases:

1. **Preparation**: Understand the new architecture and set up necessary components
2. **Gradual Transition**: Migrate code in stages using compatibility adapters
3. **Complete Adoption**: Fully transition to the new architecture and remove compatibility layers

## Key Benefits of Migration

1. **Single Source of Truth**: Consistent catalog data across all components
2. **Improved Performance**: Efficient caching and indexing
3. **Better Error Handling**: Comprehensive logging and error management
4. **Type Safety**: Strong typing with Pydantic models
5. **Cleaner Architecture**: Clear separation of concerns and modular design

## Detailed Migration Steps

### Phase 1: Preparation

1. **Review New Architecture**
   - Understand the enhanced models, services, and their relationships
   - Familiarize yourself with the new configuration system

2. **Set Up Dependencies**
   - Add the new dependencies to `app/dependencies.py`:
   ```python
   from functools import lru_cache
   from app.config import EulogosSettings
   from app.services.enhanced_catalog_service import EnhancedCatalogService
   from app.services.enhanced_xml_service import EnhancedXMLService
   from app.services.enhanced_export_service import EnhancedExportService

   @lru_cache()
   def get_settings() -> EulogosSettings:
       return EulogosSettings()

   @lru_cache()
   def get_enhanced_catalog_service() -> EnhancedCatalogService:
       settings = get_settings()
       service = EnhancedCatalogService(settings=settings)
       service.load_catalog()
       return service

   @lru_cache()
   def get_enhanced_xml_service() -> EnhancedXMLService:
       catalog_service = get_enhanced_catalog_service()
       settings = get_settings()
       return EnhancedXMLService(catalog_service=catalog_service, settings=settings)

   @lru_cache()
   def get_enhanced_export_service() -> EnhancedExportService:
       catalog_service = get_enhanced_catalog_service()
       xml_service = get_enhanced_xml_service()
       settings = get_settings()
       return EnhancedExportService(
           catalog_service=catalog_service,
           xml_service=xml_service,
           settings=settings
       )
   ```

3. **Generate Initial Integrated Catalog**
   - Create the initial `integrated_catalog.json` from existing catalog data:
   ```python
   from app.services.catalog_service import CatalogService
   from app.models.enhanced_catalog import Catalog, Author, Work, TextVersion
   import json

   def generate_integrated_catalog():
       # Load data from existing catalog service
       old_service = CatalogService()
       old_catalog = old_service.load_catalog()

       # Create new catalog structure
       new_catalog = Catalog()

       # Convert data
       for old_author in old_service.get_authors():
           author = Author(
               id=old_author.id,
               name=old_author.name,
               century=getattr(old_author, "century", None),
               type=getattr(old_author, "type", None)
           )

           texts = old_service.get_texts_by_author(old_author.id, include_archived=True)
           for text in texts:
               # Extract work ID from URN
               urn_parts = text.urn.split(":")
               if len(urn_parts) >= 4:
                   id_parts = urn_parts[3].split(".")
                   if len(id_parts) >= 2:
                       work_id = id_parts[1]

                       # Create work if not exists
                       if work_id not in author.works:
                           author.works[work_id] = Work(
                               id=work_id,
                               title=text.work_name,
                               urn=f"urn:cts:{urn_parts[2]}:{id_parts[0]}.{work_id}",
                               language=text.language
                           )

                       # Add text as edition or translation
                       text_version = TextVersion(
                           urn=text.urn,
                           label=getattr(text, "label", text.work_name),
                           description=getattr(text, "description", None),
                           language=text.language,
                           path=text.path,
                           word_count=getattr(text, "wordcount", 0),
                           archived=getattr(text, "archived", False),
                           favorite=getattr(text, "favorite", False)
                       )

                       # Determine if edition or translation based on language
                       if text.language == author.works[work_id].language:
                           author.works[work_id].editions[id_parts[2]] = text_version
                       else:
                           author.works[work_id].translations[id_parts[2]] = text_version

           # Add author to catalog
           new_catalog.authors[author.id] = author

       # Update statistics
       new_catalog.statistics.author_count = len(new_catalog.authors)

       work_count = 0
       edition_count = 0
       translation_count = 0
       greek_word_count = 0
       latin_word_count = 0
       arabic_word_count = 0

       for author in new_catalog.authors.values():
           work_count += len(author.works)

           for work in author.works.values():
               edition_count += len(work.editions)
               translation_count += len(work.translations)

               # Calculate word counts by language
               for edition in work.editions.values():
                   if edition.language == "grc":
                       greek_word_count += edition.word_count
                   elif edition.language == "lat":
                       latin_word_count += edition.word_count
                   elif edition.language == "ara":
                       arabic_word_count += edition.word_count

       new_catalog.statistics.work_count = work_count
       new_catalog.statistics.edition_count = edition_count
       new_catalog.statistics.translation_count = translation_count
       new_catalog.statistics.greek_word_count = greek_word_count
       new_catalog.statistics.latin_word_count = latin_word_count
       new_catalog.statistics.arabic_word_count = arabic_word_count

       # Save to integrated catalog file
       with open("integrated_catalog.json", "w", encoding="utf-8") as f:
           json.dump(new_catalog.model_dump(), f, indent=2, ensure_ascii=False)

       print(f"Generated integrated catalog with {new_catalog.statistics.author_count} authors, {work_count} works")

   if __name__ == "__main__":
       generate_integrated_catalog()
   ```

4. **Validate Integrated Catalog**
   - Run validation to ensure all paths in the catalog are valid:
   ```python
   from app.services.enhanced_catalog_service import EnhancedCatalogService

   catalog_service = EnhancedCatalogService()
   results = catalog_service.validate_path_consistency()

   print(f"Total URNs: {results['total_urns']}")
   print(f"URNs with path: {results['urns_with_path']}")
   print(f"URNs without path: {results['urns_without_path']}")
   print(f"Existing files: {results['existing_files']}")
   print(f"Missing files: {results['missing_files']}")

   if results['missing_files'] > 0:
       print("Missing files:")
       for urn, path in results['missing_files_list']:
           print(f"  {urn}: {path}")
   ```

### Phase 2: Configure Compatibility Adapters

1. **Add Adapter Dependencies**
   - Add these to `app/dependencies.py`:
   ```python
   from app.services.catalog_service_adapter import CatalogServiceAdapter
   from app.services.xml_processor_adapter import XMLProcessorServiceAdapter

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

2. **Verify Adapter Compatibility**
   - Create tests to verify that the adapters behave identically to the original services:
   ```python
   # tests/test_adapter_compatibility.py

   def test_catalog_adapter_compatibility():
       # Create original service
       from app.services.catalog_service import CatalogService
       original = CatalogService()
       original.load_catalog()

       # Create adapter
       from app.services.catalog_service_adapter import CatalogServiceAdapter
       from app.services.enhanced_catalog_service import EnhancedCatalogService
       enhanced = EnhancedCatalogService()
       adapter = CatalogServiceAdapter(enhanced_service=enhanced)

       # Test get_authors
       original_authors = original.get_authors()
       adapter_authors = adapter.get_authors()
       assert len(original_authors) == len(adapter_authors)

       # Test get_text_by_urn
       urn = "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
       original_text = original.get_text_by_urn(urn)
       adapter_text = adapter.get_text_by_urn(urn)

       assert original_text.urn == adapter_text.urn
       assert original_text.language == adapter_text.language
   ```

### Phase 3: Migrate Individual Components

1. **Create Dual Routes for Testing**
   - Create new API routes using enhanced services in parallel with existing routes:
   ```python
   # app/routers/enhanced_reader.py
   from fastapi import APIRouter, Depends, HTTPException

   from app.services.enhanced_catalog_service import EnhancedCatalogService
   from app.services.enhanced_xml_service import EnhancedXMLService
   from app.dependencies import get_enhanced_catalog_service, get_enhanced_xml_service

   router = APIRouter(prefix="/v2", tags=["enhanced_reader"])

   @router.get("/read/{urn}")
   async def read_text_v2(
       urn: str,
       reference: Optional[str] = None,
       catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service),
       xml_service: EnhancedXMLService = Depends(get_enhanced_xml_service),
   ):
       """Enhanced text reader endpoint."""
       # Implementation using enhanced services
   ```

2. **Update Common Components**
   - Modify shared components to work with both old and new services:
   ```python
   # app/templates/reader.html
   {% if enhanced %}
       <!-- Display using enhanced data structure -->
   {% else %}
       <!-- Display using original data structure -->
   {% endif %}
   ```

3. **Compare Performance**
   - Create benchmark scripts to compare performance between old and new implementations:
   ```python
   # scripts/benchmark.py
   import time
   from app.services.catalog_service import CatalogService
   from app.services.enhanced_catalog_service import EnhancedCatalogService

   def benchmark_catalog_service():
       # Test old service
       old_service = CatalogService()
       start = time.time()
       old_service.load_catalog()
       old_load_time = time.time() - start

       # Test new service
       new_service = EnhancedCatalogService()
       start = time.time()
       new_service.load_catalog()
       new_load_time = time.time() - start

       print(f"Catalog Load - Old: {old_load_time:.4f}s, New: {new_load_time:.4f}s")
       print(f"Improvement: {(old_load_time/new_load_time - 1)*100:.2f}%")
   ```

### Phase 4: Transition API Endpoints

1. **Update Imports and Dependencies**
   - Replace old imports with adapter imports in existing code:
   ```python
   # Before
   from app.services.catalog_service import CatalogService
   from app.services.xml_processor_service import XMLProcessorService

   # After
   from app.dependencies import get_catalog_service, get_xml_processor_service
   ```

2. **Update Dependency Injection**
   - Replace direct instantiation with dependency injection:
   ```python
   # Before
   @router.get("/read/{urn}")
   async def read_text(urn: str, reference: Optional[str] = None):
       catalog_service = CatalogService()
       xml_processor = XMLProcessorService()
       # Rest of function

   # After
   @router.get("/read/{urn}")
   async def read_text(
       urn: str,
       reference: Optional[str] = None,
       catalog_service = Depends(get_catalog_service),
       xml_processor = Depends(get_xml_processor_service)
   ):
       # Rest of function unchanged
   ```

3. **Monitor for Issues**
   - Add enhanced logging to detect any compatibility issues:
   ```python
   import logging

   logger = logging.getLogger(__name__)

   try:
       result = service_method()
       return result
   except Exception as e:
       logger.error(f"Migration error in {service_method.__name__}: {str(e)}")
       # Fall back to original implementation if possible
       try:
           logger.info(f"Attempting fallback to original implementation")
           # Fallback implementation
       except Exception as fallback_error:
           logger.error(f"Fallback also failed: {str(fallback_error)}")
           raise
   ```

### Phase 5: Complete Migration

1. **Transition to Enhanced Services Directly**
   - Replace adapter dependencies with enhanced services:
   ```python
   # Before
   from app.dependencies import get_catalog_service, get_xml_processor_service

   @router.get("/read/{urn}")
   async def read_text(
       urn: str,
       catalog_service = Depends(get_catalog_service),
       xml_processor = Depends(get_xml_processor_service)
   ):

   # After
   from app.dependencies import get_enhanced_catalog_service, get_enhanced_xml_service

   @router.get("/read/{urn}")
   async def read_text(
       urn: str,
       catalog_service = Depends(get_enhanced_catalog_service),
       xml_service = Depends(get_enhanced_xml_service)
   ):
   ```

2. **Update Configuration**
   - Disable compatibility mode:
   ```python
   # app/config.py
   settings = EulogosSettings(compatibility_mode=False)
   ```

3. **Remove Deprecated Components**
   - Remove old services and compatibility adapters:
   ```python
   # app/dependencies.py
   # Remove these functions
   def get_catalog_service():
       ...

   def get_xml_processor_service():
       ...
   ```

4. **Update Documentation**
   - Update API documentation to reflect the new architecture:
   ```markdown
   # API Documentation

   ## Text Retrieval

   ### Get Text by URN

   ```http
   GET /api/text/{urn}
   ```

   Retrieves a text by its URN.

   **Using Enhanced Catalog Service:**

   ```python
   from app.services.enhanced_catalog_service import EnhancedCatalogService

   catalog_service = EnhancedCatalogService()
   text = catalog_service.get_text_by_urn("urn:cts:greekLit:tlg0012.tlg001.perseus-grc1")
   ```
   ```

## Handling Potential Issues

### URN Format Discrepancies

If you encounter URN format discrepancies between old and new systems:

```python
from app.models.enhanced_urn import EnhancedURN

# Handle different URN formats
def normalize_urn(urn_obj):
    if hasattr(urn_obj, "urn_string"):
        # Old CtsUrn format
        return EnhancedURN(value=urn_obj.urn_string)
    elif hasattr(urn_obj, "value"):
        # Already an EnhancedURN or original URN model
        return EnhancedURN(value=urn_obj.value)
    else:
        # Assume string
        return EnhancedURN(value=str(urn_obj))
```

### Path Resolution Failures

If path resolution fails:

```python
file_path = catalog_service.resolve_file_path(urn)
if not file_path or not file_path.exists():
    # Try fallback method
    enhanced_urn = EnhancedURN(value=str(urn))
    fallback_path = enhanced_urn.get_file_path(str(settings.data_dir))
    if fallback_path.exists():
        return fallback_path

    # Log the issue
    logger.error(f"Path resolution failed for URN: {urn}")
    raise FileNotFoundError(f"Could not resolve path for URN: {urn}")
```

### Reference Navigation Issues

If you experience issues with reference navigation:

```python
# Check if references are being extracted properly
document = xml_service.load_document(urn)
if not document.references:
    # Try manual reference extraction
    logger.warning(f"No references found in document, trying manual extraction")
    xml_service._extract_references(document)

    if not document.references:
        logger.error(f"Reference extraction failed for URN: {urn}")
        return {"error": "Failed to extract references"}
```

## Verification Checklist

Use this checklist to verify the migration of each component:

- [ ] All catalog data is correctly loaded from integrated_catalog.json
- [ ] All text URNs can be resolved to file paths
- [ ] XML documents are correctly parsed and cached
- [ ] References are properly extracted from XML
- [ ] Text navigation works correctly
- [ ] Export functionality produces correct output
- [ ] Performance is equal to or better than the original implementation
- [ ] Error handling is comprehensive and consistent
- [ ] Logging provides sufficient detail for troubleshooting
- [ ] All tests pass with both compatibility adapters and direct enhanced services
- [ ] Documentation is updated to reflect the new architecture

## Timeline Recommendation

| Week | Task |
|------|------|
| Week 1 | Preparation: Generate integrated catalog and validate |
| Week 2 | Configure compatibility adapters and verify compatibility |
| Week 3 | Migrate individual components gradually |
| Week 4 | Transition API endpoints |
| Week 5 | Complete migration and remove deprecated components |

## Best Practices

1. **Test thoroughly** - Create comprehensive tests for all functionality
2. **Monitor performance** - Benchmark before and after migration
3. **Add logging** - Track all operations for debugging
4. **Implement fallbacks** - Provide a way to revert to old implementation if issues arise
5. **Communicate changes** - Document all changes for team awareness
6. **Gradual adoption** - Migrate one component at a time
7. **Validate data** - Ensure data consistency throughout the migration

## Related Documentation

For more details, refer to these documents:

- [API Documentation](API.md) - Detailed API reference
- [Implementation Guide](Implementation.md) - Implementation details
- [Architecture Overview](core-docs-architecture.md) - System architecture
