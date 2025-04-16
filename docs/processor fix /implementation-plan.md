# XML Processor Path Resolution Fix - Implementation Plan

## Problem Statement

The current XMLProcessorService bypasses our "single source of truth" principle by resolving URN-to-file-path mappings independently of the integrated catalog. This creates parallel systems for file path resolution that can lead to synchronization issues.

## Architectural Principle

The integrated_catalog.json file should be the single authoritative source for all text metadata, including file paths. All components that need to access text files should get their path information from this catalog rather than calculating paths independently.

## Implementation Plan

### Phase 1: Core Service Updates

1. **Update XMLProcessorService**
   - Modify the constructor to accept a CatalogService instance
   - Update resolve_urn_to_file_path() to use catalog as source of truth
   - Add fallback mechanism with warning for backward compatibility

2. **Update Text Model**
   - Add 'path' field to the Text model in app/models/catalog.py
   - Add logic to generate default paths from URN if not explicitly provided

3. **Update CatalogService**
   - Enhance path handling in create_unified_catalog()
   - Add path validation methods
   - Add get_path_by_urn() method

### Phase 2: Dependency Injection Updates

4. **Update Dependencies Module**
   - Modify get_xml_processor_service() to inject CatalogService
   - Ensure proper service ordering and caching

5. **Update Router Dependencies**
   - Update reader.py router to use the enhanced dependencies
   - Update export.py router to use the enhanced dependencies

### Phase 3: Testing and Validation

6. **Add Unit Tests**
   - Test XMLProcessorService with mocked CatalogService
   - Test path resolution with and without catalog
   - Test fallback behavior

7. **Integration Testing**
   - Test with actual catalog and XML files
   - Verify path resolution correctly uses catalog paths

### Phase 4: Deployment

8. **Prepare Deployment**
   - Update documentation to reflect the architectural changes
   - Create migration notes

9. **Deploy Changes**
   - Deploy changes to staging environment
   - Validate with real data
   - Deploy to production

10. **Monitor & Support**
    - Watch logs for path resolution warnings
    - Monitor for any file not found errors
    - Support users through the transition

## Files to Modify

1. `app/services/xml_processor_service.py`
2. `app/models/catalog.py`
3. `app/services/catalog_service.py`
4. `app/dependencies.py`
5. `app/routers/reader.py`
6. `app/routers/export.py`

## New Files to Create

1. `tests/test_xml_processor.py`

## Migration Considerations

The changes include backward compatibility to ensure current functionality continues to work, but with warnings that highlight bypassing the single source of truth principle. This allows for a phased transition rather than a breaking change.

## Validation Criteria

1. All existing text viewing functionality continues to work
2. Path resolution correctly uses paths from the catalog
3. Log warnings appear when fallback resolution is used
4. No duplicate path resolution logic exists in the system

## Rollback Plan

In case of issues, we can revert to the previous version of XMLProcessorService that does not depend on CatalogService, ensuring minimal disruption to the system.
