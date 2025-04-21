# Revised Eulogos Hierarchical Implementation Plan

## Core Principles

- **Single Source of Truth**: `integrated_catalog.json` is the ONLY source for text paths
- **Canonical References**: ALL text identification uses direct file paths ONLY
- **No Dual Tracking**: One implementation, one code path, zero legacy compatibility

## Implementation Strategy: Three Focused Bursts

This streamlined plan eliminates all dual-track complexity and focuses on a clean, direct replacement of key components.

## Burst A: Core Replacement (2 days)

### Day 1: Replace Core Files

1. **Backup Current Files**
   ```bash
   mkdir -p backups/services backups/routers backups/templates
   cp app/services/catalog_service.py backups/services/
   cp app/routers/browse.py backups/routers/
   cp app/templates/browse.html backups/templates/
   ```

2. **Replace Catalog Service**
   ```bash
   cp clean-catalog-service.py app/services/catalog_service.py
   ```
   
   **Key Implementation Details:**
   - Verify the service reads `integrated_catalog.json` correctly
   - Confirm it uses paths consistently as text identifiers
   - Ensure proper error handling for missing paths or malformed JSON
   - Validate all methods use canonical paths for lookup and modification

3. **Replace Browse Router**
   ```bash
   cp clean-browse-router.py app/routers/browse.py
   ```
   
   **Key Implementation Details:**
   - Confirm all endpoints use the hierarchical structure
   - Verify path parameters are properly typed and validated
   - Check that search results maintain canonical path references
   - Ensure all action endpoints use canonical paths consistently

4. **Add Author List Partial**
   ```bash
   cp author-list-partial.html app/templates/partials/author_list.html
   ```

### Day 2: Replace Templates and Update API

1. **Replace Browse Template**
   ```bash
   cp clean-browse-template.html app/templates/browse.html
   ```
   
   **Key Implementation Details:**
   - Verify all links use `text.path` for references
   - Confirm all action buttons use canonical paths
   - Check Alpine.js state management for collapsible sections
   - Validate filters and search functionality

2. **Update API Endpoint**
   ```bash
   # Edit app/main.py to update the /api/catalog endpoint
   ```
   
   **Simplified API Implementation:**
   ```python
   @app.get("/api/catalog")
   async def get_catalog(catalog_service=Depends(get_catalog_service)):
       """API endpoint to get the catalog in hierarchical structure."""
       # Return only hierarchical structure - eliminate dual representation
       return {
           "hierarchical": catalog_service.get_hierarchical_texts(include_archived=True)
       }
   ```

3. **Delete Obsolete Files**
   ```bash
   # Remove any files that implemented dual-mode functionality
   rm app/templates/flat_browse.html  # if exists
   ```

4. **Initial Smoke Test**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   **Test Key Functionality:**
   - Browse page loads correctly
   - Author sections expand/collapse
   - Links to texts work properly
   - Filters function as expected

## Burst B: UI Polish & State Management (2 days)

### Day 1: Implement JavaScript Functionality

1. **Create JavaScript State Management**
   ```bash
   # Implement clean JavaScript from the pseudocode
   cp app/static/js/main.js backups/static/js/
   ```

   **Final JavaScript Implementation:**
   ```javascript
   // Create complete implementation based on javascript-state-management.txt
   // Focusing on:
   // 1. Author section state management
   // 2. Favorite and archive button handling
   // 3. Robust error handling
   // 4. Efficient localStorage persistence
   ```

2. **Test JavaScript Functionality**
   - Verify author sections expand/collapse properly
   - Confirm state persists across page reloads
   - Test favorite button toggling
   - Test archive/unarchive functionality
   - Ensure error handling works as expected

### Day 2: UI Refinement

1. **Implement Filter Controls**
   - Test era filter buttons
   - Verify century dropdown
   - Test author type dropdown
   - Confirm favorites and archived filters work

2. **Search Functionality**
   - Test author search
   - Verify text search works properly
   - Confirm dropdown results display correctly

3. **Cross-Browser Testing**
   - Test in Chrome, Firefox, and Safari
   - Verify mobile responsiveness
   - Test with different screen sizes

## Burst C: Testing & Documentation (2 days)

### Day 1: Create Test Suite

1. **Setup Testing Framework**
   ```bash
   mkdir -p tests/unit tests/integration
   ```

2. **Create Catalog Test**
   ```bash
   # Create test_catalog_load.py
   ```
   
   **Key Test Cases:**
   - Test loading catalog from JSON
   - Verify hierarchical structure creation
   - Test path-based text lookup
   - Test filtering functionality
   - Verify favorites and archived toggles

3. **Create Endpoint Test**
   ```bash
   # Create test_browse_endpoints.py
   ```
   
   **Key Test Cases:**
   - Test root endpoint returns 200
   - Verify /browse with filters returns correct data
   - Test /search returns appropriate results
   - Test favorite and archive endpoints

4. **Setup GitHub Actions CI**
   ```bash
   mkdir -p .github/workflows
   # Create workflow YAML for CI
   ```

### Day 2: Documentation Update

1. **Update README.md**
   - Describe hierarchical-only approach
   - Document canonical path usage
   - Explain the catalog structure
   - Provide usage examples

2. **Create CONTRIBUTING.md**
   ```markdown
   # Contributing to Eulogos

   ## Core Principles
   - `integrated_catalog.json` is the ONLY source of truth for text paths
   - ALL text references must use the canonical path directly
   - NO string manipulation or alternate path construction is allowed

   ## Coding Standards
   - Black formatting (88 character line limit)
   - Flake8 linting
   - Pydocstyle D100s docstrings
   - Type annotations for all functions
   - Comprehensive error handling
   ```

3. **Update Development Documentation**
   - Remove any mentions of dual-track or URNs
   - Focus on the simplified architecture
   - Document the single canonical approach

## Final Verification

1. **Canonical Path Verification**
   - Ensure ALL text references use `text.path`
   - Verify NO string manipulation for paths
   - Confirm API endpoints consistently use paths

2. **Final Smoke Test**
   ```bash
   # Run all tests
   pytest tests/

   # Start the application
   uvicorn app.main:app
   ```

3. **Deployment Readiness Check**
   - Verify no legacy code or references remain
   - Ensure all documentation reflects the new approach
   - Confirm all tests pass

## Implementation Checklist

### Burst A: Core Replacement
- [ ] Backup current files
- [ ] Replace catalog service
- [ ] Replace browse router
- [ ] Add author list partial
- [ ] Replace browse template
- [ ] Update API endpoint
- [ ] Delete obsolete files
- [ ] Perform initial smoke test

### Burst B: UI Polish & State Management
- [ ] Implement JavaScript from pseudocode
- [ ] Test JavaScript functionality
- [ ] Implement and test filter controls
- [ ] Verify search functionality
- [ ] Perform cross-browser testing

### Burst C: Testing & Documentation
- [ ] Setup testing framework
- [ ] Create catalog tests
- [ ] Create endpoint tests
- [ ] Setup GitHub Actions CI
- [ ] Update README.md
- [ ] Create CONTRIBUTING.md
- [ ] Update development documentation
- [ ] Perform final verification
- [ ] Complete deployment readiness check

## Simplified Command Reference

For quick execution of the plan:

```bash
# Burst A: Core Replacement
mkdir -p backups/services backups/routers backups/templates backups/static/js
cp app/services/catalog_service.py backups/services/
cp app/routers/browse.py backups/routers/
cp app/templates/browse.html backups/templates/
cp app/static/js/main.js backups/static/js/

cp clean-catalog-service.py app/services/catalog_service.py
cp clean-browse-router.py app/routers/browse.py
cp author-list-partial.html app/templates/partials/author_list.html
cp clean-browse-template.html app/templates/browse.html

# [Edit app/main.py to update API endpoint]

# Burst B: UI Implementation
# [Create complete JavaScript implementation]

# Burst C: Testing & Documentation
mkdir -p tests/unit tests/integration
mkdir -p .github/workflows

# [Create test files and documentation]

# Final verification
pytest tests/
uvicorn app.main:app
```

This implementation plan provides a focused, direct approach to eliminating the dual-track strategy and establishing a single, canonical way of referencing texts using the integrated_catalog.json as the sole source of truth.