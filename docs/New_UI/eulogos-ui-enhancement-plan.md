# Eulogos UI Enhancement Plan: Author-Grouped Text Display

## Overview

This plan outlines the steps needed to modify the Eulogos interface to implement a hierarchical author-grouped view while maintaining the referencing system integrity. The implementation will follow these key requirements:

- Group works by author with collapsible sections
- Display authors with century and type information
- Provide visual indicators for different content types and status
- Maintain persistent state during user session
- Support hierarchical display (Authors → Works → Editions/Translations)
- Implement comprehensive filtering options
- Preserve the canonical path-based reference system

## Implementation Steps

### 1. Catalog Service Enhancement

Modify `app/services/catalog_service.py` to support hierarchical data retrieval without changing the underlying data model:

```python
def get_hierarchical_texts(self, include_archived: bool = False) -> Dict[str, Dict]:
    """Get texts organized hierarchically by author.
    
    Args:
        include_archived: Whether to include archived texts
        
    Returns:
        Dictionary of authors with their texts organized by work
    """
    if not self._catalog:
        return {}
    
    # Filter texts
    texts = self._catalog.texts if include_archived else [
        text for text in self._catalog.texts if not text.archived
    ]
    
    # Build hierarchical structure
    hierarchical = {}
    
    for text in texts:
        # Extract work identifier from path
        # Example path: tlg0012/tlg001/tlg0012.tlg001.perseus-grc2.xml
        path_parts = text.path.split('/')
        if len(path_parts) >= 2:
            author_id = path_parts[0]
            work_id = path_parts[1]
        else:
            # Fallback for non-standard paths
            author_id = text.author
            work_id = text.title
        
        # Ensure author exists in hierarchical structure
        if text.author not in hierarchical:
            # Extract century and type from metadata if available
            century = text.metadata.get("century", "Unknown")
            author_type = text.metadata.get("type", "Unknown")
            
            hierarchical[text.author] = {
                "metadata": {
                    "century": century,
                    "type": author_type
                },
                "works": {}
            }
        
        # Ensure work exists for this author
        if work_id not in hierarchical[text.author]["works"]:
            hierarchical[text.author]["works"][work_id] = {
                "title": None,  # Will set from first text
                "texts": []
            }
        
        # Set work title if not yet set
        if hierarchical[text.author]["works"][work_id]["title"] is None:
            hierarchical[text.author]["works"][work_id]["title"] = text.title
        
        # Add text to work
        hierarchical[text.author]["works"][work_id]["texts"].append(text)
    
    return hierarchical

def get_filtered_hierarchical_texts(
    self, 
    era: Optional[str] = None,
    century: Optional[str] = None,
    author_type: Optional[str] = None,
    query: Optional[str] = None,
    show_favorites: bool = False,
    include_archived: bool = False
) -> Dict[str, Dict]:
    """Get filtered texts organized hierarchically by author.
    
    Args:
        era: Optional era filter (pre-Socratic, Hellenistic, Imperial, Late Antiquity)
        century: Optional century filter
        author_type: Optional author type filter
        query: Optional search query for titles or author names
        show_favorites: Whether to show only favorite texts
        include_archived: Whether to include archived texts
        
    Returns:
        Dictionary of authors with their texts organized by work
    """
    if not self._catalog:
        return {}
    
    # Start with all texts
    texts = self._catalog.texts
    
    # Apply filters
    if not include_archived:
        texts = [text for text in texts if not text.archived]
    
    if show_favorites:
        texts = [text for text in texts if text.favorite]
    
    if query:
        query = query.lower()
        texts = [
            text for text in texts 
            if query in text.title.lower() or query in text.author.lower()
        ]
    
    # Build hierarchical structure
    hierarchical = {}
    
    for text in texts:
        # Skip if author metadata doesn't match filters
        author_metadata = text.metadata.get("author_metadata", {})
        text_century = author_metadata.get("century")
        text_era = author_metadata.get("era")
        text_author_type = author_metadata.get("type")
        
        if century and text_century and text_century != century:
            continue
            
        if era and text_era and text_era != era:
            continue
            
        if author_type and text_author_type and text_author_type != author_type:
            continue
        
        # Extract work identifier from path (same logic as get_hierarchical_texts)
        path_parts = text.path.split('/')
        if len(path_parts) >= 2:
            author_id = path_parts[0]
            work_id = path_parts[1]
        else:
            author_id = text.author
            work_id = text.title
        
        # Ensure author exists in hierarchical structure
        if text.author not in hierarchical:
            hierarchical[text.author] = {
                "metadata": {
                    "century": text_century or "Unknown",
                    "type": text_author_type or "Unknown",
                    "era": text_era or "Unknown"
                },
                "works": {}
            }
        
        # Ensure work exists for this author
        if work_id not in hierarchical[text.author]["works"]:
            hierarchical[text.author]["works"][work_id] = {
                "title": None,
                "texts": []
            }
        
        # Set work title if not yet set
        if hierarchical[text.author]["works"][work_id]["title"] is None:
            hierarchical[text.author]["works"][work_id]["title"] = text.title
        
        # Add text to work
        hierarchical[text.author]["works"][work_id]["texts"].append(text)
    
    return hierarchical

def get_eras(self) -> List[str]:
    """Get all unique eras from author metadata.
    
    Returns:
        List of era names
    """
    if not self._catalog:
        return []
    
    eras = set()
    for text in self._catalog.texts:
        author_metadata = text.metadata.get("author_metadata", {})
        era = author_metadata.get("era")
        if era:
            eras.add(era)
    
    return sorted(eras)

def get_centuries(self) -> List[str]:
    """Get all unique centuries from author metadata.
    
    Returns:
        List of centuries
    """
    if not self._catalog:
        return []
    
    centuries = set()
    for text in self._catalog.texts:
        author_metadata = text.metadata.get("author_metadata", {})
        century = author_metadata.get("century")
        if century:
            centuries.add(century)
    
    return sorted(centuries)

def get_author_types(self) -> List[str]:
    """Get all unique author types from metadata.
    
    Returns:
        List of author types
    """
    if not self._catalog:
        return []
    
    types = set()
    for text in self._catalog.texts:
        author_metadata = text.metadata.get("author_metadata", {})
        author_type = author_metadata.get("type")
        if author_type:
            types.add(author_type)
    
    return sorted(types)
```

### 2. Browse Router Modification

Update `app/routers/browse.py` to use the new hierarchical data structure:

```python
@router.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Render home page (redirects to browse)."""
    return templates.TemplateResponse(
        "browse.html", 
        {
            "request": request,
            "hierarchical_texts": catalog_service.get_hierarchical_texts(),
            "authors": catalog_service.get_all_authors(),
            "languages": catalog_service.get_all_languages(),
            "eras": catalog_service.get_eras(),
            "centuries": catalog_service.get_centuries(),
            "author_types": catalog_service.get_author_types(),
        }
    )


@router.get("/browse", response_class=HTMLResponse)
async def browse_texts(
    request: Request,
    author: Optional[str] = None,
    language: Optional[str] = None,
    era: Optional[str] = None,
    century: Optional[str] = None,
    author_type: Optional[str] = None,
    query: Optional[str] = None,
    show_favorites: bool = False,
    catalog_service: CatalogService = Depends(get_catalog_service)
):
    """Browse texts with optional filtering."""
    # Determine which texts to show based on filters
    if author:
        # Single author view (flat list)
        texts = catalog_service.get_texts_by_author(author)
        hierarchical_texts = {}  # Not used in single author view
    else:
        # Hierarchical view with filtering
        texts = []  # Not used in hierarchical view
        hierarchical_texts = catalog_service.get_filtered_hierarchical_texts(
            era=era,
            century=century,
            author_type=author_type,
            query=query,
            show_favorites=show_favorites
        )
    
    # Render browse template
    return templates.TemplateResponse(
        "browse.html", 
        {
            "request": request,
            "texts": texts,
            "hierarchical_texts": hierarchical_texts,
            "authors": catalog_service.get_all_authors(),
            "languages": catalog_service.get_all_languages(),
            "eras": catalog_service.get_eras(),
            "centuries": catalog_service.get_centuries(),
            "author_types": catalog_service.get_author_types(),
            "current_author": author,
            "current_language": language,
            "current_era": era,
            "current_century": century,
            "current_author_type": author_type,
            "query": query,
            "show_favorites": show_favorites,
        }
    )
```

### 3. Browse Template Redesign

Modify `app/templates/browse.html` to implement the hierarchical author-grouped interface:

```html
{% extends "base.html" %}

{% block title %}Browse Texts - Eulogos{% endblock %}

{% block header_actions %}
<a href="/" class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg px-4 py-2">
    All Texts
</a>
<a href="/browse?show_favorites=true" class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg px-4 py-2">
    Favorites
</a>
{% endblock %}

{% block content %}
<div x-data="{ 
    selectedTab: 'texts',
    filterOpen: false,
    expandedAuthors: JSON.parse(localStorage.getItem('expandedAuthors') || '{}'),
    
    toggleAuthor(author) {
        this.expandedAuthors[author] = !this.expandedAuthors[author];
        localStorage.setItem('expandedAuthors', JSON.stringify(this.expandedAuthors));
    },
    
    isAuthorExpanded(author) {
        return this.expandedAuthors[author] || false;
    }
}">
    <!-- Browse header -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">
            {% if current_author %}
                Texts by {{ current_author }}
            {% elif current_language %}
                Texts in {{ current_language }}
            {% elif current_era %}
                {{ current_era }} Era Texts
            {% elif current_century %}
                {{ current_century }} Century Texts
            {% elif current_author_type %}
                {{ current_author_type }} Texts
            {% elif query %}
                Search Results for "{{ query }}"
            {% elif show_favorites %}
                Favorite Texts
            {% else %}
                Browse Texts by Author
            {% endif %}
        </h1>
        
        {% if current_author or current_language or query or show_favorites or current_era or current_century or current_author_type %}
        <p class="mt-2">
            <a href="/" class="text-blue-600 hover:text-blue-800 font-medium">
                &larr; Back to all texts
            </a>
        </p>
        {% endif %}
    </div>
    
    <!-- Filter toolbar -->
    <div class="mb-6 flex flex-wrap gap-2 justify-between items-center">
        <div class="flex flex-wrap gap-2">
            <!-- Era filter dropdown -->
            <div class="relative" x-data="{ open: false }">
                <button @click="open = !open" class="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <span>Era: {{ current_era or 'All' }}</span>
                    <svg class="ml-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </button>
                
                <div x-show="open" @click.away="open = false" class="origin-top-right absolute left-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
                    <div class="py-1">
                        <a href="/browse" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">All Eras</a>
                        {% for era_name in eras %}
                        <a href="/browse?era={{ era_name }}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 {% if current_era == era_name %}bg-gray-100{% endif %}">{{ era_name }}</a>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <!-- Century filter dropdown -->
            <div class="relative" x-data="{ open: false }">
                <button @click="open = !open" class="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <span>Century: {{ current_century or 'All' }}</span>
                    <svg class="ml-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </button>
                
                <div x-show="open" @click.away="open = false" class="origin-top-right absolute left-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
                    <div class="py-1">
                        <a href="/browse" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">All Centuries</a>
                        {% for century_name in centuries %}
                        <a href="/browse?century={{ century_name }}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 {% if current_century == century_name %}bg-gray-100{% endif %}">{{ century_name }}</a>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <!-- Author type filter dropdown -->
            <div class="relative" x-data="{ open: false }">
                <button @click="open = !open" class="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">
                    <span>Type: {{ current_author_type or 'All' }}</span>
                    <svg class="ml-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </button>
                
                <div x-show="open" @click.away="open = false" class="origin-top-right absolute left-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
                    <div class="py-1">
                        <a href="/browse" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">All Types</a>
                        {% for type_name in author_types %}
                        <a href="/browse?author_type={{ type_name }}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 {% if current_author_type == type_name %}bg-gray-100{% endif %}">{{ type_name }}</a>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Search form -->
        <div class="flex-grow max-w-md ml-auto">
            <form action="/browse" method="GET" class="flex">
                <input 
                    type="text" 
                    name="query" 
                    value="{{ query }}" 
                    placeholder="Search authors or texts..." 
                    class="flex-grow px-4 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </button>
            </form>
        </div>
    </div>
    
    {% if current_author %}
        <!-- Single author view (flat list) -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {% for text in texts %}
            <div class="relative bg-white rounded-lg shadow border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
                <div class="p-5">
                    <h3 class="text-lg font-bold text-gray-900 mb-2 line-clamp-2">{{ text.title }}</h3>
                    <p class="text-sm text-gray-500 mb-4">
                        <span class="inline-block bg-blue-100 text-blue-800 rounded-full px-2 py-1 text-xs">{{ text.language }}</span>
                    </p>
                    
                    <div class="flex justify-between items-center">
                        <a href="/read/{{ text.path }}" class="text-blue-600 hover:text-blue-800 font-medium">
                            Read text &rarr;
                        </a>
                        
                        <div class="flex space-x-2">
                            <button
                                hx-post="/favorite/{{ text.path }}"
                                hx-swap="none"
                                class="text-gray-400 hover:text-yellow-500 focus:outline-none"
                                onclick="this.classList.toggle('text-yellow-500'); this.classList.toggle('text-gray-400');"
                                title="Add to favorites"
                            >
                                {% if text.favorite %}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
                                {% else %}
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                                {% endif %}
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                            </button>
                            
                            <button
                                hx-post="/archive/{{ text.path }}"
                                hx-swap="none"
                                class="text-gray-400 hover:text-red-500 focus:outline-none"
                                title="Archive text"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <!-- Hierarchical author-grouped view -->
        <div class="space-y-6">
            {% for author_name, author_data in hierarchical_texts.items() %}
                <div class="border border-gray-200 rounded-lg overflow-hidden bg-white">
                    <!-- Author header (always visible) -->
                    <div class="flex justify-between items-center p-4 bg-gray-50 cursor-pointer" @click="toggleAuthor('{{ author_name }}')">
                        <div class="flex flex-grow items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-gray-500 transition-transform duration-200" :class="{'rotate-90': isAuthorExpanded('{{ author_name }}')}" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                            </svg>
                            <h2 class="text-lg font-semibold">{{ author_name }}</h2>
                            <div class="ml-4 text-sm text-gray-500">
                                {% if author_data.metadata.century != "Unknown" %}
                                    <span class="inline-block bg-gray-100 text-gray-800 rounded-full px-2 py-1 text-xs mr-2">{{ author_data.metadata.century }}</span>
                                {% endif %}
                                {% if author_data.metadata.type != "Unknown" %}
                                    <span class="inline-block bg-gray-100 text-gray-800 rounded-full px-2 py-1 text-xs">{{ author_data.metadata.type }}</span>
                                {% endif %}
                            </div>
                        </div>
                        
                        <div class="flex space-x-2">
                            <a href="/browse?author={{ author_name }}" class="text-blue-600 hover:text-blue-800 text-sm font-medium p-1">
                                View all
                            </a>
                        </div>
                    </div>
                    
                    <!-- Works and texts (collapsible) -->
                    <div x-show="isAuthorExpanded('{{ author_name }}')" x-transition class="px-4 pb-4 pt-2 divide-y divide-gray-100">
                        {% for work_id, work_data in author_data.works.items() %}
                            <div class="py-3">
                                <h3 class="font-medium text-gray-800 mb-2">{{ work_data.title }}</h3>
                                <ul class="space-y-2 pl-6">
                                    {% for text in work_data.texts %}
                                        <li class="flex justify-between items-center">
                                            <div class="flex items-center">
                                                <a href="/read/{{ text.path }}" class="text-blue-600 hover:text-blue-800">
                                                    {{ text.title }}
                                                </a>
                                                <span class="inline-block bg-blue-100 text-blue-800 rounded-full px-2 py-0.5 text-xs ml-2">{{ text.language }}</span>
                                            </div>
                                            
                                            <div class="flex space-x-2">
                                                <button
                                                    hx-post="/favorite/{{ text.path }}"
                                                    hx-swap="none"
                                                    class="text-gray-400 hover:text-yellow-500 focus:outline-none"
                                                    onclick="event.stopPropagation(); this.classList.toggle('text-yellow-500'); this.classList.toggle('text-gray-400');"
                                                    title="Add to favorites"
                                                >
                                                    {% if text.favorite %}
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
                                                    {% else %}
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                                    {% endif %}
                                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                                    </svg>
                                                </button>
                                                
                                                <button
                                                    hx-post="/archive/{{ text.path }}"
                                                    hx-swap="none"
                                                    class="text-gray-400 hover:text-red-500 focus:outline-none"
                                                    onclick="event.stopPropagation();"
                                                    title="{% if text.archived %}Unarchive text{% else %}Archive text{% endif %}"
                                                >
                                                    {% if text.archived %}
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                                                    </svg>
                                                    {% else %}
                                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                                                    </svg>
                                                    {% endif %}
                                                </button>
                                            </div>
                                        </li>
                                    {% endfor %}
                                </ul>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            {% endfor %}
        </div>
    {% endif %}
    
    <!-- No results message -->
    {% if (texts|length == 0 and current_author) or (hierarchical_texts|length == 0 and not current_author) %}
    <div class="text-center py-12">
        <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900">No texts found</h3>
        <p class="mt-2 text-gray-500">
            {% if query %}
            No texts matching "{{ query }}" were found.
            {% elif current_author %}
            No texts by {{ current_author }} were found.
            {% elif current_language %}
            No texts in {{ current_language }} were found.
            {% elif current_era %}
            No texts from the {{ current_era }} era were found.
            {% elif current_century %}
            No texts from the {{ current_century }} century were found.
            {% elif current_author_type %}
            No texts of type {{ current_author_type }} were found.
            {% elif show_favorites %}
            You haven't added any texts to your favorites yet.
            {% else %}
            No texts are available in the catalog.
            {% endif %}
        </p>
    </div>
    {% endif %}
</div>
{% endblock %}

{% block scripts %}
<script>
    // Initialize Alpine.js data persistence
    document.addEventListener('alpine:init', () => {
        // Expand authors by default on first load
        if (!localStorage.getItem('expandedAuthors')) {
            // Get first few authors and expand them
            const authorHeaders = document.querySelectorAll('.author-header');
            const initialExpanded = {};
            
            // Expand first 3 authors by default
            for (let i = 0; i < Math.min(3, authorHeaders.length); i++) {
                const authorName = authorHeaders[i].dataset.author;
                if (authorName) {
                    initialExpanded[authorName] = true;
                }
            }
            
            localStorage.setItem('expandedAuthors', JSON.stringify(initialExpanded));
        }
    });
</script>
{% endblock %}
```

### 4. Additional Helper Templates

Create a partial template for the author list in `app/templates/partials/author_list.html`:

```html
<div class="space-y-2">
    {% for author_name, author_data in authors.items() %}
    <div class="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
        <div>
            <a href="/browse?author={{ author_name }}" class="text-blue-600 hover:text-blue-800">
                {{ author_name }}
            </a>
            {% if author_data.metadata.century %}
            <span class="text-xs text-gray-500 ml-2">{{ author_data.metadata.century }}</span>
            {% endif %}
        </div>
        <span class="text-xs text-gray-500">{{ author_data.work_count }} works</span>
    </div>
    {% endfor %}
</div>
```

### 5. JavaScript Enhancements

Add Alpine.js code to handle collapsible sections and persistent state in `app/static/js/main.js`:

```javascript
/**
 * Initialize Alpine.js data for author collapsible sections
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('authorBrowser', () => ({
        expandedAuthors: {},
        
        init() {
            // Load expanded state from localStorage
            try {
                const saved = localStorage.getItem('expandedAuthors');
                if (saved) {
                    this.expandedAuthors = JSON.parse(saved);
                }
            } catch (e) {
                console.error('Error loading expanded authors state:', e);
                this.expandedAuthors = {};
            }
        },
        
        toggleAuthor(author) {
            this.expandedAuthors[author] = !this.expandedAuthors[author];
            this.saveState();
        },
        
        isExpanded(author) {
            return this.expandedAuthors[author] || false;
        },
        
        saveState() {
            localStorage.setItem('expandedAuthors', JSON.stringify(this.expandedAuthors));
        }
    }));
});
```

## Testing Strategy

1. Implement changes incrementally, testing each component:
   - First catalog service modifications
   - Then browse router updates
   - Finally template changes

2. Test with small subsets of data before deploying with full catalog

3. Create a testing checklist:
   - Verify hierarchical display works correctly
   - Check that all filtering options function
   - Ensure favorite/archive toggles work
   - Confirm collapsible sections maintain state
   - Test search functionality
   - Validate that all links use the correct paths

## Rollback Plan

1. Keep backup copies of all modified files

2. Implement a feature flag in the configuration:
   ```python
   # In app/config.py
   hierarchical_browse: bool = Field(
       True, 
       description="Enable hierarchical browsing by author"
   )
   ```

3. Use the feature flag in the router:
   ```python
   if settings.hierarchical_browse:
       # Use new hierarchical browsing
       ...
   else:
       # Fallback to original grid layout
       ...
   ```

4. Create a rollback script that can quickly disable the feature if issues arise

## Deployment Plan

1. Implement the changes in a development environment
2. Test thoroughly with real data
3. Deploy to staging environment
4. Conduct user acceptance testing
5. Deploy to production with feature flag enabled
6. Monitor for issues and be prepared to disable if necessary
7. After confirming stability, clean up backup code and feature flags

## Conclusion

This implementation carefully enhances the Eulogos UI to provide a hierarchical author-grouped view while preserving the canonical path-based reference system. The changes are focused on the presentation layer, ensuring the underlying data model remains intact.

The plan provides a comprehensive approach that:
- Respects the existing codebase structure
- Maintains backward compatibility
- Enhances the user experience with better organization
- Adds comprehensive filtering options
- Preserves all existing functionality
- Includes robust testing and rollback strategies
