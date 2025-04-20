# Eulogos UI Enhancement Implementation Checklist

## Overview

This document provides a step-by-step implementation guide for enhancing the Eulogos UI with a hierarchical author-grouped display while maintaining the integrity of the canonical path-based reference system.

## Prerequisites

- Backup all files that will be modified
- Ensure `integrated_catalog.json` contains the necessary author and work metadata
- Verify development environment is properly set up

## Implementation Steps

### 1. Update Catalog Service

- [ ] Replace `app/services/catalog_service.py` with the enhanced version
- [ ] Add the following methods:
  - [ ] `get_hierarchical_texts()`
  - [ ] `get_filtered_hierarchical_texts()`
  - [ ] `get_all_eras()`
  - [ ] `get_all_centuries()`
  - [ ] `get_all_author_types()`
  - [ ] `search_texts_by_title()`
  - [ ] `search_authors()`
- [ ] Update `_transform_hierarchical_to_flat()` to extract author metadata
- [ ] Update `_build_indexes()` to build additional lookup lists for eras, centuries, and author types
- [ ] Add new endpoint for unarchiving: `unset_archived()`

### 2. Update Browse Router

- [ ] Replace `app/routers/browse.py` with the enhanced version
- [ ] Update the `/` route to use hierarchical data
- [ ] Update the `/browse` route to support new filter parameters:
  - [ ] `era`
  - [ ] `century`
  - [ ] `author_type`
  - [ ] `author_query`
  - [ ] `show_archived`
- [ ] Add new `/unarchive/{path:path}` endpoint
- [ ] Add new `/authors` endpoint for HTMX partial template support

### 3. Create/Update Templates

- [ ] Replace `app/templates/browse.html` with the new hierarchical version
- [ ] Create `app/templates/partials/author_list.html` for author search results
- [ ] Update `app/static/js/main.js` to include new Alpine.js components for author collapsing functionality
- [ ] Ensure all templates use correct path-based references

### 4. Testing Phase

#### Basic Functionality Tests

- [ ] Verify application starts without errors
- [ ] Check that browsing without filters displays all authors and works
- [ ] Verify author sections expand/collapse correctly
- [ ] Confirm that filter buttons/dropdowns work as expected
- [ ] Test favorite and archive/unarchive functionality
- [ ] Verify text and author search work independently

#### Path Reference Tests

- [ ] Verify all links to texts use the canonical path format
- [ ] Check that favorite/archive toggles use the correct path references
- [ ] Test text reading navigation to ensure it works with the proper paths

#### Filter Tests

- [ ] Test each era filter
- [ ] Test century dropdown filtering
- [ ] Test author type filtering
- [ ] Test combined filters (e.g., era + author type)
- [ ] Verify favorites-only view
- [ ] Test archived texts view

#### Edge Cases

- [ ] Test with a small dataset (few authors/works)
- [ ] Test with a large dataset (many authors/works)
- [ ] Verify behavior with no texts in the catalog
- [ ] Test behavior with texts missing metadata
- [ ] Check behavior with very long author/work names

### 5. Rollback Plan

If issues are encountered during implementation or testing:

1. Restore backed up files to their original state
2. Alternatively, add a feature flag to `app/config.py`:
   ```python
   hierarchical_browse: bool = Field(
      True, 
      description="Enable hierarchical browsing by author"
   )
   ```
3. Use the feature flag in the router to conditionally render the hierarchical or grid view

### 6. Deployment Steps

1. [ ] Ensure all local tests pass
2. [ ] Deploy to staging environment and verify functionality
3. [ ] Test on multiple browsers and devices
4. [ ] Deploy to production environment
5. [ ] Monitor for any issues after deployment

## Conclusion

The hierarchical author-grouped UI enhances the browsing experience while maintaining the canonical path-based reference system. The implementation carefully preserves compatibility with existing features and focuses on providing a more organized and intuitive interface for users.

By following this checklist, the implementation should proceed smoothly with minimal risk to the existing functionality.
