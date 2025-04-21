# Migration Checklist and Verification Steps

Use this checklist to ensure a smooth migration to the hierarchical implementation.

## Backup Phase

- [ ] Create a backup of the entire repository
- [ ] Create branch for implementation: `git checkout -b hierarchical-implementation`

## Preparation Phase

- [ ] Review all files that will be modified:
  - [ ] `app/services/catalog_service.py`
  - [ ] `app/routers/browse.py`
  - [ ] `app/templates/browse.html`
  - [ ] `app/static/js/main.js`
  - [ ] `app/main.py` (just the `/api/catalog` endpoint)
  - [ ] Any test files that depend on the above

## Implementation Phase

1. **Update Catalog Service**
   - [ ] Replace `app/services/catalog_service.py` with the clean implementation
   - [ ] Verify imports in service file are correct
   - [ ] Ensure all methods have proper docstrings and type hints

2. **Update Browse Router**
   - [ ] Replace `app/routers/browse.py` with the clean implementation
   - [ ] Verify all imports in the router
   - [ ] Check that all endpoints maintain canonical path usage

3. **Update Templates**
   - [ ] Replace `app/templates/browse.html` with the hierarchical-only version
   - [ ] Verify template references the correct variables
   - [ ] Check all path references in templates

4. **Update JavaScript**
   - [ ] Update `app/static/js/main.js` with the robust state management
   - [ ] Verify error handling is properly implemented
   - [ ] Test localStorage functionality

5. **Update API Endpoint**
   - [ ] Update the `/api/catalog` endpoint in `app/main.py`

## Verification Phase

### Path Consistency Checks

- [ ] Verify all `href` attributes use canonical paths
- [ ] Verify all `hx-post` attributes use canonical paths
- [ ] Check that no URNs or alternative paths are being used

### Visual and Functional Tests

- [ ] Load the main browse page and verify hierarchical display works
- [ ] Test expanding and collapsing author sections
- [ ] Test author state persistence across page reloads
- [ ] Verify all filtering options work:
  - [ ] Era filter
  - [ ] Century filter
  - [ ] Author type filter
  - [ ] Author search
  - [ ] Text search
  - [ ] Favorites filter
  - [ ] Archived filter
- [ ] Test search dropdown functionality
- [ ] Test basic text operations:
  - [ ] Adding to favorites
  - [ ] Archiving texts
  - [ ] Unarchiving texts
- [ ] Test text reading functionality:
  - [ ] Loading texts
  - [ ] References navigation
  - [ ] Text rendering

### Component Tests

Use these test commands to verify specific components:

#### Catalog Service

```bash
# Run just the catalog service tests
pytest tests/unit/test_catalog_service.py -v
```

Check for:
- All hierarchical methods work
- Path-based text lookup works
- Filtering by various criteria works

#### Browse Router

```bash
# Run just the browse router tests
pytest tests/unit/test_browse_router.py -v
```

Check for:
- Correct hierarchical structure in responses
- Proper filtering in all endpoints
- Canonical path usage in all responses

#### Templates

Load each template in a browser and verify:
- The browse page displays the hierarchical structure
- Text sections expand and collapse correctly
- All links point to the correct paths
- Search results display correctly

## Rollback Plan

If issues are encountered:

1. Revert changes to each file:
   ```bash
   git checkout main -- app/services/catalog_service.py
   git checkout main -- app/routers/browse.py
   # etc.
   ```

2. If necessary, restore the entire branch:
   ```bash
   git checkout main
   git branch -D hierarchical-implementation
   ```

## Final Deployment Steps

Once all verification steps pass:

1. Merge to main branch:
   ```bash
   git checkout main
   git merge hierarchical-implementation
   ```

2. Deploy to staging environment and test again

3. Deploy to production

## Post-Deployment Monitoring

Watch for:
- Any errors in application logs
- Performance issues with large catalogs
- Browser compatibility issues
- User feedback on the new interface