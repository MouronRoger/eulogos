# Eulogos URN Deprecation and Removal Plan

> **MODIFIED IMPLEMENTATION:** This plan was modified during execution. Since there were no active users of the codebase, we skipped directly to the final removal phase (Phase 6) without going through the deprecation phases. All URN-related code has been completely removed from the codebase.

## Overview

This document details the strategy for phasing out and eventually removing all URN-based endpoints in the Eulogos application. After implementing parallel ID-based endpoints as outlined in the URN elimination plan, we will follow this phased approach to complete the transition.

## Timeline

The transition will occur over 6 months with the following phases:

### Phase 1: Parallel Implementation (Complete)

- ✅ Implement ID-based endpoints parallel to URN-based endpoints
- ✅ Update models to use explicit ID fields
- ✅ Update templates to include ID-based links
- ✅ Ensure all texts have stable unique IDs

### Phase 2: Deprecation Notices (Months 1-2)

- Add `Deprecated` annotations to all URN-based endpoint functions
- Add deprecation warnings in logs when URN-based endpoints are accessed
- Include deprecation notices in API responses for URN-based endpoints
- Add visual indicators in the UI for deprecated features
- Update all documentation to mark URN-based endpoints as deprecated

Implementation:

```python
# Example implementation of deprecation notice in router
@router.get("/read/{urn}", response_class=HTMLResponse, response_model=None, 
            deprecated=True)
async def read_text(
    request: Request,
    urn: str,
    # ...
):
    """Read a text with optional reference navigation.
    
    Deprecated: This endpoint is deprecated and will be removed in a future version.
    Use /read/id/{text_id} instead.
    
    Args:
        request: FastAPI request object
        urn: The URN of the text to read
        # ...
    """
    # Log deprecation warning
    logger.warning(f"Deprecated endpoint accessed: /read/{urn} - Use ID-based endpoint instead")
    
    # Add deprecation notice to the context
    # ... existing code ...
    
    # Include deprecation notice in the response
    return templates.TemplateResponse(
        "reader.html",
        {
            # ... existing context ...
            "deprecation_notice": "This endpoint is deprecated. Please use ID-based endpoints instead.",
        },
    )
```

### Phase 3: Usage Monitoring (Months 2-3)

- Implement detailed usage tracking for both URN and ID-based endpoints
- Create a monitoring dashboard to track adoption rate of ID-based endpoints
- Identify patterns of URN-based usage to target specific communications
- Set up alerts for high-volume URN endpoint usage

Implementation:

```python
# Example middleware for tracking endpoint usage
@app.middleware("http")
async def endpoint_usage_tracker(request: Request, call_next):
    # Track the start time
    start_time = time.time()
    
    # Get the path and method
    path = request.url.path
    method = request.method
    
    # Track if this is a URN or ID-based endpoint
    is_urn_endpoint = "/id/" not in path and any(pattern in path for pattern in ["/read/", "/document/", "/passage/"])
    is_id_endpoint = "/id/" in path
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log the usage metrics
    if is_urn_endpoint:
        logger.info(f"URN endpoint used: {method} {path} (Time: {process_time:.2f}s)")
        # Increment counter in metrics database
        await metrics_service.increment_counter("urn_endpoint_usage", {"path": path, "method": method})
    elif is_id_endpoint:
        logger.info(f"ID endpoint used: {method} {path} (Time: {process_time:.2f}s)")
        # Increment counter in metrics database
        await metrics_service.increment_counter("id_endpoint_usage", {"path": path, "method": method})
    
    return response
```

### Phase 4: Communication Campaign (Months 3-4)

- Send direct communications to any identified high-volume URN users
- Add more prominent deprecation notices in the UI
- Update all documentation to emphasize the impending removal
- Create migration tutorials and examples
- Add a countdown to URN deprecation on the dashboard

Implementation:

```python
# Example UI banner for deprecation
@app.middleware("http")
async def deprecation_banner_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Only modify HTML responses
    if response.headers.get("content-type", "").startswith("text/html"):
        content = response.body.decode()
        
        # Calculate days until removal
        removal_date = datetime.datetime(2023, 12, 31)  # Example date
        days_left = (removal_date - datetime.datetime.now()).days
        
        # Add banner to HTML content
        banner = f"""
        <div class="deprecation-banner" style="background-color: #ffcccc; color: #990000; padding: 10px; text-align: center; font-weight: bold;">
            WARNING: URN-based endpoints will be removed in {days_left} days. 
            Please transition to ID-based endpoints. 
            <a href="/docs/api/id_based_endpoints" style="color: #990000; text-decoration: underline;">Learn more</a>
        </div>
        """
        
        # Insert banner after the body tag
        modified_content = content.replace("<body>", f"<body>\n{banner}")
        
        # Create a new response with the modified content
        return Response(
            content=modified_content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
    
    return response
```

### Phase 5: Read-Only Mode (Months 4-5)

- Make all URN-based endpoints read-only
- Return 410 Gone status for deprecated write operations
- Add enhanced logging to track any remaining URN-based usage
- Finalize the cleanup plan based on usage patterns

Implementation:

```python
# Example read-only implementation for a previously writable endpoint
@router.post("/text/{urn}/favorite", deprecated=True)
async def toggle_favorite_deprecated(
    urn: str,
    catalog_service: EnhancedCatalogService = Depends(get_enhanced_catalog_service)
):
    """Toggle favorite status for a text.
    
    Deprecated: This endpoint is now read-only and will be removed.
    Use /text/id/{text_id}/favorite instead.
    """
    # Return 410 Gone status
    raise HTTPException(
        status_code=410,
        detail={
            "message": "This endpoint is deprecated and now read-only. Use ID-based endpoints instead.",
            "migration_path": f"/text/id/{catalog_service.get_text_by_urn(urn).id}/favorite"
        }
    )
```

### Phase 6: Removal (Month 6)

- Remove all URN-based endpoints from the codebase
- Remove URN fields from the Text model
- Delete URN model files (urn.py, enhanced_urn.py)
- Update all remaining code to work exclusively with IDs
- Redirect all URN-based URLs to an informational page
- Deploy the final URN-free version

## Clean-up Checklist

Once the transition period is complete, perform the following cleanup tasks:

- [ ] Delete URN model files:
  - [ ] `app/models/urn.py`
  - [ ] `app/models/enhanced_urn.py`

- [ ] Remove URN validation from middleware:
  - [ ] Remove validate_urn_format function from `app/middleware/validation.py`

- [ ] Update the Text model:
  - [ ] Remove the `urn` field entirely
  - [ ] Update the `to_dict()` method to not include URN
  - [ ] Remove URN-related code from `from_dict()` method

- [ ] Clean up CatalogService:
  - [ ] Remove `get_text_by_urn` method
  - [ ] Remove `get_path_by_urn` method
  - [ ] Remove `_texts_by_urn` index
  - [ ] Remove URN references from all other methods

- [ ] Update XMLProcessorService:
  - [ ] Remove `load_document` method that takes URNs
  - [ ] Only keep `load_document_by_id` and `load_document_by_path` methods

- [ ] Clean up Export Services:
  - [ ] Update export methods to only accept text_id parameters
  - [ ] Remove all URN-handling code

- [ ] Clean up routers:
  - [ ] Remove all URN-based endpoint functions
  - [ ] Remove URN references from documentation

- [ ] Update tests:
  - [ ] Remove URN-specific tests
  - [ ] Update remaining tests to use IDs instead of URNs

## Monitoring and Rollback Plan

Throughout the transition, we will monitor for any issues:

1. Track error rates for both URN and ID-based endpoints
2. Set up alerts for any significant increases in errors
3. Maintain the ability to roll back changes if critical issues arise
4. Have support resources ready to assist with transition issues

## Conclusion

This phased approach allows for a gradual transition from URN-based to ID-based endpoints while minimizing disruption. The 6-month timeline provides ample opportunity for users to update their code, and the monitoring will help identify any issues early in the process. 