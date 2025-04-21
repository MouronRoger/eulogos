# Eulogos Complete Migration Audit Checklist

## 1. File Replacement
* [ ] app/services/catalog_service.py is replaced with clean-catalog-service.py
* [ ] app/routers/browse.py is replaced with clean-browse-router.py
* [ ] app/templates/browse.html is replaced with clean-browse-template.html
* [ ] app/templates/partials/author_list.html is added for author search results
* [ ] app/static/js/main.js is updated with robust state management
* [ ] Update API catalog endpoint in app/main.py
* [ ] Remove any unused/legacy files related to the old flat logic

## 2. Imports and Dependencies
* [ ] All imports of CatalogService and get_catalog_service point to the new hierarchical implementation
* [ ] No code imports or uses legacy/flat methods (e.g., get_all_texts, get_texts_by_author, etc.)
* [ ] All routers and services use only the new hierarchical API
* [ ] Check for any indirect dependencies on flat structure in other modules

## 3. Canonical Path Consistency
* [ ] All text references in templates, routers, and JS use text.path from the catalog
* [ ] No string manipulation or alternate path construction anywhere in the codebase
* [ ] All HTMX and JS actions use canonical paths
* [ ] API endpoints consistently use path-based identifiers

## 4. Template and UI Consistency
* [ ] The browse template displays texts grouped by author and work (hierarchical)
* [ ] All links, buttons, and forms use canonical paths
* [ ] No references to flat or legacy UI remain
* [ ] Search results template works with flattened hierarchical results
* [ ] Alpine.js state management properly handles author expansion/collapse

## 5. Testing
* [ ] All unit and integration tests are updated to use the new hierarchical API
* [ ] Tests for catalog service, browse router, and templates pass
* [ ] Verify test fixtures include proper hierarchical structure
* [ ] Manual UI tests confirm:
  * Hierarchical display works
  * Expand/collapse and state persistence work
  * All filters and searches work
  * Favorites and archive/unarchive work
  * Reading and reference navigation work
* [ ] Test across multiple browsers and screen sizes
* [ ] Test with both small and large catalogs

## 6. Documentation
* [ ] All documentation and onboarding materials reflect the new, single approach
* [ ] No mention of feature flags, dual-mode, or legacy/flat logic
* [ ] Update comments in code to reflect hierarchical-only approach
* [ ] Update development guidelines to enforce canonical path usage

## 7. Code Quality
* [ ] All code is formatted with Black, passes flake8, and has docstrings (pydocstyle D100s)
* [ ] No unused imports or variables
* [ ] All functions and classes have type annotations
* [ ] Proper error handling for all operations, especially JSON parsing and state management
* [ ] No commented-out legacy code

## 8. Rollback Readiness
* [ ] Backups and/or a separate branch exist for the pre-migration state
* [ ] Rollback steps are documented and tested
* [ ] Database and file system migrations (if any) have rollback plans

## 9. Performance Verification
* [ ] Measure page load times with large catalogs
* [ ] Verify expand/collapse performance with many authors
* [ ] Test search performance with various queries
* [ ] Ensure localStorage management doesn't degrade with large datasets