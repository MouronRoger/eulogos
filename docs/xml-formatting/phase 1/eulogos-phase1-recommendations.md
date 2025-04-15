# Eulogos XML Export System: Phase 1 Completion Recommendations

## Overview

Based on a thorough code review of the Eulogos XML formatting and export system implementation, Phase 1 (Core Reference Handling) is mostly complete with some remaining items that need to be addressed before moving fully to Phase 2 (Export Service).

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| URN Model | ✅ Complete | Two implementations exist (utility class and Pydantic model) |
| Enhanced XMLProcessorService | ✅ Complete | All required reference handling capabilities implemented |
| Reader Interface | ⚠️ Partially Complete | Basic functionality implemented but lacks reference navigation |
| Export Functionality | 🔄 In Progress | Basic implementation started (part of Phase 2) |

## Recommendations

### 1. Complete Reader Interface with Reference Navigation

The reader interface should be enhanced to utilize the reference extraction and navigation capabilities implemented in the XMLProcessorService.

**Tasks:**

- Update `app/routers/reader.py` to:
  ```python
  @router.get("/read/{urn}")
  async def read_text(
      request: Request,
      urn: str,
      reference: Optional[str] = None,
      catalog_service: CatalogService = Depends(get_catalog_service),
      xml_processor: XMLProcessorService = Depends(get_xml_processor)
  ):
      """Read a text with optional reference navigation.

      Args:
          request: FastAPI request object
          urn: The URN of the text to read
          reference: Optional reference to navigate to
          catalog_service: CatalogService instance
          xml_processor: XMLProcessorService instance

      Returns:
          HTMLResponse with rendered template
      """
      # Parse URN
      try:
          urn_obj = URN(value=urn)
      except ValueError as e:
          raise HTTPException(status_code=400, detail=f"Invalid URN: {e}")

      # Get text from catalog
      text = catalog_service.get_text_by_urn(urn)
      if not text:
          raise HTTPException(status_code=404, detail=f"Text not found: {urn}")

      try:
          # Load XML content
          xml_root = xml_processor.load_xml(urn_obj)

          # Get adjacent references
          adjacent_refs = xml_processor.get_adjacent_references(xml_root, reference)

          # Transform to HTML with reference highlighting
          html_content = xml_processor.transform_to_html(xml_root, reference)

          # Render template
          return templates.TemplateResponse(
              "reader.html",
              {
                  "request": request,
                  "text": text,
                  "content": html_content,
                  "urn": urn,
                  "current_ref": reference,
                  "prev_ref": adjacent_refs["prev"],
                  "next_ref": adjacent_refs["next"],
              }
          )
      except Exception as e:
          # Return error message
          return templates.TemplateResponse(
              "reader.html",
              {
                  "request": request,
                  "text": text,
                  "content": f"<p><em>Error processing text: {str(e)}</em></p>",
                  "urn": urn,
              },
              status_code=500
          )
  ```

- Update `app/templates/reader.html` to include reference navigation UI:
  ```html
  <!-- Reference Navigation -->
  {% if current_ref %}
  <div class="mb-4 flex items-center justify-between bg-gray-100 p-2 rounded">
      <span class="text-gray-600">Currently viewing: <strong>{{ current_ref }}</strong></span>
      <div class="flex space-x-2">
          {% if prev_ref %}
          <a href="/read/{{ urn }}?reference={{ prev_ref }}" class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
              Previous
          </a>
          {% else %}
          <button disabled class="px-3 py-1 bg-gray-400 text-white rounded cursor-not-allowed">
              Previous
          </button>
          {% endif %}

          {% if next_ref %}
          <a href="/read/{{ urn }}?reference={{ next_ref }}" class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
              Next
          </a>
          {% else %}
          <button disabled class="px-3 py-1 bg-gray-400 text-white rounded cursor-not-allowed">
              Next
          </button>
          {% endif %}
      </div>
  </div>
  {% endif %}

  <!-- Table of Contents / Reference Browser -->
  <div x-data="{ showToc: false }" class="mb-4">
      <button
          @click="showToc = !showToc"
          class="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center"
      >
          <span x-text="showToc ? 'Hide References' : 'Show References'"></span>
          <svg x-show="!showToc" class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
          </svg>
          <svg x-show="showToc" class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>
          </svg>
      </button>

      <div x-show="showToc" class="mt-2 p-3 border rounded max-h-64 overflow-y-auto bg-white">
          <div hx-get="/api/references/{{ urn }}" hx-trigger="load" hx-target="this">
              Loading references...
          </div>
      </div>
  </div>
  ```

- Create a new endpoint in `app/routers/reader.py` to fetch references:
  ```python
  @router.get("/api/references/{urn}")
  async def get_references(
      urn: str,
      xml_processor: XMLProcessorService = Depends(get_xml_processor)
  ):
      """Get references for a text.

      Args:
          urn: The URN of the text
          xml_processor: XMLProcessorService instance

      Returns:
          HTML with references
      """
      try:
          # Parse URN
          urn_obj = URN(value=urn)

          # Load XML content
          xml_root = xml_processor.load_xml(urn_obj)

          # Extract references
          references = xml_processor.extract_references(xml_root)

          # Sort references naturally
          sorted_refs = sorted(references.keys(),
                              key=lambda x: [int(n) if n.isdigit() else n for n in x.split(".")])

          # Build reference tree HTML
          html = ['<ul class="space-y-1">']

          for ref in sorted_refs:
              html.append(f'<li class="hover:bg-gray-100 rounded">')
              html.append(f'<a href="/read/{urn}?reference={ref}" class="block px-2 py-1">')
              html.append(f'<span class="font-medium">{ref}</span>')
              html.append(f'</a>')
              html.append(f'</li>')

          html.append('</ul>')

          return HTMLResponse(content="".join(html))

      except Exception as e:
          return HTMLResponse(
              content=f'<div class="text-red-500">Error loading references: {str(e)}</div>',
              status_code=500
          )
  ```

### 2. Standardize URN Implementation

Currently, there are two URN implementations: a utility class in `app/utils/urn.py` and a Pydantic model in `app/models/urn.py`. To ensure consistency and maintainability, the codebase should standardize on a single implementation.

**Tasks:**

- Update all code that uses `app/utils/urn.py` to use the Pydantic model from `app/models/urn.py` instead
- Add deprecation warnings to `app/utils/urn.py` to discourage its use:
  ```python
  import warnings

  class CtsUrn:
      """Utility class for CTS URN parsing and manipulation.

      Note:
          This class is deprecated. Use the URN model from app.models.urn instead.
      """

      def __init__(self, urn_string: str):
          """Initialize a CtsUrn object.

          Args:
              urn_string: The CTS URN string

          Raises:
              ValueError: If the URN is invalid
          """
          warnings.warn(
              "CtsUrn is deprecated. Use the URN model from app.models.urn instead.",
              DeprecationWarning,
              stacklevel=2
          )
          # Rest of the implementation...
  ```

- Update the import statements in existing files to use the new model:
  ```python
  # OLD
  from app.utils.urn import CtsUrn

  # NEW
  from app.models.urn import URN
  ```

### 3. Add Comprehensive Integration Tests

To ensure that the components work together correctly, add integration tests that verify the complete functionality from URN parsing to reference navigation in the reader interface.

**Tasks:**

- Create `tests/test_reader_reference_navigation.py`:
  ```python
  """Integration tests for reader with reference navigation."""

  import pytest
  from fastapi.testclient import TestClient
  from unittest.mock import MagicMock

  from app.main import app
  from app.models.urn import URN
  from app.services.xml_processor_service import XMLProcessorService


  @pytest.fixture
  def mock_xml_processor():
      """Create a mock XMLProcessorService."""
      processor = MagicMock(spec=XMLProcessorService)

      # Mock load_xml to return a mock XML root
      processor.load_xml.return_value = MagicMock()

      # Mock extract_references to return a mock references dict
      references = {
          "1": MagicMock(),
          "1.1": MagicMock(),
          "1.2": MagicMock()
      }
      processor.extract_references.return_value = references

      # Mock get_adjacent_references to return mock prev/next refs
      processor.get_adjacent_references.return_value = {
          "prev": "1.1",
          "next": "1.3"
      }

      # Mock transform_to_html to return a simple HTML string
      processor.transform_to_html.return_value = "<div>Test content</div>"

      return processor


  @pytest.fixture
  def client(mock_xml_processor):
      """Create a test client with mocked dependencies."""
      app.dependency_overrides[get_xml_processor] = lambda: mock_xml_processor

      # Also mock catalog_service to return a dummy text
      mock_catalog = MagicMock()
      mock_catalog.get_text_by_urn.return_value = {
          "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
          "group_name": "Homer",
          "work_name": "Iliad",
          "language": "grc"
      }
      app.dependency_overrides[get_catalog_service] = lambda: mock_catalog

      yield TestClient(app)
      app.dependency_overrides = {}


  class TestReaderReferenceNavigation:
      """Tests for reader reference navigation."""

      def test_read_text_with_reference(self, client, mock_xml_processor):
          """Test reading a text with a specific reference."""
          response = client.get("/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.2")

          assert response.status_code == 200

          # Check that the correct methods were called
          mock_xml_processor.load_xml.assert_called_once()
          mock_xml_processor.get_adjacent_references.assert_called_once_with(
              mock_xml_processor.load_xml.return_value, "1.2"
          )
          mock_xml_processor.transform_to_html.assert_called_once_with(
              mock_xml_processor.load_xml.return_value, "1.2"
          )

          # Check that the response contains navigation elements
          html = response.text
          assert "Currently viewing: <strong>1.2</strong>" in html
          assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.1"' in html
          assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.3"' in html

      def test_get_references(self, client, mock_xml_processor):
          """Test the references API endpoint."""
          response = client.get("/api/references/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

          assert response.status_code == 200

          # Check that the correct methods were called
          mock_xml_processor.load_xml.assert_called_once()
          mock_xml_processor.extract_references.assert_called_once_with(
              mock_xml_processor.load_xml.return_value
          )

          # Check that the response contains reference links
          html = response.text
          assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1"' in html
          assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.1"' in html
          assert 'href="/read/urn:cts:greekLit:tlg0012.tlg001.perseus-grc2?reference=1.2"' in html
  ```

## Conclusion

Completing these remaining items will finalize Phase 1 of the Eulogos XML formatting and export system implementation, providing a solid foundation for the Phase 2 work on the Export Service. The core components (URN Model and Enhanced XMLProcessorService) are already well-implemented, and these recommendations focus on integrating them effectively into the reader interface and ensuring consistency across the codebase.
