# Eulogos Hierarchical UI Implementation Checklist

## Overview

This document provides a step-by-step implementation guide for enhancing the Eulogos UI with a hierarchical author-grouped display while maintaining strict canonical path consistency. The implementation eliminates dual-mode code paths to ensure consistency and maintainability.

## Prerequisites

- Backup all files that will be modified
- Ensure `integrated_catalog.json` contains the necessary author and work metadata
- Verify development environment is properly set up

## Implementation Steps

### 1. Update Catalog Service

- [ ] Replace `app/services/catalog_service.py` with the clean implementation
- [ ] Remove any methods that deal with flat-only views
- [ ] Ensure all methods use path consistently as text identifier
- [ ] Add robust error handling for all operations:
  - [ ] Safe fallbacks for missing metadata fields
  - [ ] Proper handling of missing paths
  - [ ] Error capture for JSON parsing issues
- [ ] Add or update the following methods:
  - [ ] `get_hierarchical_texts()`
  - [ ] `get_filtered_hierarchical_texts()`
  - [ ] `get_all_eras()`
  - [ ] `get_all_centuries()`
  - [ ] `get_all_author_types()`
  - [ ] `search_authors()`

### 2. Update Browse Router

- [ ] Replace `app/routers/browse.py` with the clean implementation
- [ ] Remove any conditional logic for flat vs. hierarchical views
- [ ] Ensure all endpoints return hierarchical data structures
- [ ] Update the `/` route to always use hierarchical data
- [ ] Add new endpoints:
  - [ ] `/unarchive/{path:path}`
  - [ ] `/authors` (for HTMX partial template support)
- [ ] Ensure all endpoints consistently use the canonical path

### 3. Update Templates

- [ ] Replace `app/templates/browse.html` with the hierarchical-only implementation
- [ ] Ensure all links, buttons, and forms use canonical paths
- [ ] Add explicit `data-author` attributes to all author headers
- [ ] Create `app/templates/partials/author_list.html` for author search results
- [ ] Add robust error handling for JSON parsing in Alpine.js data loading

### 4. Update JavaScript

- [ ] Implement robust state management with error handling
- [ ] Add localStorage cleanup for removed authors
- [ ] Implement default expansion for first 3 authors when no state exists
- [ ] Ensure all HTMX actions correctly use canonical paths
- [ ] Add error handling for response parsing

### 5. Testing Phase

#### Path Consistency Tests

- [ ] Verify all links to texts use the canonical path (`text.path`)
- [ ] Check that all action buttons (favorite/archive) use the canonical path
- [ ] Verify all search, filtering, and sorting maintains path consistency
- [ ] Test navigation from browse to read views with correct path resolution

#### Functionality Tests

- [ ] Test expanding/collapsing author sections
- [ ] Verify author state persistence across page reloads
- [ ] Test all filtering options (era, century, author type, etc.)
- [ ] Test search functionality (text search and author search)
- [ ] Verify favorite and archive/unarchive functionality
- [ ] Test combined filtering (e.g., era + favorites)

#### Robustness Tests

- [ ] Test with missing metadata fields to ensure safe fallbacks work
- [ ] Test with corrupted localStorage data
- [ ] Test with an empty catalog or missing sections
- [ ] Verify behavior with very long author/work names
- [ ] Test across different browsers and screen sizes

#### Performance Tests

- [ ] Measure load time for large catalogs
- [ ] Test expand/collapse performance with many authors
- [ ] Verify filtering performance with large datasets

### 6. Deployment Steps

1. [ ] Ensure all local tests pass
2. [ ] Deploy to staging environment
3. [ ] Test on multiple browsers and devices
4. [ ] Deploy to production environment
5. [ ] Monitor for any issues

## Code Inspection Checklist

When reviewing the implementation, verify that:

1. **No Path Manipulation**: All text references use the canonical path from the catalog
2. **No Conditional Logic**: No feature flags or conditional rendering between flat and hierarchical views
3. **Single Source of Truth**: All operations start from the hierarchical catalog data
4. **Consistent Identifiers**: The path field is used consistently as the text identifier
5. **Robust Error Handling**: All operations have proper error handling and safe fallbacks
6. **Clean State Management**: Alpine.js and localStorage operations have proper error handling

## Conclusion

The hierarchical author-grouped UI enhances the browsing experience while maintaining strict canonical path consistency. By eliminating the dual-mode approach, this implementation creates a more maintainable codebase that's less prone to referencing errors.

The key improvement over previous approaches is the complete removal of feature flags and alternate code paths, ensuring that there's only one way to reference texts throughout the application.