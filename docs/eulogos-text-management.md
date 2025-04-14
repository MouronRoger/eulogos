# Eulogos Text Management UI Implementation

This document outlines the implementation for a front-end text management interface in the Eulogos project, focusing on viewing, archiving, favoriting, and deleting texts - with emphasis on pre-Socratic and Hellenistic texts.

## 1. Data Model Extensions

First, let's extend the existing catalog model to support favoriting:

```python
# app/models/catalog.py
class Text(BaseModel):
    """Text model with author reference."""
    
    urn: str
    group_name: str
    work_name: str
    language: str
    wordcount: int
    scaife: Optional[str] = None
    author_id: Optional[str] = None
    archived: bool = False  # Already exists
    favorite: bool = False  # New field for marking favorites
```

## 2. CatalogService Extension

```python
# app/services/catalog_service.py
def toggle_text_favorite(self, urn: str) -> bool:
    """Toggle favorite status for a text."""
    if urn not in self._texts_by_urn:
        return False
        
    text = self._texts_by_urn[urn]
    text.favorite = not text.favorite
    self._save_catalog()
    return True
```

## 3. API Endpoints

### Text Management Endpoints

```python
# app/routers/texts.py
@router.post("/texts/{urn}/archive")
async def archive_text(urn: str, archive: bool = True):
    """Archive or unarchive a text."""
    success = catalog_service.archive_text(urn, archive)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"status": "success", "archived": archive}
    
@router.post("/texts/{urn}/favorite")
async def favorite_text(urn: str):
    """Toggle favorite status for a text."""
    success = catalog_service.toggle_text_favorite(urn)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"status": "success"}
    
@router.delete("/texts/{urn}")
async def delete_text(urn: str, confirmation: bool = Query(False)):
    """Delete a text."""
    if not confirmation:
        raise HTTPException(status_code=400, detail="Confirmation required")
    
    success = catalog_service.delete_text(urn)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"status": "success"}
```

### Browse API

```python
# app/routers/browse.py
@router.get("/browse", response_class=HTMLResponse)
async def browse_texts(
    request: Request,
    show: str = Query("all", description="Filter by status: all, favorites, archived"),
    era: Optional[str] = Query(None, description="Filter by era: pre-socratic, hellenistic, imperial, late-antiquity"),
    search: Optional[str] = Query(None, description="Search term")
):
    """Browse texts with filtering options."""
    # Get all authors
    authors = catalog_service.get_all_authors(include_archived=(show == "archived"))
    
    # Apply era filter
    if era:
        # Map era to century ranges
        era_ranges = {
            "pre-socratic": (-7, -5),  # 7th to 5th century BCE
            "hellenistic": (-4, -1),   # 4th to 1st century BCE
            "imperial": (1, 3),        # 1st to 3rd century CE
            "late-antiquity": (4, 6)   # 4th to 6th century CE
        }
        
        if era in era_ranges:
            start_century, end_century = era_ranges[era]
            authors = [
                author for author in authors
                if start_century <= author.century <= end_century
            ]
    
    # Process authors to include their works
    result_authors = []
    for author in authors:
        # Get works for this author
        works = catalog_service.get_texts_by_author(
            author.id,
            include_archived=(show == "archived")
        )
        
        # Filter by favorites if requested
        if show == "favorites":
            works = [work for work in works if work.favorite]
            # Skip author if no favorite works
            if not works:
                continue
        
        # Apply search filter if provided
        if search:
            works = [
                work for work in works
                if search.lower() in work.work_name.lower() or search.lower() in author.name.lower()
            ]
            # Skip author if no matching works
            if not works:
                continue
        
        # Add author with filtered works to results
        author_data = author.dict()
        author_data["works"] = [work.dict() for work in works]
        result_authors.append(author_data)
    
    # Sort authors by name
    result_authors.sort(key=lambda a: a["name"])
    
    # Render the template
    return templates.TemplateResponse(
        "partials/author_works_tree.html",
        {
            "request": request,
            "authors": result_authors,
            "show": show,
            "era": era,
            "search": search
        }
    )
```

## 4. Frontend UI Template

```html
<!-- app/templates/partials/author_works_tree.html -->
<div id="author-works-tree" class="overflow-auto p-4">
  <!-- Filter Controls -->
  <div class="mb-4 flex flex-wrap gap-2">
    <div class="filter-group">
      <label class="text-sm font-medium">Show:</label>
      <div class="flex space-x-2">
        <button 
          hx-get="/api/browse?show=all{% if era %}&era={{ era }}{% endif %}{% if search %}&search={{ search }}{% endif %}"
          hx-target="#author-works-tree"
          class="px-2 py-1 {{ 'bg-blue-600' if show == 'all' else 'bg-gray-600' }} text-white rounded text-sm"
        >All</button>
        <button 
          hx-get="/api/browse?show=favorites{% if era %}&era={{ era }}{% endif %}{% if search %}&search={{ search }}{% endif %}"
          hx-target="#author-works-tree"
          class="px-2 py-1 {{ 'bg-blue-600' if show == 'favorites' else 'bg-gray-600' }} text-white rounded text-sm"
        >Favorites</button>
        <button 
          hx-get="/api/browse?show=archived{% if era %}&era={{ era }}{% endif %}{% if search %}&search={{ search }}{% endif %}"
          hx-target="#author-works-tree"
          class="px-2 py-1 {{ 'bg-blue-600' if show == 'archived' else 'bg-gray-600' }} text-white rounded text-sm"
        >Archived</button>
      </div>
    </div>
    
    <div class="filter-group">
      <label class="text-sm font-medium">Era:</label>
      <div class="flex space-x-2">
        <button 
          hx-get="/api/browse?show={{ show }}&era=pre-socratic{% if search %}&search={{ search }}{% endif %}"
          hx-target="#author-works-tree"
          class="px-2 py-1 {{ 'bg-blue-600' if era == 'pre-socratic' else 'bg-gray-600' }} text-white rounded text-sm"
        >Pre-Socratic</button>
        <button 
          hx-get="/api/browse?show={{ show }}&era=hellenistic{% if search %}&search={{ search }}{% endif %}"
          hx-target="#author-works-tree"
          class="px-2 py-1 {{ 'bg-blue-600' if era == 'hellenistic' else 'bg-gray-600' }} text-white rounded text-sm"
        >Hellenistic</button>
        <button 
          hx-get="/api/browse?show={{ show }}&era=imperial{% if search %}&search={{ search }}{% endif %}"
          hx-target="#author-works-tree"
          class="px-2 py-1 {{ 'bg-blue-600' if era == 'imperial' else 'bg-gray-600' }} text-white rounded text-sm"
        >Imperial</button>
        <button 
          hx-get="/api/browse?show={{ show }}&era=late-antiquity{% if search %}&search={{ search }}{% endif %}"
          hx-target="#author-works-tree"
          class="px-2 py-1 {{ 'bg-blue-600' if era == 'late-antiquity' else 'bg-gray-600' }} text-white rounded text-sm"
        >Late Antiquity</button>
      </div>
    </div>
    
    <div class="filter-group flex-grow">
      <div class="flex">
        <input 
          type="text" 
          name="search" 
          value="{{ search or '' }}"
          placeholder="Search texts..." 
          class="px-3 py-2 border border-gray-300 rounded-l w-full focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
        <button
          hx-get="/api/browse?show={{ show }}{% if era %}&era={{ era }}{% endif %}&search=${this.previousElementSibling.value}"
          hx-target="#author-works-tree"
          class="px-4 py-2 bg-blue-600 text-white rounded-r"
        >
          Search
        </button>
      </div>
    </div>
  </div>
  
  <!-- No results message -->
  {% if authors|length == 0 %}
  <div class="text-center py-8">
    <h3 class="text-lg font-medium text-gray-700">No texts found</h3>
    <p class="text-gray-500">Try adjusting your filters</p>
  </div>
  {% endif %}
  
  <!-- Authors List -->
  <div class="space-y-2">
    {% for author in authors %}
    <div 
      id="author-{{ author.id }}" 
      class="author-item {{ 'opacity-70' if author.archived else '' }}"
      x-data="{ expanded: {{ 'true' if authors|length <= 5 else 'false' }} }"
    >
      <!-- Author heading -->
      <div class="flex items-center p-2 bg-gray-100 rounded cursor-pointer" @click="expanded = !expanded">
        <button class="mr-2 w-6 h-6 flex items-center justify-center">
          <span x-show="!expanded">+</span>
          <span x-show="expanded">-</span>
        </button>
        <h3 class="text-md font-medium flex-grow">
          {{ author.name }} 
          <span class="text-sm text-gray-500">{{ (author.century|abs ~ ' BCE') if author.century < 0 else (author.century ~ ' CE') }}</span>
        </h3>
        
        <!-- Author actions -->
        <div class="flex space-x-2">
          <button 
            hx-post="/api/authors/{{ author.id }}/archive?archive={{ not author.archived }}"
            hx-target="#author-works-tree"
            class="px-2 py-1 {{ 'bg-green-600' if author.archived else 'bg-gray-600' }} text-white rounded text-sm"
          >
            {{ 'Unarchive' if author.archived else 'Archive' }}
          </button>
        </div>
      </div>
      
      <!-- Works list for this author -->
      <div x-show="expanded" class="pl-8 mt-1 space-y-1">
        {% if author.works|length == 0 %}
        <div class="text-sm italic text-gray-500 p-2">No works</div>
        {% endif %}
        
        {% for work in author.works %}
        <div id="work-{{ work.urn }}" class="p-2 {{ 'opacity-70' if work.archived else '' }} {{ 'bg-yellow-50' if work.favorite else 'bg-white' }} border rounded">
          <div class="flex items-center">
            <h4 class="text-md flex-grow">
              <a href="/read/{{ work.urn }}" class="text-blue-600 hover:underline">
                {{ work.work_name }}
              </a>
              <span class="text-sm text-gray-500">{{ work.language }}</span>
            </h4>
            
            <!-- Text management actions -->
            <div class="flex space-x-1" x-data="{ showConfirmDelete: false }">
              <!-- Archive button -->
              <button 
                hx-post="/api/texts/{{ work.urn }}/archive?archive={{ not work.archived }}"
                hx-target="#author-works-tree"
                title="{{ 'Unarchive' if work.archived else 'Archive' }}"
                class="p-1 {{ 'text-green-600' if work.archived else 'text-gray-600' }} hover:bg-gray-100 rounded"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
              </button>
              
              <!-- Favorite button -->
              <button 
                hx-post="/api/texts/{{ work.urn }}/favorite"
                hx-target="#author-works-tree"
                title="{{ 'Unfavorite' if work.favorite else 'Favorite' }}"
                class="p-1 {{ 'text-yellow-600' if work.favorite else 'text-gray-600' }} hover:bg-gray-100 rounded"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="{{ 'currentColor' if work.favorite else 'none' }}" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
              
              <!-- Delete button -->
              <button 
                @click="showConfirmDelete = true"
                title="Delete"
                class="p-1 text-red-600 hover:bg-gray-100 rounded"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              
              <!-- Delete confirmation dialog -->
              <div 
                x-show="showConfirmDelete" 
                x-transition 
                class="absolute z-10 bg-white border rounded shadow-lg p-4 mt-2"
                @click.outside="showConfirmDelete = false"
              >
                <p class="text-sm mb-2">Are you sure you want to delete "{{ work.work_name }}"?</p>
                <div class="flex justify-end space-x-2">
                  <button 
                    @click="showConfirmDelete = false"
                    class="px-2 py-1 bg-gray-200 text-gray-800 rounded text-sm"
                  >Cancel</button>
                  <button 
                    hx-delete="/api/texts/{{ work.urn }}?confirmation=true"
                    hx-target="#author-works-tree"
                    class="px-2 py-1 bg-red-600 text-white rounded text-sm"
                  >Delete</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  </div>
</div>
```

## 5. Main Template Integration

This partial template can be included in the main page template:

```html
<!-- app/templates/browse.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browse Texts - Eulogos</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script src="https://unpkg.com/htmx.org@1.9.4" crossorigin="anonymous"></script>
    <script src="https://unpkg.com/alpinejs@3.13.0" crossorigin="anonymous" defer></script>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen flex flex-col">
        <!-- Header -->
        <header class="bg-blue-600 text-white shadow">
            <div class="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
                <h1 class="text-2xl font-bold">Eulogos</h1>
            </div>
        </header>
        
        <!-- Main Content -->
        <main class="flex-grow">
            <div class="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
                <h2 class="text-lg font-semibold mb-4">Browse Texts</h2>
                
                <!-- Include the Author-Works Tree -->
                {% include "partials/author_works_tree.html" %}
            </div>
        </main>
        
        <!-- Footer -->
        <footer class="bg-white border-t border-gray-200">
            <div class="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
                <p class="text-center text-sm text-gray-500">
                    Eulogos &copy; 2025
                </p>
            </div>
        </footer>
    </div>
</body>
</html>
```

## 6. Key Features

### Text Management Operations
- **Archive/Unarchive**: Hide texts temporarily without deleting them
- **Favorite**: Mark texts of special interest for easy access
- **Delete**: Permanently remove texts you don't want

### Rich Filtering Options
- **Status Filters**: Show all, favorites, or archived texts
- **Era Filters**: Focus on pre-Socratic, Hellenistic, Imperial, or Late Antiquity texts
- **Search**: Find texts by author name or title

### Visual Indicators
- Archived texts display with reduced opacity
- Favorited texts have a yellow background
- Collapsible author sections that auto-expand with small result sets

### User Experience Enhancements
- Confirmation dialogs for destructive actions
- HTMX for seamless page updates without full reloads
- Responsive UI with Tailwind CSS
- Maintaining filter state across interactions

## 7. Implementation Requirements

### Files to create or update:
1. `app/models/catalog.py` - Update the Text model with the favorite field
2. `app/services/catalog_service.py` - Add toggle_text_favorite method
3. `app/routers/texts.py` - Create endpoints for text management
4. `app/routers/browse.py` - Create browse API
5. `app/templates/partials/author_works_tree.html` - Create the tree component
6. `app/templates/browse.html` - Create the main browse page

### Dependencies:
- FastAPI for API endpoints
- HTMX for seamless interaction
- Alpine.js for client-side interactivity
- Tailwind CSS for styling
