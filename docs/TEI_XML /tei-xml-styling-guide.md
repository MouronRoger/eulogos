# TEI XML Styling Guide for Ancient Greek Texts

## Introduction

This guide provides comprehensive styling recommendations for rendering TEI XML documents containing ancient Greek texts in the Eulogos system. It focuses on creating a clean, readable presentation while preserving scholarly conventions and structural elements.

## Core Architectural Principles

Before diving into styling, it's important to understand the core architectural principles of the Eulogos system:

1. **text_id is ALWAYS the full data path including filename** - Throughout the system, text identifiers are the complete path to the file in the data directory
2. **integrated_catalog.json is the ONLY source of truth** for all file paths
3. **All path resolution happens through the CatalogService** - No direct path construction is allowed
4. **XMLProcessorService depends on CatalogService** for all document loading

## Core CSS for TEI XML

### Structural Elements

```css
/* Main structural containers */
div[data-reference] {
  margin: 1.5rem 0;
  padding: 0.5rem;
  border-left: 3px solid #e2e8f0;
  background-color: #f8fafc;
}

/* Text division containers */
.tei-div {
  margin-bottom: 1.5rem;
}

/* Text body */
.tei-body {
  line-height: 1.6;
}

/* Front matter */
.tei-front {
  font-style: italic;
  color: #4a5568;
  margin-bottom: 2rem;
}

/* Back matter */
.tei-back {
  margin-top: 2rem;
  font-size: 0.9em;
  color: #4a5568;
}
```

### Reference and Navigation Elements

```css
/* Section numbers and references */
.section-num {
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 0.5rem;
  font-size: 1.1em;
}

.section-num a {
  text-decoration: none;
  color: inherit;
}

.section-num a:hover {
  text-decoration: underline;
}

/* Milestone markers in text */
.milestone {
  display: inline-block;
  position: relative;
  height: 1em;
  width: 1em;
  margin: 0 0.25em;
  vertical-align: middle;
}

.milestone::after {
  content: attr(data-n);
  position: absolute;
  top: -0.8em;
  right: -1em;
  font-size: 0.7em;
  background-color: #e5e7eb;
  color: #4b5563;
  padding: 0.1em 0.3em;
  border-radius: 2px;
}

/* References (cross-references) */
.ref {
  color: #2563eb;
  text-decoration: none;
}

.ref:hover {
  text-decoration: underline;
}
```

### Textual Elements

```css
/* Regular paragraphs */
p.p, .tei-p {
  margin-bottom: 1.25em;
  line-height: 1.7;
}

/* Paragraph alignment variations */
p.align\(center\) {
  text-align: center;
}

p.align\(indent\) {
  text-indent: 2em;
}

p.align\(right\) {
  text-align: right;
}

/* Headings */
h3.head, .tei-head {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 2rem;
  margin-bottom: 1rem;
  color: #1f2937;
}

/* Lines in poetry or verse */
span.line, .tei-l {
  display: block;
  margin-left: 2em;
  text-indent: -2em;
  line-height: 1.6;
}

/* Foreign text (non-Greek within Greek or vice versa) */
.foreign, .tei-foreign {
  font-style: italic;
}
```

### Scholarly Elements

```css
/* Notes */
.note, .tei-note {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0.5rem 0;
  padding-left: 1rem;
  border-left: 2px solid #d1d5db;
}

/* Note references */
.note-ref, .tei-note-ref {
  cursor: pointer;
  color: #d97706;
  font-size: 0.8rem;
  vertical-align: super;
}

/* Quotes */
.quote, .tei-quote {
  margin: 1rem 0;
  padding: 0.5rem 1rem;
  background-color: #f3f4f6;
  border-left: 3px solid #9ca3af;
  font-style: italic;
}

/* Bibliography entries */
.bibl, .tei-bibl {
  font-style: normal;
  color: #4b5563;
  font-size: 0.875rem;
}

/* Person names */
.person, .tei-person {
  color: #047857;
}

/* Place names */
.place, .tei-place {
  color: #7c3aed;
}

/* Date references */
.date, .tei-date {
  color: #b91c1c;
}
```

### Greek-Specific Styling

```css
/* Greek text container */
.greek-text {
  font-family: 'New Athena Unicode', 'GFS Porson', serif;
}

/* Handling unclear text */
.unclear, .tei-unclear {
  color: #6b7280;
  border-bottom: 1px dotted #6b7280;
}

/* Lacunae (gaps in text) */
.gap, .tei-gap {
  display: inline-block;
  width: 3em;
  border-bottom: 2px dashed #6b7280;
  height: 0.5em;
  vertical-align: middle;
}

/* Editorial corrections */
.corr, .tei-corr {
  color: #1d4ed8;
}

/* Original uncorrected text */
.sic, .tei-sic {
  color: #b91c1c;
  text-decoration: line-through;
}

/* Supplied text (editor's addition) */
.supplied, .tei-supplied {
  color: #4b5563;
  font-style: italic;
}
```

### Dark Mode Support

```css
/* Dark mode adjustments */
.dark-mode div[data-reference] {
  background-color: rgba(31, 41, 55, 0.8);
  border-left: 3px solid #4b5563;
}

.dark-mode .section-num {
  color: #9ca3af;
}

.dark-mode h3.head, .dark-mode .tei-head {
  color: #f3f4f6;
}

.dark-mode .note, .dark-mode .tei-note {
  color: #9ca3af;
  border-left-color: #6b7280;
}

.dark-mode .quote, .dark-mode .tei-quote {
  background-color: #374151;
  border-left-color: #9ca3af;
}

.dark-mode .bibl, .dark-mode .tei-bibl {
  color: #9ca3af;
}

.dark-mode .ref, .dark-mode .tei-ref {
  color: #3b82f6;
}

.dark-mode .milestone::after, .dark-mode .tei-milestone::after {
  background-color: #4b5563;
  color: #e5e7eb;
}
```

## Reading Preferences Support

```css
/* Font size presets */
.text-size-small { font-size: 0.875rem; }
.text-size-medium { font-size: 1rem; }
.text-size-large { font-size: 1.125rem; }
.text-size-xl { font-size: 1.25rem; }

/* Line height presets */
.leading-comfortable { line-height: 1.8; }
.leading-relaxed { line-height: 2; }
.leading-spacious { line-height: 2.2; }
```

## Print-Specific Styling

```css
@media print {
  @page {
    margin: 2cm;
    size: A4;
  }
  
  body {
    font-size: 11pt;
    max-width: none;
    padding: 0;
    margin: 0;
    color: black;
  }
  
  div[data-reference] {
    page-break-inside: avoid;
    break-inside: avoid;
    border-left: 0.5pt solid #bbb;
    background-color: transparent;
  }
  
  h3, .tei-head {
    page-break-after: avoid;
    break-after: avoid;
  }
  
  .note, .tei-note {
    border-left: 0.5pt solid #bbb;
    color: #555;
  }
  
  .quote, .tei-quote {
    background-color: transparent;
    border-left: 0.5pt solid #bbb;
  }
  
  .section-num {
    color: #555;
  }
  
  p {
    orphans: 3;
    widows: 3;
  }
  
  a, .ref, .tei-ref {
    color: black;
    text-decoration: none;
  }
  
  .milestone::after, .tei-milestone::after {
    background-color: transparent;
    color: #555;
  }
}
```

## Implementation Notes

### File Path as ID

Throughout the Eulogos system:

1. The `text_id` always refers to the full data path including filename
2. This full path is used for all identification, navigation, and retrieval
3. In templates, always use `text.path` to refer to the text's identifier
4. When displaying text information, make it clear that the ID is the file path

### Embedding in Templates

When implementing these styles in your templates, ensure the following:

1. Include the full CSS in a stylesheet or within a `<style>` tag
2. Reference the file path in display contexts consistently
3. Use proper BEM naming for custom styles to avoid conflicts

Example template usage:

```html
<div class="text-metadata">
  <div class="text-title">{{ text.title }}</div>
  <div class="text-author">{{ text.author }}</div>
  <div class="text-path">File path (ID): {{ text.path }}</div>
</div>
```

### Customization by Text Type

You may want to add custom styling based on text types:

```css
/* Poetry-specific styling */
.poetry .tei-l {
  font-style: italic;
  margin-left: 3em;
}

/* Prose-specific styling */
.prose .tei-p {
  text-indent: 1.5em;
}

/* Drama-specific styling */
.drama .tei-speaker {
  font-weight: bold;
  color: #4b5563;
}
```