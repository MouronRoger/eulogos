# Eulogos URN Elimination Implementation Plan

## Overview

This implementation plan details the process of removing URN-based path resolution from the Eulogos project and establishing the `integrated_catalog.json` as the single source of truth for all path resolution. The plan is designed for a codebase with no active users, allowing for a clean architectural transition rather than a gradual migration.

## Phase 1: Preparation (1-2 days)

### 1.1 Catalog Service Enhancement

- Create a new `get_text_by_id` method in `CatalogService`:
  ```python
  def get_text_by_id(self, text_id: str) -> Optional[Text]:
      """Get a text by its stable ID (not URN).
      
      Args:
          text_id: The stable ID of the text
          
      Returns:
          The text object or None if not found
      """
      return self._texts_by_id.get(text_id)
  ```

- Build a new index in `_build_indexes` method:
  ```python
  # Index texts by ID
  self._texts_by_id = {}
  for text in self._unified_catalog.catalog:
      if text.id:
          self._texts_by_id[text.id] = text
  ```

- Ensure all texts have stable, unique IDs in `Text` model:
  ```python
  # In app/models/catalog.py
  class Text:
      """Model for a text in the catalog."""
      
      def __init__(
          self,
          id: str,  # Add explicit ID field
          urn: Optional[str] = None,  # Make URN optional
          # ... other parameters ...
      ):
          self.id = id
          self.urn = urn
          # ... other assignments ...
  ```

### 1.2 Identify All URN Dependencies

- Conduct comprehensive code analysis:
  ```bash
  # Find all files with URN references
  grep -r "URN" --include="*.py" .
  grep -r "urn" --include="*.py" .
  
  # Find all import statements for URN models
  grep -r "from app.models.urn import" --include="*.py" .
  grep -r "from app.models.enhanced_urn import" --include="*.py" .
  ```

- Document all URN dependencies:
  | File | URN Usage | Replacement Approach |
  |------|-----------|----------------------|
  | app/services/export_service.py | Path resolution | Use `text.path` from catalog |
  | app/services/enhanced_export_service.py | Path resolution | Use `text.path` from catalog |
  | app/routers/v2/reader.py | Endpoint parameter | Replace with `text_id` |
  | ... | ... | ... |

## Phase 2: Routing Layer Redesign (2-3 days)

### 2.1 Create New ID-based Endpoints

- Modify endpoint definitions in relevant router files:
  ```python
  # From:
  @router.get("/read/{urn}", response_class=HTMLResponse)
  async def read_text(request: Request, urn: str, ...):
      # URN-based implementation
  
  # To:
  @router.get("/read/{text_id}", response_class=HTMLResponse)
  async def read_text(request: Request, text_id: str, ...):
      # ID-based implementation
      text = catalog_service.get_text_by_id(text_id)
      if not text:
          raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")
      path = text.path
      # Continue with path-based processing
  ```

- Create new route parameter documentation:
  ```python
  @router.get("/document/{text_id}", response_model=None)
  async def get_document_info(
      text_id: str = Path(..., description="The stable ID of the document"),
      # ... other parameters ...
  ):
  ```

### 2.2 Update Service Layer

- Modify XMLProcessorService to work with direct paths:
  ```python
  # Remove:
  def load_document(self, urn: Union[str, EnhancedURN]) -> XMLDocument:
      """Load XML document by URN."""
  
  # Replace with:
  def load_document_by_path(self, path: str) -> XMLDocument:
      """Load XML document directly by path."""
  ```

- Update service dependencies:
  ```python
  # In app/dependencies.py
  @lru_cache()
  def get_xml_processor_service() -> EnhancedXMLService:
      """Get an EnhancedXMLService instance, cached for performance."""
      catalog_service = get_catalog_service()
      settings = get_settings()
      return EnhancedXMLService(catalog_service=catalog_service, settings=settings)
  ```

## Phase 3: Implementation & Testing (3-4 days)

### 3.1 Core API Implementation

#### Browse Endpoint
```python
@router.get("/browse", response_class=HTMLResponse)
async def browse_texts(
    request: Request,
    show: str = Query("all"),
    era: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    catalog_service: EnhancedCatalogService = Depends(get_catalog_service),
):
    # Get all authors using catalog directly
    authors = catalog_service.get_all_authors(include_archived=(show == "archived"))
    
    # Use ID-based references in templates
    result_authors = []
    for author in authors:
        author_data = author.dict()
        works = catalog_service.get_texts_by_author(author.id)
        author_data["works"] = [work.dict() for work in works]
        result_authors.append(author_data)
    
    return templates.TemplateResponse(
        "browse.html",
        {"request": request, "authors": result_authors}
    )
```

#### Reader Endpoint
```python
@router.get("/read/{text_id}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    text_id: str,
    reference: Optional[str] = None,
    catalog_service: EnhancedCatalogService = Depends(get_catalog_service),
    xml_service: EnhancedXMLService = Depends(get_xml_processor_service),
):
    # Get text from catalog by ID
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")
    
    # Get path from text object
    path = text.path
    if not path:
        raise HTTPException(status_code=404, detail="Text has no associated file path")
    
    try:
        # Load document by path
        document = xml_service.load_document_by_path(path)
        
        # Process document as before
        # ...
        
        return templates.TemplateResponse(
            "reader.html",
            {
                "request": request,
                "text": text,
                "content": html_content,
                "path": path,
                "current_ref": reference,
                # ... other context variables ...
            },
        )
    except Exception as e:
        # Error handling
        # ...
```

#### References Endpoint
```python
@router.get("/references/{text_id}", response_model=None)
async def get_references(
    text_id: str,
    xml_service: EnhancedXMLService = Depends(get_xml_processor_service),
    catalog_service: EnhancedCatalogService = Depends(get_catalog_service),
    html_output: bool = Query(True),
):
    # Get text from catalog by ID
    text = catalog_service.get_text_by_id(text_id)
    if not text:
        raise HTTPException(status_code=404, detail=f"Text not found: {text_id}")
    
    # Get path from text object
    path = text.path
    if not path:
        raise HTTPException(status_code=404, detail="Text has no associated file path")
    
    try:
        # Load document by path
        document = xml_service.load_document_by_path(path)
        
        # Extract references
        references = xml_service.extract_references(document)
        
        # Generate response
        # ...
    except Exception as e:
        # Error handling
        # ...
```

### 3.2 Test New Endpoints

- Create test fixtures for ID-based resolution:
  ```python
  # In tests/fixtures.py
  @pytest.fixture
  def catalog_with_texts():
      """Fixture providing a catalog with test texts."""
      catalog = {
          "text1": {
              "id": "text1",
              "path": "data/test/text1.xml",
              "work_name": "Test Text 1",
              # ... other fields ...
          },
          # ... more texts ...
      }
      return catalog
  ```

- Write tests for path resolution:
  ```python
  # In tests/test_catalog_service.py
  def test_get_text_by_id(catalog_service_with_texts):
      """Test retrieving a text by ID."""
      text = catalog_service_with_texts.get_text_by_id("text1")
      assert text is not None
      assert text.id == "text1"
      assert text.path == "data/test/text1.xml"
  ```

- Test ID-based endpoints:
  ```python
  # In tests/test_reader_router.py
  async def test_read_text_by_id(client, catalog_service_mock):
      """Test reading a text by ID."""
      # Setup catalog mock
      catalog_service_mock.get_text_by_id.return_value = Text(
          id="text1",
          path="data/test/text1.xml",
          work_name="Test Text 1",
          # ... other fields ...
      )
      
      # Test endpoint
      response = await client.get("/read/text1")
      assert response.status_code == 200
  ```

## Phase 4: Cleanup & Documentation (1-2 days)

### 4.1 Remove URN-Related Code

- Delete URN model files:
  ```bash
  rm app/models/urn.py
  rm app/models/enhanced_urn.py
  ```

- Remove URN validation from middleware:
  ```bash
  # Remove validate_urn_format function and related code
  # from app/middleware/validation.py
  ```

- Remove URN imports from all files:
  ```bash
  # In each file that imported URN models
  # Remove lines like:
  from app.models.urn import URN
  from app.models.enhanced_urn import EnhancedURN
  ```

- Remove URN-to-path mapping code:
  ```bash
  # Remove deprecated methods like get_path_by_urn from CatalogService
  ```

### 4.2 Update Documentation

- Update API documentation:
  ```python
  # In app/routers/v2/reader.py docstrings
  """Router for text reading operations (v2 API).

  This module provides endpoints for text reading functionality including:
  - Text display with reference-based navigation using text ID
  - Hierarchical reference extraction and browsing
  - XML to HTML transformation with enhanced styling options
  - Metadata exposure with rich context
  """
  ```

- Add examples of ID-based access:
  ```python
  # Example documentation comment
  """
  Example usage:
  
  GET /read/text123
  GET /read/text123?reference=1.1
  """
  ```

- Document architectural principles:
  ```python
  # In app/services/catalog_service.py docstring
  """Service for catalog operations.
  
  The catalog service is the single source of truth for path resolution
  in the Eulogos system. All file access must go through the catalog
  to ensure consistency and maintainability.
  """
  ```

## Phase 5: Final Review & Deployment (1 day)

### 5.1 Code Review Checklist

- [ ] Verify all URN-related code has been removed
- [ ] Confirm all path resolution uses catalog service
- [ ] Check all templates for URN references
- [ ] Ensure export services properly use ID-based access
- [ ] Validate that there's only one copy of canonical_catalog_builder.py
- [ ] Review all docstrings for outdated URN references
- [ ] Verify error handling for ID resolution failures

### 5.2 Deployment

- Build and test the application
- Deploy to staging environment
- Run integration tests
- Deploy to production environment
- Monitor logs for any path resolution errors

## Total Timeline: 8-12 days

This implementation plan provides a comprehensive approach to removing URNs from Eulogos and establishing the catalog-based path resolution as the only method of accessing texts.
