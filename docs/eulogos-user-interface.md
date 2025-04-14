# Eulogos User Interface Design and Implementation

## 1. Overview

The Eulogos user interface is the primary way users will interact with the First1KGreek data collection. This document outlines the design and implementation of the user-facing components that enable browsing, searching, viewing, and downloading ancient Greek texts.

Unlike the administrative interface (which is focused on system management), the user interface is designed for scholars, students, and general readers who want to access and study the texts without needing to understand the underlying technical structure.

## 2. Core User Interface Components

### 2.1. Author-Works Tree Browser

The hierarchical author-works tree browser is the primary navigation mechanism for users to explore the corpus:

#### Features

- **Hierarchical Display**: Authors → Works → Editions/Translations
- **Alphabetical Sorting**: Default sorting by author name with alternative sort options
- **Collapsible Sections**: Expand/collapse authors to see their works
- **Visual Indicators**: Icons denoting different types of content (original Greek, translations)
- **Quick Preview**: Hover to see brief metadata about works and editions
- **Persistent State**: Remember expanded/collapsed state during session

#### Implementation

```html
<!-- templates/browse/author_tree.html -->
<div class="author-tree bg-white shadow rounded-lg" x-data="{ expandedAuthors: {} }">
  <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
    <h3 class="text-lg leading-6 font-medium text-gray-900">Browse Texts</h3>
    <div class="mt-2 flex flex-wrap gap-2">
      <button 
        class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm hover:bg-blue-200"
        @click="expandAll"
      >
        Expand All
      </button>
      <button 
        class="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm hover:bg-gray-200"
        @click="collapseAll"
      >
        Collapse All
      </button>
      
      <!-- Sort Controls -->
      <div class="flex-grow"></div>
      <select 
        id="sort-control"
        class="text-sm border-gray-300 rounded-md"
        hx-get="/browse"
        hx-target="#author-list"
        hx-trigger="change"
        name="sort"
      >
        <option value="name">Sort by Name</option>
        <option value="century">Sort by Century</option>
        <option value="work_count">Sort by Work Count</option>
      </select>
    </div>
  </div>
  
  <div class="author-list px-4 py-5 sm:px-6" id="author-list">
    {% for author in authors %}
    <div class="author-item mb-3">
      <div 
        class="flex items-center py-2 px-3 bg-gray-50 rounded-md cursor-pointer hover:bg-blue-50"
        @click="expandedAuthors['{{ author.id }}'] = !expandedAuthors['{{ author.id }}']"
        :class="{ 'bg-blue-50': expandedAuthors['{{ author.id }}'] }"
      >
        <div 
          class="mr-2 text-gray-500"
          :class="{ 'transform rotate-90': expandedAuthors['{{ author.id }}'] }"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </div>
        <span class="font-medium">{{ author.name }}</span>
        <span class="ml-2 text-sm text-gray-500">
          {% if author.century < 0 %}
          {{ abs(author.century) }} BCE
          {% else %}
          {{ author.century }} CE
          {% endif %}
        </span>
        <span class="ml-auto text-sm text-gray-500">{{ author.works|length }} works</span>
      </div>
      
      <!-- Works List (Collapsible) -->
      <div 
        class="pl-8 mt-2 space-y-2" 
        x-show="expandedAuthors['{{ author.id }}']" 
        x-transition:enter="transition ease-out duration-200"
        x-transition:enter-start="opacity-0 transform scale-95"
        x-transition:enter-end="opacity-100 transform scale-100"
      >
        {% for work in author.works %}
        <div class="work-item">
          <div 
            class="flex items-center py-1 px-3 rounded-md hover:bg-gray-100"
            hx-get="/browse/{{ author.id }}/{{ work.id }}"
            hx-target="#content-area"
          >
            <span class="flex-grow">{{ work.title }}</span>
            <div class="flex space-x-1">
              {% for edition in work.editions %}
              <span class="px-2 py-0.5 text-xs rounded bg-green-100 text-green-800">
                {{ edition.language }}
              </span>
              {% endfor %}
              {% for translation in work.translations %}
              <span class="px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-800">
                {{ translation.language }}
              </span>
              {% endfor %}
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

### 2.2. Filtering and Sorting Panel

A flexible filtering system allowing users to narrow down the corpus:

#### Features

- **Author Filtering**:
  - By century (timeline or range selector)
  - By type (dropdown: historian, poet, philosopher, etc.)
  - By name (text search with autocomplete)

- **Work Filtering**:
  - By language (primarily Greek, but also translations)
  - By word count (range slider)
  - By title (text search)
  - By content (full-text search)

- **Sorting Options**:
  - Authors: alphabetical, chronological, by work count
  - Works: alphabetical, by size, by language availability

#### Implementation

```html
<!-- templates/browse/filter_panel.html -->
<div class="filter-panel bg-white shadow rounded-lg mb-4">
  <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
    <div class="flex justify-between items-center">
      <h3 class="text-lg leading-6 font-medium text-gray-900">Filter Texts</h3>
      <button 
        class="text-sm text-blue-600 hover:text-blue-800" 
        hx-get="/browse"
        hx-target="#main-content"
      >
        Reset Filters
      </button>
    </div>
  </div>
  
  <div class="px-4 py-5 sm:px-6">
    <form hx-get="/browse" hx-target="#main-content" hx-trigger="change delay:500ms, search delay:500ms">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Author Filters -->
        <div>
          <label for="author-name" class="block text-sm font-medium text-gray-700 mb-1">
            Author Name
          </label>
          <input 
            type="text" 
            id="author-name" 
            name="author_name" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Homer, Plato"
            hx-get="/api/authors/autocomplete"
            hx-trigger="keyup delay:200ms"
            hx-target="#author-suggestions"
          >
          <div id="author-suggestions" class="absolute z-10 w-full bg-white shadow-lg rounded-md mt-1"></div>
        </div>
        
        <div>
          <label for="author-type" class="block text-sm font-medium text-gray-700 mb-1">
            Author Type
          </label>
          <select 
            id="author-type" 
            name="author_type" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Any Type</option>
            {% for type in author_types %}
            <option value="{{ type }}">{{ type }}</option>
            {% endfor %}
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Century
          </label>
          <div class="flex items-center space-x-2">
            <select 
              id="century-min" 
              name="century_min" 
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Any</option>
              {% for century in centuries %}
              <option value="{{ century }}">
                {% if century < 0 %}{{ abs(century) }} BCE{% else %}{{ century }} CE{% endif %}
              </option>
              {% endfor %}
            </select>
            <span>to</span>
            <select 
              id="century-max" 
              name="century_max" 
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Any</option>
              {% for century in centuries %}
              <option value="{{ century }}">
                {% if century < 0 %}{{ abs(century) }} BCE{% else %}{{ century }} CE{% endif %}
              </option>
              {% endfor %}
            </select>
          </div>
        </div>
        
        <!-- Work Filters -->
        <div>
          <label for="work-title" class="block text-sm font-medium text-gray-700 mb-1">
            Work Title
          </label>
          <input 
            type="text" 
            id="work-title" 
            name="work_title" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Republic, Iliad"
          >
        </div>
        
        <div>
          <label for="language" class="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select 
            id="language" 
            name="language" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Any Language</option>
            <option value="grc">Greek</option>
            <option value="eng">English</option>
            <option value="lat">Latin</option>
            <option value="fre">French</option>
            <option value="ger">German</option>
          </select>
        </div>
        
        <div>
          <label for="word-count" class="block text-sm font-medium text-gray-700 mb-1">
            Word Count
          </label>
          <div class="px-2" x-data="{ min: 0, max: 100000 }">
            <div class="flex justify-between text-xs text-gray-600 mb-1">
              <span x-text="min"></span>
              <span x-text="max"></span>
            </div>
            <div class="relative">
              <input 
                type="range" 
                id="word-count-min" 
                name="word_count_min" 
                min="0" 
                max="100000" 
                step="1000"
                class="w-full appearance-none h-2 bg-gray-200 rounded-full"
                x-model="min"
              >
              <input 
                type="range" 
                id="word-count-max" 
                name="word_count_max" 
                min="0" 
                max="100000" 
                step="1000"
                class="w-full appearance-none h-2 bg-gray-200 rounded-full absolute top-0"
                x-model="max"
              >
            </div>
          </div>
        </div>
      </div>
      
      <!-- Advanced Search -->
      <div class="mt-4 pt-4 border-t border-gray-200">
        <label for="content-search" class="block text-sm font-medium text-gray-700 mb-1">
          Full-text Search
        </label>
        <div class="flex">
          <input 
            type="text" 
            id="content-search" 
            name="content_search" 
            class="flex-grow px-3 py-2 border border-gray-300 rounded-l-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Search text content..."
          >
          <button
            type="submit"
            class="px-4 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Search
          </button>
        </div>
      </div>
    </form>
  </div>
</div>
```

### 2.3. Text Reader

A feature-rich text reader for displaying the ancient Greek texts and translations:

#### Features

- **Clean Reading View**: Well-formatted text with proper typography
- **Original/Translation Toggle**: Easy switching between Greek text and translations
- **Parallel Text View**: Display original and translation side-by-side
- **Citation Tools**: Copy or link to specific passages
- **Reading Tools**:
  - Adjustable font size and line spacing
  - Light/dark mode toggle
  - Line/verse numbering toggle
  - Contextual notes (when available)
- **Download Options**: PDF, plain text, XML, and HTML formats

#### Implementation

```html
<!-- templates/reader/text_view.html -->
<div class="text-reader bg-white shadow rounded-lg" 
     x-data="{ 
       view: 'original', 
       fontSize: 16, 
       lineSpacing: 1.5,
       darkMode: false,
       showNumbers: true,
       parallelView: false 
     }">
  <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
    <div class="flex flex-wrap items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900">{{ work.title }}</h2>
        <p class="text-sm text-gray-500">{{ author.name }} 
          ({% if author.century < 0 %}{{ abs(author.century) }} BCE{% else %}{{ author.century }} CE{% endif %})
        </p>
      </div>
      
      <!-- View Controls -->
      <div class="flex items-center space-x-2 mt-2 sm:mt-0">
        <div class="inline-flex rounded-md shadow-sm" role="group">
          <button
            type="button"
            class="px-3 py-2 text-sm font-medium rounded-l-lg"
            :class="view === 'original' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            @click="view = 'original'; parallelView = false"
          >
            Original
          </button>
          <button
            type="button"
            class="px-3 py-2 text-sm font-medium"
            :class="view === 'translation' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            @click="view = 'translation'; parallelView = false"
          >
            Translation
          </button>
          <button
            type="button"
            class="px-3 py-2 text-sm font-medium rounded-r-lg"
            :class="parallelView ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            @click="parallelView = true"
          >
            Parallel
          </button>
        </div>
        
        <!-- Reading Tools Dropdown -->
        <div class="relative" x-data="{ open: false }">
          <button
            @click="open = !open"
            class="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
            </svg>
          </button>
          
          <div
            x-show="open"
            @click.away="open = false"
            class="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg z-10"
            x-transition:enter="transition ease-out duration-100"
            x-transition:enter-start="transform opacity-0 scale-95"
            x-transition:enter-end="transform opacity-100 scale-100"
          >
            <div class="p-4 space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Font Size</label>
                <div class="flex items-center">
                  <button @click="fontSize = Math.max(12, fontSize - 2)" class="p-1 text-gray-500 hover:text-gray-700">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clip-rule="evenodd" />
                    </svg>
                  </button>
                  <div class="flex-grow mx-2 bg-gray-200 h-2 rounded-full">
                    <div class="bg-blue-600 h-2 rounded-full" :style="`width: ${(fontSize-12)/12*100}%`"></div>
                  </div>
                  <button @click="fontSize = Math.min(24, fontSize + 2)" class="p-1 text-gray-500 hover:text-gray-700">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clip-rule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Line Spacing</label>
                <div class="flex items-center">
                  <button @click="lineSpacing = Math.max(1, lineSpacing - 0.1)" class="p-1 text-gray-500 hover:text-gray-700">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clip-rule="evenodd" />
                    </svg>
                  </button>
                  <div class="flex-grow mx-2 bg-gray-200 h-2 rounded-full">
                    <div class="bg-blue-600 h-2 rounded-full" :style="`width: ${(lineSpacing-1)/1*100}%`"></div>
                  </div>
                  <button @click="lineSpacing = Math.min(2, lineSpacing + 0.1)" class="p-1 text-gray-500 hover:text-gray-700">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clip-rule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
              
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-700">Dark Mode</span>
                <button
                  @click="darkMode = !darkMode"
                  :class="darkMode ? 'bg-blue-600' : 'bg-gray-200'"
                  class="relative inline-flex items-center h-6 rounded-full w-11 transition-colors focus:outline-none"
                >
                  <span
                    :class="darkMode ? 'translate-x-6' : 'translate-x-1'"
                    class="inline-block w-4 h-4 transform bg-white rounded-full transition-transform"
                  ></span>
                </button>
              </div>
              
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-700">Line Numbers</span>
                <button
                  @click="showNumbers = !showNumbers"
                  :class="showNumbers ? 'bg-blue-600' : 'bg-gray-200'"
                  class="relative inline-flex items-center h-6 rounded-full w-11 transition-colors focus:outline-none"
                >
                  <span
                    :class="showNumbers ? 'translate-x-6' : 'translate-x-1'"
                    class="inline-block w-4 h-4 transform bg-white rounded-full transition-transform"
                  ></span>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Download Options -->
        <div class="relative" x-data="{ open: false }">
          <button
            @click="open = !open"
            class="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
            Download
          </button>
          
          <div
            x-show="open"
            @click.away="open = false"
            class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10"
            x-transition:enter="transition ease-out duration-100"
            x-transition:enter-start="transform opacity-0 scale-95"
            x-transition:enter-end="transform opacity-100 scale-100"
          >
            <div class="py-1">
              <a href="/download/{{ work.urn }}/pdf" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">PDF Format</a>
              <a href="/download/{{ work.urn }}/plain" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Plain Text</a>
              <a href="/download/{{ work.urn }}/xml" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">XML (TEI)</a>
              <a href="/download/{{ work.urn }}/html" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">HTML</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Text Content -->
  <div 
    class="px-4 py-5 sm:px-6 text-content overflow-auto"
    :class="{ 'bg-gray-900 text-white': darkMode, 'bg-white text-gray-900': !darkMode }"
    style="max-height: 70vh;"
  >
    <!-- Text display varies based on view selection -->
    <template x-if="!parallelView">
      <div>
        <!-- Original Text View -->
        <div x-show="view === 'original'" class="original-text">
          <div class="prose max-w-none" :style="`font-size: ${fontSize}px; line-height: ${lineSpacing};`">
            {% for section in original_text.sections %}
            <div class="text-section mb-6">
              <h3 class="text-lg font-medium mb-2">{{ section.title }}</h3>
              <div class="text-container">
                {% for line in section.lines %}
                <div class="line flex">
                  {% if showNumbers %}
                  <span class="line-number text-gray-400 w-12 flex-shrink-0 text-right pr-4">{{ line.number }}</span>
                  {% endif %}
                  <span class="line-content">{{ line.text }}</span>
                </div>
                {% endfor %}
              </div>
            </div>
            {% endfor %}
          </div>
        </div>
        
        <!-- Translation View -->
        <div x-show="view === 'translation'" class="translation-text">
          <div class="prose max-w-none" :style="`font-size: ${fontSize}px; line-height: ${lineSpacing};`">
            {% for section in translation.sections %}
            <div class="text-section mb-6">
              <h3 class="text-lg font-medium mb-2">{{ section.title }}</h3>
              <div class="text-container">
                {% for line in section.lines %}
                <div class="line flex">
                  {% if showNumbers %}
                  <span class="line-number text-gray-400 w-12 flex-shrink-0 text-right pr-4">{{ line.number }}</span>
                  {% endif %}
                  <span class="line-content">{{ line.text }}</span>
                </div>
                {% endfor %}
              </div>
            </div>
            {% endfor %}
          </div>
        </div>
      </div>
    </template>
    
    <!-- Parallel View -->
    <template x-if="parallelView">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Original Text -->
        <div class="original-text">
          <h3 class="text-lg font-medium mb-2">Original Text ({{ original_text.language }})</h3>
          <div class="prose max-w-none" :style="`font-size: ${fontSize}px; line-height: ${lineSpacing};`">
            {% for section in original_text.sections %}
            <div class="text-section mb-6">
              <h4 class="text-md font-medium mb-2">{{ section.title }}</h4>
              <div class="text-container">
                {% for line in section.lines %}
                <div class="line flex">
                  {% if showNumbers %}
                  <span class="line-number text-gray-400 w-12 flex-shrink-0 text-right pr-4">{{ line.number }}</span>
                  {% endif %}
                  <span class="line-content">{{ line.text }}</span>
                </div>
                {% endfor %}
              </div>
            </div>
            {% endfor %}
          </div>
        </div>
        
        <!-- Translation -->
        <div class="translation-text">
          <h3 class="text-lg font-medium mb-2">Translation ({{ translation.language }})</h3>
          <div class="prose max-w-none" :style="`font-size: ${fontSize}px; line-height: ${lineSpacing};`">
            {% for section in translation.sections %}
            <div class="text-section mb-6">
              <h4 class="text-md font-medium mb-2">{{ section.title }}</h4>
              <div class="text-container">
                {% for line in section.lines %}
                <div class="line flex">
                  {% if showNumbers %}
                  <span class="line-number text-gray-400 w-12 flex-shrink-0 text-right pr-4">{{ line.number }}</span>
                  {% endif %}
                  <span class="line-content">{{ line.text }}</span>
                </div>
                {% endfor %}
              </div>
            </div>
            {% endfor %}
          </div>
        </div>
      </div>
    </template>
  </div>
  
  <!-- Footer with citation information -->
  <div class="px-4 py-3 sm:px-6 bg-gray-50 border-t border-gray-200 text-sm">
    <div class="flex flex-wrap justify-between items-center">
      <div>
        <span class="text-gray-500">Edition: </span>
        <span class="font-medium">{{ original_text.edition }}</span>
        {% if original_text.editor %}
        <span class="text-gray-500 ml-2">Editor: </span>
        <span class="font-medium">{{ original_text.editor }}</span>
        {% endif %}
      </div>
      <div>
        <button 
          class="text-blue-600 hover:text-blue-800 mr-4"
          @click="navigator.clipboard.writeText('{{ work.citation }}'); alert('Citation copied to clipboard');"
        >
          Copy Citation
        </button>
        <button 
          class="text-blue-600 hover:text-blue-800"
          @click="navigator.clipboard.writeText(window.location.href); alert('Link copied to clipboard');"
        >
          Copy Link
        </button>
      </div>
    </div>
  </div>
</div>
```

### 2.4. Text Search Interface

An intuitive search interface for finding texts based on content:

#### Features

- **Simple Search**: Basic text search with language options
- **Advanced Search**: Boolean operators, phrase matching, proximity search
- **Contextual Results**: Display matching text snippets with highlighted search terms
- **Metadata Filtering**: Refine search by author, time period, and genre
- **Result Sorting**: By relevance, chronological order, or alphabetical
- **Search History**: Track recent searches for easy reference
- **Saved Searches**: Allow users to save and name common searches (client-side storage)
- **Copy Paste Search**: Paste Greek text to find similar passages or references

#### Implementation

```html
<!-- templates/search/search_form.html -->
<div class="search-interface bg-white shadow rounded-lg">
  <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
    <h2 class="text-lg font-medium text-gray-900">Search Texts</h2>
    <p class="mt-1 text-sm text-gray-500">
      Search across all texts in the corpus or paste Greek text to find similar passages
    </p>
  </div>
  
  <div class="px-4 py-5 sm:px-6">
    <form hx-post="/search" hx-target="#search-results">
      <!-- Basic Search -->
      <div class="flex flex-col md:flex-row gap-4 mb-4">
        <div class="flex-grow">
          <input 
            type="text" 
            id="search-query" 
            name="query" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter search terms or paste Greek text..."
            required
          >
        </div>
        <div class="flex-shrink-0">
          <select 
            id="search-language" 
            name="language" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Languages</option>
            <option value="grc">Greek Only</option>
            <option value="eng">English Only</option>
            <option value="lat">Latin Only</option>
          </select>
        </div>
        <div class="flex-shrink-0">
          <button 
            type="submit"
            class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Search
          </button>
        </div>
      </div>
      
      <!-- Advanced Search Options -->
      <div x-data="{ showAdvanced: false }">
        <button 
          type="button"
          @click="showAdvanced = !showAdvanced"
          class="text-sm text-blue-600 hover:text-blue-800 mb-4 flex items-center"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            class="h-4 w-4 mr-1" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor" 
            :class="{ 'transform rotate-90': showAdvanced }"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
          Advanced Search Options
        </button>
        
        <div x-show="showAdvanced" class="bg-gray-50 p-4 rounded-md mb-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="search-mode" class="block text-sm font-medium text-gray-700 mb-1">
                Search Mode
              </label>
              <select 
                id="search-mode" 
                name="mode" 
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="terms">Find any terms (OR)</option>
                <option value="all_terms">Find all terms (AND)</option>
                <option value="exact">Exact phrase</option>
                <option value="proximity">Terms near each other</option>
                <option value="similar">Similar text (for pasted passages)</option>
              </select>
            </div>
            
            <div>
              <label for="search-context" class="block text-sm font-medium text-gray-700 mb-1">
                Result Context
              </label>
              <select 
                id="search-context" 
                name="context" 
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="3">3 lines</option>
                <option value="5">5 lines</option>
                <option value="10" selected>10 lines</option>
                <option value="20">20 lines</option>
                <option value="all">Full section</option>
              </select>
            </div>
            
            <div>
              <label for="search-author" class="block text-sm font-medium text-gray-700 mb-1">
                Author
              </label>
              <select 
                id="search-author" 
                name="author_id" 
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Any Author</option>
                {% for author in authors %}
                <option value="{{ author.id }}">{{ author.name }}</option>
                {% endfor %}
              </select>
            </div>
            
            <div>
              <label for="search-sort" class="block text-sm font-medium text-gray-700 mb-1">
                Sort Results
              </label>
              <select 
                id="search-sort" 
                name="sort" 
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="relevance">By Relevance</option>
                <option value="chronological">Chronological (oldest first)</option>
                <option value="chronological_desc">Chronological (newest first)</option>
                <option value="alphabetical">Alphabetical by Author</option>
              </select>
            </div>
            
            <div>
              <label for="search-century-min" class="block text-sm font-medium text-gray-700 mb-1">
                Century Range
              </label>
              <div class="flex items-center space-x-2">
                <select 
                  id="search-century-min" 
                  name="century_min" 
                  class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Any</option>
                  {% for century in centuries %}
                  <option value="{{ century }}">
                    {% if century < 0 %}{{ abs(century) }} BCE{% else %}{{ century }} CE{% endif %}
                  </option>
                  {% endfor %}
                </select>
                <span>to</span>
                <select 
                  id="search-century-max" 
                  name="century_max" 
                  class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Any</option>
                  {% for century in centuries %}
                  <option value="{{ century }}">
                    {% if century < 0 %}{{ abs(century) }} BCE{% else %}{{ century }} CE{% endif %}
                  </option>
                  {% endfor %}
                </select>
              </div>
            </div>
            
            <div>
              <label for="search-type" class="block text-sm font-medium text-gray-700 mb-1">
                Author Type
              </label>
              <select 
                id="search-type" 
                name="author_type" 
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Any Type</option>
                {% for type in author_types %}
                <option value="{{ type }}">{{ type }}</option>
                {% endfor %}
              </select>
            </div>
          </div>
          
          <div class="mt-4 flex justify-end">
            <button 
              type="reset"
              class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 mr-2"
            >
              Reset
            </button>
            <button 
              type="button"
              class="px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              id="save-search-button"
            >
              Save Search
            </button>
          </div>
        </div>
      </div>
    </form>
    
    <!-- Search History -->
    <div class="mt-4 pt-4 border-t border-gray-200" x-data="{ showHistory: false }">
      <button 
        type="button"
        @click="showHistory = !showHistory"
        class="text-sm text-blue-600 hover:text-blue-800 mb-2 flex items-center"
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          class="h-4 w-4 mr-1" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor" 
          :class="{ 'transform rotate-90': showHistory }"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
        Search History & Saved Searches
      </button>
      
      <div x-show="showHistory" class="mt-2">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Recent Searches -->
          <div>
            <h3 class="text-sm font-medium text-gray-700 mb-2">Recent Searches</h3>
            <ul class="space-y-1" id="recent-searches">
              <!-- Dynamically populated with JavaScript -->
              <li class="text-sm text-gray-600">No recent searches</li>
            </ul>
          </div>
          
          <!-- Saved Searches -->
          <div>
            <h3 class="text-sm font-medium text-gray-700 mb-2">Saved Searches</h3>
            <ul class="space-y-1" id="saved-searches">
              <!-- Dynamically populated with JavaScript -->
              <li class="text-sm text-gray-600">No saved searches</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Search Results -->
  <div id="search-results" class="px-4 py-5 sm:px-6 border-t border-gray-200">
    <!-- Results will be loaded here -->
    <div class="text-center text-gray-500 py-8">
      Enter a search query to see results
    </div>
  </div>
</div>

<!-- templates/search/search_results.html -->
<div class="search-results">
  <div class="mb-4">
    <h3 class="text-lg font-medium text-gray-900">
      {{ results.total }} results for "{{ query }}"
    </h3>
    <p class="text-sm text-gray-500">
      Found in {{ results.author_count }} authors and {{ results.work_count }} works
    </p>
  </div>
  
  {% if results.total > 0 %}
  <div class="space-y-6">
    {% for result in results.items %}
    <div class="result-item bg-gray-50 p-4 rounded-md">
      <div class="flex justify-between mb-2">
        <div>
          <h4 class="text-md font-medium text-blue-600">
            <a href="/reader/{{ result.work_urn }}#line-{{ result.line_number }}">
              {{ result.author_name }}: {{ result.work_title }}
            </a>
          </h4>
          <p class="text-sm text-gray-500">
            {{ result.edition_info }} 
            {% if result.century %}
            • 
            {% if result.century < 0 %}{{ abs(result.century) }} BCE{% else %}{{ result.century }} CE{% endif %}
            {% endif %}
          </p>
        </div>
        <div class="text-sm text-gray-500">
          Line {{ result.line_number }}
        </div>
      </div>
      
      <div class="text-snippet mt-2 pl-4 border-l-4 border-blue-200">
        {% for line in result.context %}
        <div class="text-line py-1 {% if line.is_match %}bg-yellow-100 -mx-2 px-2 rounded{% endif %}">
          {{ line.text|safe }}
        </div>
        {% endfor %}
      </div>
      
      <div class="mt-3 flex justify-end">
        <a 
          href="/reader/{{ result.work_urn }}#line-{{ result.line_number }}"
          class="text-sm text-blue-600 hover:text-blue-800"
        >
          View in context
        </a>
      </div>
    </div>
    {% endfor %}
  </div>
  
  <!-- Pagination -->
  <div class="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
    <div class="flex flex-1 justify-between sm:hidden">
      <a href="#" class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
        Previous
      </a>
      <a href="#" class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
        Next
      </a>
    </div>
    <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
      <div>
        <p class="text-sm text-gray-700">
          Showing <span class="font-medium">{{ results.offset + 1 }}</span> to <span class="font-medium">{{ results.offset + results.items|length }}</span> of <span class="font-medium">{{ results.total }}</span> results
        </p>
      </div>
      <div>
        <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
          <a href="{{ pagination.prev_url }}" class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">
            <span class="sr-only">Previous</span>
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
          </a>
          
          {% for page in pagination.pages %}
          <a 
            href="{{ page.url }}" 
            class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium {% if page.current %}text-blue-600 bg-blue-50{% else %}text-gray-700 hover:bg-gray-50{% endif %}"
          >
            {{ page.number }}
          </a>
          {% endfor %}
          
          <a href="{{ pagination.next_url }}" class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">
            <span class="sr-only">Next</span>
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
            </svg>
          </a>
        </nav>
      </div>
    </div>
  </div>
  {% else %}
  <div class="text-center py-8 text-gray-500">
    No results found for your search query.
    <p class="mt-2 text-sm">
      Try different search terms or adjust your filters.
    </p>
  </div>
  {% endif %}
</div>
```

### 2.5. Download Options

Allow users to download texts in various formats:

#### Features

- **Multiple Formats**:
  - PDF (formatted for reading or printing)
  - Plain Text (for simple text processing)
  - XML (TEI original format)
  - HTML (for web use)
  - ePub (for e-readers)
- **Customization Options**:
  - Include/exclude line numbers
  - Include/exclude footnotes/commentary
  - Font and styling preferences
  - Page size and layout options for PDF
- **Batch Download**: Options to download multiple works or an author's complete corpus

#### Implementation

```python
# app/routers/download.py
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from io import BytesIO
import os
from pathlib import Path
from typing import Optional

from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService
from app.utils.download_utils import (
    generate_pdf, 
    generate_plain_text, 
    generate_html, 
    generate_epub
)

router = APIRouter(prefix="/download", tags=["download"])

@router.get("/{urn}/pdf")
async def download_pdf(
    urn: str,
    include_line_numbers: bool = Query(True),
    include_notes: bool = Query(True),
    font_size: int = Query(12),
    page_size: str = Query("a4"),
    catalog_service: CatalogService = Depends(),
    xml_service: XMLProcessorService = Depends(),
):
    """Download a text as PDF."""
    try:
        # Get text information
        text = catalog_service.get_text(urn)
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        
        # Load XML content
        xml_content = xml_service.load_xml(urn)
        if not xml_content:
            raise HTTPException(status_code=404, detail="XML content not found")
        
        # Generate PDF
        pdf_bytes = generate_pdf(
            xml_content, 
            text, 
            include_line_numbers=include_line_numbers,
            include_notes=include_notes,
            font_size=font_size,
            page_size=page_size
        )
        
        # Return PDF file
        filename = f"{text.author_id}_{text.work_id}_{text.version}.pdf"
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@router.get("/{urn}/plain")
async def download_plain_text(
    urn: str,
    include_line_numbers: bool = Query(True),
    catalog_service: CatalogService = Depends(),
    xml_service: XMLProcessorService = Depends(),
):
    """Download a text as plain text."""
    try:
        # Get text information
        text = catalog_service.get_text(urn)
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        
        # Load XML content
        xml_content = xml_service.load_xml(urn)
        if not xml_content:
            raise HTTPException(status_code=404, detail="XML content not found")
        
        # Generate plain text
        text_content = generate_plain_text(
            xml_content, 
            text, 
            include_line_numbers=include_line_numbers
        )
        
        # Return text file
        filename = f"{text.author_id}_{text.work_id}_{text.version}.txt"
        return StreamingResponse(
            BytesIO(text_content.encode('utf-8')),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plain text: {str(e)}")

@router.get("/{urn}/xml")
async def download_xml(
    urn: str,
    catalog_service: CatalogService = Depends(),
    xml_service: XMLProcessorService = Depends(),
):
    """Download the original XML file."""
    try:
        # Get text information
        text = catalog_service.get_text(urn)
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        
        # Get XML file path
        file_path = xml_service.get_file_path(urn)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="XML file not found")
        
        # Return XML file
        filename = f"{text.author_id}_{text.work_id}_{text.version}.xml"
        return FileResponse(
            file_path,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving XML file: {str(e)}")

@router.get("/{urn}/html")
async def download_html(
    urn: str,
    include_line_numbers: bool = Query(True),
    include_notes: bool = Query(True),
    include_css: bool = Query(True),
    catalog_service: CatalogService = Depends(),
    xml_service: XMLProcessorService = Depends(),
):
    """Download a text as HTML."""
    try:
        # Get text information
        text = catalog_service.get_text(urn)
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        
        # Load XML content
        xml_content = xml_service.load_xml(urn)
        if not xml_content:
            raise HTTPException(status_code=404, detail="XML content not found")
        
        # Generate HTML
        html_content = generate_html(
            xml_content, 
            text, 
            include_line_numbers=include_line_numbers,
            include_notes=include_notes,
            include_css=include_css
        )
        
        # Return HTML file
        filename = f"{text.author_id}_{text.work_id}_{text.version}.html"
        return StreamingResponse(
            BytesIO(html_content.encode('utf-8')),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating HTML: {str(e)}")

@router.get("/{urn}/epub")
async def download_epub(
    urn: str,
    include_line_numbers: bool = Query(True),
    include_notes: bool = Query(True),
    catalog_service: CatalogService = Depends(),
    xml_service: XMLProcessorService = Depends(),
):
    """Download a text as ePub."""
    try:
        # Get text information
        text = catalog_service.get_text(urn)
        if not text:
            raise HTTPException(status_code=404, detail="Text not found")
        
        # Load XML content
        xml_content = xml_service.load_xml(urn)
        if not xml_content:
            raise HTTPException(status_code=404, detail="XML content not found")
        
        # Generate ePub
        epub_bytes = generate_epub(
            xml_content, 
            text, 
            include_line_numbers=include_line_numbers,
            include_notes=include_notes
        )
        
        # Return ePub file
        filename = f"{text.author_id}_{text.work_id}_{text.version}.epub"
        return StreamingResponse(
            BytesIO(epub_bytes),
            media_type="application/epub+zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating ePub: {str(e)}")

@router.get("/author/{author_id}")
async def download_author_corpus(
    author_id: str,
    format: str = Query("zip", description="Format: zip, pdf, plain"),
    include_line_numbers: bool = Query(True),
    include_notes: bool = Query(True),
    catalog_service: CatalogService = Depends(),
    xml_service: XMLProcessorService = Depends(),
):
    """Download all works by an author in the selected format."""
    try:
        # Get author and works
        author = catalog_service.get_author(author_id)
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")
            
        works = catalog_service.get_texts_by_author(author_id)
        if not works:
            raise HTTPException(status_code=404, detail="No works found for this author")
        
        # Handle different formats
        if format == "zip":
            # Create a zip file with all texts in XML format
            # Implementation details...
            pass
        elif format == "pdf":
            # Create a single PDF with all works
            # Implementation details...
            pass
        elif format == "plain":
            # Create a plain text file with all works
            # Implementation details...
            pass
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
        # Return file
        # Implementation details...
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating corpus download: {str(e)}")
```

## 3. API Endpoints

### 3.1. Core API Structure

```python
### 3.1. Core API Structure

```python
# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Eulogos",
    description="Web application for accessing, viewing, and managing ancient Greek texts",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
from app.routers import browse, reader, search, download

app.include_router(browse.router)
app.include_router(reader.router)
app.include_router(search.router)
app.include_router(download.router)

# Admin routers (if authenticated)
from app.routers import admin
app.include_router(admin.router)
```

### 3.2. Browse API

```python
# app/routers/browse.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any

from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/browse", tags=["browse"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def browse_authors(
    request: Request,
    sort: str = Query("name", description="Sort authors by: name, century, work_count"),
    author_name: Optional[str] = Query(None, description="Filter by author name"),
    author_type: Optional[str] = Query(None, description="Filter by author type"),
    century_min: Optional[int] = Query(None, description="Minimum century (negative for BCE)"),
    century_max: Optional[int] = Query(None, description="Maximum century (negative for BCE)"),
    catalog_service: CatalogService = Depends()
):
    """Browse authors with filtering and sorting."""
    # Get authors with filtering
    filtered_authors = catalog_service.get_authors(
        name_filter=author_name,
        type_filter=author_type,
        century_min=century_min,
        century_max=century_max
    )
    
    # Sort authors
    if sort == "century":
        filtered_authors.sort(key=lambda x: x.century)
    elif sort == "work_count":
        filtered_authors.sort(key=lambda x: len(catalog_service.get_texts_by_author(x.id)), reverse=True)
    else:  # Default to name
        filtered_authors.sort(key=lambda x: x.name)
    
    # Get available filters for dropdowns
    author_types = catalog_service.get_author_types()
    centuries = catalog_service.get_centuries()
    
    return templates.TemplateResponse(
        "browse/index.html",
        {
            "request": request,
            "authors": filtered_authors,
            "author_types": author_types,
            "centuries": centuries,
            "filters": {
                "sort": sort,
                "author_name": author_name,
                "author_type": author_type,
                "century_min": century_min,
                "century_max": century_max
            }
        }
    )

@router.get("/author/{author_id}", response_class=HTMLResponse)
async def browse_author_works(
    request: Request,
    author_id: str,
    catalog_service: CatalogService = Depends()
):
    """Browse works by a specific author."""
    # Get author
    author = catalog_service.get_author(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Get works by this author
    works = catalog_service.get_texts_by_author(author_id)
    
    return templates.TemplateResponse(
        "browse/author.html",
        {
            "request": request,
            "author": author,
            "works": works
        }
    )

@router.get("/api/authors/autocomplete")
async def author_autocomplete(
    q: str,
    catalog_service: CatalogService = Depends()
):
    """API endpoint for author name autocomplete."""
    matching_authors = catalog_service.search_authors(q, limit=10)
    return [{"id": author.id, "name": author.name} for author in matching_authors]
```

### 3.3. Reader API

```python
# app/routers/reader.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService

router = APIRouter(prefix="/reader", tags=["reader"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/{urn}", response_class=HTMLResponse)
async def read_text(
    request: Request,
    urn: str,
    translation_urn: Optional[str] = Query(None, description="URN of translation to show in parallel"),
    catalog_service: CatalogService = Depends(),
    xml_service: XMLProcessorService = Depends()
):
    """View a text in the reader."""
    # Get text information
    text = catalog_service.get_text(urn)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    
    # Get author information
    author = catalog_service.get_author(text.author_id) if text.author_id else None
    
    # Get work information
    work = catalog_service.get_work(text.author_id, text.work_id) if text.author_id and text.work_id else None
    
    # Load XML content and process for display
    xml_content = xml_service.load_xml(urn)
    if not xml_content:
        raise HTTPException(status_code=404, detail="XML content not found")
    
    # Process XML to sections and lines
    processed_text = xml_service.process_for_display(xml_content)
    
    # Get translation if requested
    translation = None
    if translation_urn:
        translation_text = catalog_service.get_text(translation_urn)
        if translation_text:
            translation_xml = xml_service.load_xml(translation_urn)
            if translation_xml:
                translation = xml_service.process_for_display(translation_xml)
    
    # Get available translations for this work
    translations = []
    if work:
        translations = catalog_service.get_translations_for_work(text.author_id, text.work_id)
    
    return templates.TemplateResponse(
        "reader/text_view.html",
        {
            "request": request,
            "text": text,
            "author": author,
            "work": work,
            "original_text": processed_text,
            "translation": translation,
            "available_translations": translations
        }
    )
```

### 3.4. Search API

```python
# app/routers/search.py
from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any

from app.services.catalog_service import CatalogService
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def search_form(
    request: Request,
    catalog_service: CatalogService = Depends()
):
    """Display the search form."""
    # Get available filters for dropdowns
    authors = catalog_service.get_all_authors()
    author_types = catalog_service.get_author_types()
    centuries = catalog_service.get_centuries()
    
    return templates.TemplateResponse(
        "search/search_form.html",
        {
            "request": request,
            "authors": authors,
            "author_types": author_types,
            "centuries": centuries
        }
    )

@router.post("/", response_class=HTMLResponse)
async def perform_search(
    request: Request,
    query: str = Form(...),
    language: str = Form("all"),
    mode: str = Form("terms"),
    context: int = Form(10),
    author_id: Optional[str] = Form(None),
    sort: str = Form("relevance"),
    century_min: Optional[int] = Form(None),
    century_max: Optional[int] = Form(None),
    author_type: Optional[str] = Form(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search_service: SearchService = Depends(),
    catalog_service: CatalogService = Depends()
):
    """Perform a search and display results."""
    # Calculate offset for pagination
    offset = (page - 1) * limit
    
    # Perform search
    results = search_service.search_texts(
        query=query,
        language=language,
        mode=mode,
        context_lines=context,
        author_id=author_id,
        sort=sort,
        century_min=century_min,
        century_max=century_max,
        author_type=author_type,
        offset=offset,
        limit=limit
    )
    
    # Prepare pagination information
    total_pages = (results["total"] + limit - 1) // limit
    pages = []
    for i in range(max(1, page - 2), min(total_pages + 1, page + 3)):
        # Construct URL for this page
        url = f"/search?query={query}&language={language}&mode={mode}&context={context}"
        if author_id:
            url += f"&author_id={author_id}"
        if sort:
            url += f"&sort={sort}"
        if century_min:
            url += f"&century_min={century_min}"
        if century_max:
            url += f"&century_max={century_max}"
        if author_type:
            url += f"&author_type={author_type}"
        url += f"&page={i}&limit={limit}"
        
        pages.append({
            "number": i,
            "url": url,
            "current": i == page
        })
    
    pagination = {
        "pages": pages,
        "prev_url": pages[0]["url"] if page > 1 and pages else None,
        "next_url": pages[-1]["url"] if page < total_pages and pages else None
    }
    
    return templates.TemplateResponse(
        "search/search_results.html",
        {
            "request": request,
            "query": query,
            "results": {
                **results,
                "offset": offset
            },
            "pagination": pagination
        }
    )
```

## 4. Service Components

The user interface is supported by several core services that handle data access and processing.

### 4.1. XML Processor Service

Handles loading, parsing, and transforming XML files for display:

```python
# app/services/xml_processor_service.py
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.utils.urn import CtsUrn

class XMLProcessorService:
    """Service for processing XML files."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize with data directory path."""
        self.data_dir = Path(data_dir)
    
    def get_file_path(self, urn: str) -> Path:
        """Get file path from URN."""
        try:
            cts_urn = CtsUrn(urn)
            return cts_urn.get_file_path(self.data_dir)
        except Exception as e:
            # Log error
            print(f"Error resolving file path for URN {urn}: {e}")
            return None
    
    def load_xml(self, urn: str) -> Optional[ET.Element]:
        """Load XML content for a text."""
        try:
            file_path = self.get_file_path(urn)
            if not file_path or not os.path.exists(file_path):
                return None
            
            # Parse XML
            tree = ET.parse(file_path)
            return tree.getroot()
        except Exception as e:
            # Log error
            print(f"Error loading XML for URN {urn}: {e}")
            return None
    
    def process_for_display(self, xml_root: ET.Element) -> Dict[str, Any]:
        """Process XML for display in the reader."""
        # Extract language
        lang = xml_root.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        
        # Extract editor information
        editor = self._extract_editor(xml_root)
        
        # Extract edition information
        edition_info = self._extract_edition_info(xml_root)
        
        # Extract text divisions
        sections = self._extract_sections(xml_root)
        
        return {
            "language": self._get_language_display_name(lang),
            "lang_code": lang,
            "editor": editor,
            "edition": edition_info,
            "sections": sections
        }
    
    def _extract_editor(self, xml_root: ET.Element) -> Optional[str]:
        """Extract editor information from XML."""
        # Find editor elements
        editor_elements = xml_root.findall(".//editor") or xml_root.findall(".//{http://www.tei-c.org/ns/1.0}editor")
        if not editor_elements:
            return None
        
        # Extract text from first editor element
        editor_text = "".join(editor_elements[0].itertext()).strip()
        return editor_text if editor_text else None
    
    def _extract_edition_info(self, xml_root: ET.Element) -> str:
        """Extract edition information from XML."""
        # Find title elements
        title_elements = xml_root.findall(".//title") or xml_root.findall(".//{http://www.tei-c.org/ns/1.0}title")
        if not title_elements:
            return "Unknown Edition"
        
        # Extract text from first title element
        title_text = "".join(title_elements[0].itertext()).strip()
        return title_text if title_text else "Unknown Edition"
    
    def _extract_sections(self, xml_root: ET.Element) -> List[Dict[str, Any]]:
        """Extract text sections from XML."""
        sections = []
        
        # Find text divisions
        div_elements = xml_root.findall(".//div") or xml_root.findall(".//{http://www.tei-c.org/ns/1.0}div")
        if not div_elements:
            # If no divisions, treat whole text as one section
            lines = self._extract_lines(xml_root)
            if lines:
                sections.append({
                    "title": "Text",
                    "lines": lines
                })
            return sections
        
        # Process each division
        for div_index, div in enumerate(div_elements):
            # Extract division title
            head_elements = div.findall("./head") or div.findall("./{http://www.tei-c.org/ns/1.0}head")
            title = "".join(head_elements[0].itertext()).strip() if head_elements else f"Section {div_index + 1}"
            
            # Extract lines
            lines = self._extract_lines(div)
            
            sections.append({
                "title": title,
                "lines": lines
            })
        
        return sections
    
    def _extract_lines(self, element: ET.Element) -> List[Dict[str, str]]:
        """Extract lines from XML element."""
        lines = []
        
        # Find line elements
        line_elements = element.findall(".//l") or element.findall(".//{http://www.tei-c.org/ns/1.0}l")
        if line_elements:
            # Process verse lines
            for line_index, line in enumerate(line_elements):
                # Get line number
                n = line.get("n", str(line_index + 1))
                
                # Get line text
                text = "".join(line.itertext()).strip()
                
                lines.append({
                    "number": n,
                    "text": text
                })
        else:
            # Process paragraph text
            p_elements = element.findall(".//p") or element.findall(".//{http://www.tei-c.org/ns/1.0}p")
            for p_index, p in enumerate(p_elements):
                # Get paragraph text
                text = "".join(p.itertext()).strip()
                
                # Split into lines (simplified)
                text_lines = text.split(". ")
                for line_index, line_text in enumerate(text_lines):
                    if line_text:
                        lines.append({
                            "number": f"{p_index + 1}.{line_index + 1}",
                            "text": line_text + ("." if line_index < len(text_lines) - 1 else "")
                        })
        
        return lines
    
    def _get_language_display_name(self, lang_code: str) -> str:
        """Convert language code to display name."""
        language_map = {
            "grc": "Greek",
            "eng": "English",
            "lat": "Latin",
            "fre": "French",
            "ger": "German",
            "ita": "Italian",
            "spa": "Spanish",
            "ara": "Arabic",
            "heb": "Hebrew",
            "cop": "Coptic"
        }
        return language_map.get(lang_code, lang_code)
```

### 4.2. Search Service

Implements text search capabilities:

```python
# app/services/search_service.py
from typing import Dict, List, Optional, Any
import re

from app.services.catalog_service import CatalogService
from app.services.xml_processor_service import XMLProcessorService

class SearchService:
    """Service for searching texts."""
    
    def __init__(
        self, 
        catalog_service: CatalogService,
        xml_service: XMLProcessorService
    ):
        """Initialize with required services."""
        self.catalog_service = catalog_service
        self.xml_service = xml_service
    
    def search_texts(
        self,
        query: str,
        language: str = "all",
        mode: str = "terms",
        context_lines: int = 10,
        author_id: Optional[str] = None,
        sort: str = "relevance",
        century_min: Optional[int] = None,
        century_max: Optional[int] = None,
        author_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search texts based on query and filters."""
        # Get filtered texts
        texts = self._get_filtered_texts(
            language=language,
            author_id=author_id,
            century_min=century_min,
            century_max=century_max,
            author_type=author_type
        )
        
        # Prepare search pattern based on mode
        pattern = self._prepare_search_pattern(query, mode)
        
        # Search in each text
        results = []
        for text in texts:
            # Load XML content
            xml_root = self.xml_service.load_xml(text.urn)
            if not xml_root:
                continue
            
            # Extract text content (simplified)
            content = self._extract_text_content(xml_root)
            
            # Search for pattern in content
            matches = self._find_matches(content, pattern, mode)
            
            # If matches found, add to results
            for match in matches:
                # Get context
                context = self._get_context(content, match, context_lines)
                
                # Get author information
                author = self.catalog_service.get_author(text.author_id) if text.author_id else None
                
                # Add to results
                results.append({
                    "urn": text.urn,
                    "work_urn": f"{text.author_id}.{text.work_id}" if text.author_id and text.work_id else None,
                    "author_id": text.author_id,
                    "author_name": author.name if author else text.group_name,
                    "work_title": text.work_name,
                    "edition_info": text.version,
                    "language": text.language,
                    "line_number": match["line_number"],
                    "context": context,
                    "century": author.century if author else None,
                    "relevance": match["relevance"]
                })
        
        # Sort results
        sorted_results = self._sort_results(results, sort)
        
        # Paginate results
        paginated_results = sorted_results[offset:offset + limit]
        
        # Count unique authors and works
        author_ids = set(result["author_id"] for result in results if result["author_id"])
        work_urns = set(result["work_urn"] for result in results if result["work_urn"])
        
        return {
            "total": len(results),
            "author_count": len(author_ids),
            "work_count": len(work_urns),
            "items": paginated_results
        }
    
    def _get_filtered_texts(
        self,
        language: str = "all",
        author_id: Optional[str] = None,
        century_min: Optional[int] = None,
        century_max: Optional[int] = None,
        author_type: Optional[str] = None
    ) -> List[Any]:
        """Get filtered texts based on criteria."""
        # Get all texts
        all_texts = self.catalog_service.get_all_texts()
        
        # Filter by language
        if language != "all":
            all_texts = [text for text in all_texts if language in text.language]
        
        # Filter by author
        if author_id:
            all_texts = [text for text in all_texts if text.author_id == author_id]
        
        # Filter by century and author type
        if century_min or century_max or author_type:
            filtered_texts = []
            for text in all_texts:
                if not text.author_id:
                    continue
                
                author = self.catalog_service.get_author(text.author_id)
                if not author:
                    continue
                
                # Check century range
                if century_min and author.century < century_min:
                    continue
                if century_max and author.century > century_max:
                    continue
                
                # Check author type
                if author_type and author.type != author_type:
                    continue
                
                filtered_texts.append(text)
            
            all_texts = filtered_texts
        
        return all_texts
    
    def _prepare_search_pattern(self, query: str, mode: str) -> Any:
        """Prepare search pattern based on query and mode."""
        if mode == "exact":
            # Exact phrase matching
            return re.compile(re.escape(query), re.IGNORECASE)
        elif mode == "all_terms":
            # All terms must be present (AND)
            terms = query.split()
            return [re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE) for term in terms]
        elif mode == "similar":
            # Similar text (simplified)
            return query
        else:
            # Default: any term matches (OR)
            terms = query.split()
            return re.compile("|".join(rf"\b{re.escape(term)}\b" for term in terms), re.IGNORECASE)
    
    def _extract_text_content(self, xml_root: Any) -> List[Dict[str, Any]]:
        """Extract text content from XML as lines."""
        # Process XML to get sections and lines
        processed = self.xml_service.process_for_display(xml_root)
        
        # Flatten into lines
        lines = []
        line_number = 1
        for section in processed["sections"]:
            for line in section["lines"]:
                lines.append({
                    "number": line["number"],
                    "line_number": line_number,
                    "text": line["text"],
                    "section": section["title"]
                })
                line_number += 1
        
        return lines
    
    def _find_matches(
        self, 
        content: List[Dict[str, Any]], 
        pattern: Any, 
        mode: str
    ) -> List[Dict[str, Any]]:
        """Find pattern matches in content."""
        matches = []
        
        for line in content:
            text = line["text"]
            line_number = line["line_number"]
            
            # Different matching logic based on mode
            if mode == "all_terms":
                # All terms must be present
                if all(p.search(text) for p in pattern):
                    matches.append({
                        "line_number": line_number,
                        "relevance": 1.0  # Simplified
                    })
            elif mode == "similar":
                # Similar text (simplified)
                similarity = self._calculate_similarity(text, pattern)
                if similarity > 0.5:  # Threshold
                    matches.append({
                        "line_number": line_number,
                        "relevance": similarity
                    })
            else:
                # Default: regex search
                if pattern.search(text):
                    matches.append({
                        "line_number": line_number,
                        "relevance": 1.0  # Simplified
                    })
        
        return matches
    
    def _calculate_similarity(self, text: str, query: str) -> float:
        """Calculate text similarity (simplified)."""
        # Very simplified similarity calculation
        # In a real implementation, use a proper algorithm
        # like cosine similarity or Levenshtein distance
        text_lower = text.lower()
        query_lower = query.lower()
        
        # Count matching words
        text_words = set(re.findall(r'\b\w+\b', text_lower))
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        
        if not query_words:
            return 0.0
        
        matches = text_words.intersection(query_words)
        return len(matches) / len(query_words)
    
    def _get_context(
        self, 
        content: List[Dict[str, Any]], 
        match: Dict[str, Any], 
        context_lines: int
    ) -> List[Dict[str, Any]]:
        """Get context lines around a match."""
        match_line_number = match["line_number"]
        
        # Find the matching line index
        match_index = next((i for i, line in enumerate(content) if line["line_number"] == match_line_number), -1)
        if match_index == -1:
            return []
        
        # Get lines before and after
        start = max(0, match_index - context_lines // 2)
        end = min(len(content), match_index + context_lines // 2 + 1)
        
        # Extract context lines
        context = []
        for i in range(start, end):
            line = content[i]
            context.append({
                "text": line["text"],
                "number": line["number"],
                "is_match": i == match_index
            })
        
        return context
    
    def _sort_results(self, results: List[Dict[str, Any]], sort: str) -> List[Dict[str, Any]]:
        """Sort search results based on sort criteria."""
        if sort == "chronological":
            # Sort by century, oldest first
            return sorted(results, key=lambda x: x.get("century", 0) or 0)
        elif sort == "chronological_desc":
            # Sort by century, newest first
            return sorted(results, key=lambda x: x.get("century", 0) or 0, reverse=True)
        elif sort == "alphabetical":
            # Sort by author name then work title
            return sorted(results, key=lambda x: (x["author_name"], x["work_title"]))
        else:
            # Default: sort by relevance
            return sorted(results, key=lambda x: x["relevance"], reverse=True)
```

## 5. Page Structure and Layout

The overall layout of the user interface follows a consistent pattern:

### 5.1. Main Layout

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Eulogos - Ancient Greek Texts{% endblock %}</title>
    <link href="/static/css/tailwind.css" rel="stylesheet">
    <script defer src="/static/js/alpine.min.js"></script>
    <script src="/static/js/htmx.min.js"></script>
    {% block head %}{% endblock %}
</head>
<body class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Header -->
    <header class="bg-blue-600 text-white shadow">
        <div class="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center">
                <div class="flex items-center">
                    <h1 class="text-2xl font-bold">
                        <a href="/" class="hover:text-blue-100">Eulogos</a>
                    </h1>
                    <span class="ml-2 text-xs text-blue-200">Ancient Greek Texts</span>
                </div>
                
                <nav class="flex space-x-4">
                    <a href="/browse" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700">Browse</a>
                    <a href="/search" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700">Search</a>
                    <a href="/about" class="px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700">About</a>
                </nav>
            </div>
        </div>
    </header>
    
    <!-- Main Content -->
    <main class="flex-grow py-6">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {% block content %}{% endblock %}
        </div>
    </main>
    
    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200">
        <div class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
            <div class="md:flex md:justify-between">
                <div class="mb-4 md:mb-0">
                    <h2 class="text-lg font-medium text-gray-900">Eulogos</h2>
                    <p class="text-sm text-gray-500">
                        A web application for accessing, viewing, and managing ancient Greek texts from the First 1000 Years Project.
                    </p>
                </div>
                
                <div class="grid grid-cols-2 gap-8 sm:grid-cols-3">
                    <div>
                        <h3 class="text-sm font-medium text-gray-800">Navigation</h3>
                        <ul class="mt-2 space-y-2">
                            <li>
                                <a href="/browse" class="text-sm text-gray-500 hover:text-gray-900">Browse Texts</a>
                            </li>
                            <li>
                                <a href="/search" class="text-sm text-gray-500 hover:text-gray-900">Search</a>
                            </li>
                            <li>
                                <a href="/about" class="text-sm text-gray-500 hover:text-gray-900">About</a>
                            </li>
                        </ul>
                    </div>
                    
                    <div>
                        <h3 class="text-sm font-medium text-gray-800">Resources</h3>
                        <ul class="mt-2 space-y-2">
                            <li>
                                <a href="/help" class="text-sm text-gray-500 hover:text-gray-900">Help</a>
                            </li>
                            <li>
                                <a href="/api/docs" class="text-sm text-gray-500 hover:text-gray-900">API Documentation</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="mt-6 border-t border-gray-200 pt-6">
                <p class="text-sm text-gray-500 text-center">
                    &copy; 2025 Eulogos. All rights reserved.
                </p>
            </div>
        </div>
    </footer>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

### 5.2. Home Page

```html
<!-- templates/home.html -->
{% extends "base.html" %}

{% block title %}Eulogos - Ancient Greek Texts{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Hero Section -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
        <div class="px-4 py-5 sm:p-6">
            <h1 class="text-3xl font-bold text-gray-900">Welcome to Eulogos</h1>
            <p class="mt-2 text-lg text-gray-500">
                Explore, read, and search ancient Greek texts from the First 1000 Years Project.
            </p>
            
            <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <a href="/browse" class="px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-center">
                    Browse Texts
                </a>
                <a href="/search" class="px-4 py-3 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-center">
                    Search Texts
                </a>
            </div>
        </div>
    </div>
    
    <!-- Stats Section -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
        <div class="px-4 py-5 sm:p-6">
            <h2 class="text-xl font-bold text-gray-900">Collection Statistics</h2>
            
            <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-gray-50 p-4 rounded-lg">
                    <div class="text-2xl font-bold text-blue-600">{{ stats.authorCount }}</div>
                    <div class="text-sm text-gray-500">Authors</div>
                </div>
                <div class="bg-gray-50 p-4 rounded-lg">
                    <div class="text-2xl font-bold text-blue-600">{{ stats.textCount }}</div>
                    <div class="text-sm text-gray-500">Works</div>
                </div>
                <div class="bg-gray-50 p-4 rounded-lg">
                    <div class="text-2xl font-bold text-blue-600">{{ stats.editions }}</div>
                    <div class="text-sm text-gray-500">Editions</div>
                </div>
                <div class="bg-gray-50 p-4 rounded-lg">
                    <div class="text-2xl font-bold text-blue-600">{{ stats.translations }}</div>
                    <div class="text-sm text-gray-500">Translations</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Featured Authors -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
        <div class="px-4 py-5 sm:p-6">
            <h2 class="text-xl font-bold text-gray-900">Featured Authors</h2>
            
            <div class="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                {% for author in featured_authors %}
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="text-lg font-medium text-blue-600">
                        <a href="/browse/author/{{ author.id }}" class="hover:underline">{{ author.name }}</a>
                    </h3>
                    <p class="text-sm text-gray-500">
                        {% if author.century < 0 %}{{ abs(author.century) }} BCE{% else %}{{ author.century }} CE{% endif %}
                        • {{ author.type }}
                    </p>
                    <p class="mt-2 text-sm text-gray-600">
                        {{ author.works|length }} works available
                    </p>
                </div>
                {% endfor %}
            </div>
            
            <div class="mt-4 text-center">
                <a href="/browse" class="text-blue-600 hover:text-blue-800">
                    View all authors →
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 6. User Search Interface

### 6.1. Search Backend Implementation

For the text search functionality, we'll implement a more detailed service that supports both basic keyword search and advanced search options for finding specific texts or passages:

```python
# app/services/search_implementation.py
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

@dataclass
class SearchMatch:
    """A match in a search."""
    line_number: int
    line_text: str
    match_positions: List[tuple]  # List of (start, end) positions
    relevance: float

class TextSearchEngine:
    """Implementation of text search engine."""
    
    def search_text(
        self,
        text_content: List[Dict[str, Any]],
        query: str,
        mode: str = "terms"
    ) -> List[SearchMatch]:
        """Search text content using the specified query and mode."""
        if mode == "terms":
            return self._search_terms(text_content, query)
        elif mode == "all_terms":
            return self._search_all_terms(text_content, query)
        elif mode == "exact":
            return self._search_exact_phrase(text_content, query)
        elif mode == "proximity":
            return self._search_proximity(text_content, query)
        elif mode == "similar":
            return self._search_similar(text_content, query)
        else:
            # Default to terms search
            return self._search_terms(text_content, query)
    
    def _search_terms(
        self,
        text_content: List[Dict[str, Any]],
        query: str
    ) -> List[SearchMatch]:
        """Search for any of the terms in the query (OR)."""
        # Split query into terms
        terms = query.split()
        if not terms:
            return []
        
        # Create regex pattern for each term
        patterns = [re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE) for term in terms]
        
        matches = []
        for line in text_content:
            line_text = line["text"]
            line_number = line["line_number"]
            
            # Find matches for each pattern
            match_positions = []
            for pattern in patterns:
                for match in pattern.finditer(line_text):
                    match_positions.append(match.span())
            
            # If matches found, add to results
            if match_positions:
                # Calculate relevance based on number of matches
                relevance = len(match_positions) / len(terms)
                
                matches.append(SearchMatch(
                    line_number=line_number,
                    line_text=line_text,
                    match_positions=match_positions,
                    relevance=relevance
                ))
        
        return matches
    
    def _search_all_terms(
        self,
        text_content: List[Dict[str, Any]],
        query: str
    ) -> List[SearchMatch]:
        """Search for all terms in the query (AND)."""
        # Split query into terms
        terms = query.split()
        if not terms:
            return []
        
        # Create regex pattern for each term
        patterns = [re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE) for term in terms]
        
        matches = []
        for line in text_content:
            line_text = line["text"]
            line_number = line["line_number"]
            
            # Check if all patterns match
            all_match = True
            match_positions = []
            
            for pattern in patterns:
                found_matches = list(pattern.finditer(line_text))
                if not found_matches:
                    all_match = False
                    break
                
                for match in found_matches:
                    match_positions.append(match.span())
            
            # If all patterns match, add to results
            if all_match and match_positions:
                matches.append(SearchMatch(
                    line_number=line_number,
                    line_text=line_text,
                    match_positions=match_positions,
                    relevance=1.0  # All terms match, highest relevance
                ))
        
        return matches
    
    def _search_exact_phrase(
        self,
        text_content: List[Dict[str, Any]],
        query: str
    ) -> List[SearchMatch]:
        """Search for exact phrase."""
        if not query:
            return []
        
        # Create regex pattern for exact phrase
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        
        matches = []
        for line in text_content:
            line_text = line["text"]
            line_number = line["line_number"]
            
            # Find all occurrences of the exact phrase
            found_matches = list(pattern.finditer(line_text))
            
            # If matches found, add to results
            if found_matches:
                match_positions = [match.span() for match in found_matches]
                
                matches.append(SearchMatch(
                    line_number=line_number,
                    line_text=line_text,
                    match_positions=match_positions,
                    relevance=1.0
                ))
        
        return matches
    
    def _search_proximity(
        self,
        text_content: List[Dict[str, Any]],
        query: str
    ) -> List[SearchMatch]:
        """Search for terms near each other."""
        # Split query into terms
        terms = query.split()
        if len(terms) < 2:
            # Fall back to exact phrase for single term
            return self._search_exact_phrase(text_content, query)
        
        # Create regex pattern for each term
        patterns = [re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE) for term in terms]
        
        matches = []
        for line in text_content:
            line_text = line["text"]
            line_number = line["line_number"]
            
            # Find positions of all terms
            term_positions = []
            for pattern in patterns:
                positions = []
                for match in pattern.finditer(line_text):
                    positions.append(match.span())
                
                if not positions:
                    term_positions = []
                    break
                
                term_positions.append(positions)
            
            if not term_positions:
                continue
            
            # Check proximity
            # For simplicity, we check if all terms are within a certain number of words
            # This is a very simplified implementation
            word_indices = [pos[0][0] for pos in term_positions]
            max_distance = max(word_indices) - min(word_indices)
            
            # If terms are close enough, add to results
            if max_distance < 50:  # Arbitrary threshold
                # Flatten all match positions
                match_positions = [pos for positions in term_positions for pos in positions]
                
                # Calculate relevance based on proximity
                relevance = 1.0 - (max_distance / 100)  # Closer = higher relevance
                
                matches.append(SearchMatch(
                    line_number=line_number,
                    line_text=line_text,
                    match_positions=match_positions,
                    relevance=max(0.1, relevance)  # Minimum relevance of 0.1
                ))
        
        return matches
    
    def _search_similar(
        self,
        text_content: List[Dict[str, Any]],
        query: str
    ) -> List[SearchMatch]:
        """Search for similar text (for pasted passages)."""
        if not query:
            return []
            
        # Extract query words (removing common words)
        query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
        query_words = {word for word in query_words if word not in self._get_stop_words()}
        
        if not query_words:
            return []
            
        matches = []
        for line in text_content:
            line_text = line["text"]
            line_number = line["line_number"]
            
            # Extract line words
            line_words = set(re.findall(r'\b\w{3,}\b', line_text.lower()))
            line_words = {word for word in line_words if word not in self._get_stop_words()}
            
            if not line_words:
                continue
                
            # Calculate Jaccard similarity
            intersection = query_words.intersection(line_words)
            union = query_words.union(line_words)
            
            if not union:
                continue
                
            similarity = len(intersection) / len(union)
            
            # If similarity is above threshold, add to results
            if similarity > 0.3:  # Arbitrary threshold
                # We can't highlight specific matches for similarity search,
                # so we just use an empty list for match_positions
                matches.append(SearchMatch(
                    line_number=line_number,
                    line_text=line_text,
                    match_positions=[],
                    relevance=similarity
                ))
        
        return matches
    
    def _get_stop_words(self) -> set:
        """Get a set of common words to ignore in similarity search."""
        return {
            "the", "and", "a", "of", "to", "in", "is", "you", "that", "it", "he",
            "was", "for", "on", "are", "as", "with", "his", "they", "at", "be",
            "this", "have", "from", "or", "one", "had", "by", "but", "not", "what",
            "all", "were", "we", "when", "your", "can", "said", "there", "use",
            "an", "each", "which", "she", "do", "how", "their", "if", "will", "up",
            "other", "about", "out", "many", "then", "them", "these", "so", "some",
            "her", "would", "make", "like", "him", "into", "time", "has", "look",
            "two", "more", "go", "see", "no", "way", "could", "my", "than", "been"
        }
```

### 6.2. Copy-Paste Greek Text Search

To enable users to paste Greek text and find similar passages:

```python
# app/routers/search.py (additional endpoint)

@router.post("/paste-search", response_class=HTMLResponse)
async def paste_search(
    request: Request,
    pasted_text: str = Form(...),
    context: int = Form(10),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search_service: SearchService = Depends(),
):
    """Search for passages similar to pasted text."""
    # Process the pasted text
    processed_text = pasted_text.strip()
    
    # Perform search with "similar" mode
    results = search_service.search_texts(
        query=processed_text,
        mode="similar",
        context_lines=context,
        offset=(page - 1) * limit,
        limit=limit
    )
    
    # Prepare pagination
    # (similar to regular search pagination)
    
    return templates.TemplateResponse(
        "search/paste_results.html",
        {
            "request": request,
            "pasted_text": processed_text,
            "results": results,
            "pagination": pagination
        }
    )
```

```html
<!-- templates/search/paste_search.html -->
<div class="paste-search bg-white shadow rounded-lg">
  <div class="px-4 py-5 sm:px-6 border-b border-gray-200">
    <h2 class="text-lg font-medium text-gray-900">Paste Greek Text</h2>
    <p class="mt-1 text-sm text-gray-500">
      Paste a Greek passage to find similar texts in the corpus
    </p>
  </div>
  
  <div class="px-4 py-5 sm:px-6">
    <form hx-post="/search/paste-search" hx-target="#search-results">
      <div class="mb-4">
        <label for="pasted-text" class="block text-sm font-medium text-gray-700 mb-1">
          Greek Text
        </label>
        <textarea
          id="pasted-text"
          name="pasted_text"
          rows="6"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Paste Greek text here..."
          required
        ></textarea>
      </div>
      
      <div class="flex justify-end">
        <select 
          id="context"
          name="context"
          class="mr-2 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="5">5 lines of context</option>
          <option value="10" selected>10 lines of context</option>
          <option value="20">20 lines of context</option>
        </select>
        
        <button
          type="submit"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Find Similar Passages
        </button>
      </div>
    </form>
  </div>
  
  <div id="search-results" class="px-4 py-5 sm:px-6 border-t border-gray-200">
    <!-- Results will be loaded here -->
    <div class="text-center text-gray-500 py-8">
      Paste some Greek text to find similar passages
    </div>
  </div>
</div>
```

## 7. Conclusion

The user interface design for Eulogos prioritizes:

### 7.1. Key Features
- **Intuitive Navigation**: Hierarchical author-works tree for browsing
- **Powerful Search**: Multiple search modes including text similarity
- **Feature-rich Reader**: Reading tools, citation capabilities, download options
- **Responsive Design**: Works on desktop and mobile devices

### 7.2. Implementation Approach
- **Service-Oriented Architecture**: Separation of concerns with dedicated services
- **Modular Components**: Each feature encapsulated in its own component
- **Progressive Enhancement**: Basic functionality without JavaScript, enhanced with HTMX and Alpine.js
- **Accessibility Considerations**: Proper markup and contrast for accessibility

### 7.3. Next Steps
1. **Frontend Refinement**: Polish UI components and transitions
2. **Expanded Search Capabilities**: Implement vector-based semantic search in Phase 3
3. **User Preferences**: Add user preference storage for reading settings
4. **Performance Optimization**: Implement caching and pagination for large texts
5. **Export Formats**: Complete implementation of all download formats

This design provides a comprehensive foundation for the user-facing aspects of the Eulogos application, focusing on the core functionality of browsing, searching, and reading ancient Greek texts.
