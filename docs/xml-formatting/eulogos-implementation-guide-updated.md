# Updated Eulogos TEI XML Reader Implementation Guide

This guide provides detailed instructions for implementing the enhanced TEI XML processing capabilities in the Eulogos project. The implementation will fix both the styling issue and the routing issue that's causing raw XML to be displayed instead of properly transformed content.

## Background

[TEI (Text Encoding Initiative)](https://tei-c.org/) is the standard for encoding scholarly texts, especially ancient texts with critical apparatus and textual variants. The Eulogos application should be rendering these TEI XML documents with sophisticated styling that properly represents scholarly editions of ancient Greek texts.

## Current Issues

There are two main issues:

1. **XML Transformation Issue**: The `XMLProcessorService._process_element_to_html()` method is not properly transforming TEI elements into HTML with the right structure to match CSS selectors.

2. **Routing Issue**: The `/data/{path:path}` route is always returning raw XML content instead of checking for a `raw` parameter and conditionally transforming content.

## Implementation Steps

### 1. Update XMLProcessorService

Replace the current implementation in `app/services/xml_processor.py` with the enhanced version provided in the `eulogos-xml-processor-fix.py` artifact. This implementation:

- Properly handles TEI-specific elements (`div`, `p`, `note`, `lb`, `pb`, etc.)
- Correctly processes references and adds navigation attributes
- Tokenizes Greek text at the word level
- Generates HTML that matches the CSS selectors

### 2. Fix Route Handler

Update the route handler for `/data/{path:path}` to properly check for the `raw` parameter and conditionally serve raw XML or transformed HTML:

1. Locate the route definition in your codebase (likely in `app/main.py`)
2. Replace it with the implementation from the `eulogos-route-handler-fix.py` artifact
3. This will ensure that requests without `?raw=true` will properly transform XML to HTML

### 3. Add or Update CSS Styles

Add the CSS styles from the `eulogos-tei-css.css` artifact to your reader template. You can either:

- Replace the existing TEI XML styles in `app/templates/reader.html` with these styles
- Add these styles to a separate CSS file and include it in your template

### 4. Update Reader Template

Update your `reader.html` template with the improved version from `eulogos-reader-html-template.html` which includes:

- Reference navigation controls
- Word-level token interaction
- Reading preferences (dark mode, font size, etc.)
- Export options

### 5. Test the Implementation

Test the implementation with a sample TEI XML file that includes various elements like:

- Text divisions with chapter numbering
- Line breaks with line numbers
- Page breaks
- Footnotes and marginal notes
- Greek text with critical apparatus

## URL Patterns

After implementation, your application should properly handle the following URL patterns:

| URL Pattern | What Should Display |
|-------------|---------------------|
| `/data/xxx.xml?raw=true` | Raw XML in a `<pre>` block for debugging |
| `/data/xxx.xml` | Transformed HTML with proper TEI styling |

## Technical Details

### Route Handler Logic

The updated route handler:

1. Checks for the `raw` parameter in the query string
2. If present, returns the raw XML content with `FileResponse`
3. If not present, loads the XML, transforms it, and returns the rendered template
4. Handles reference-based navigation if a reference is provided
5. Includes proper error handling and logging

### TEI XML Elements Handled

The enhanced implementation handles these TEI XML elements:

| Element | Description | HTML Output |
|---------|-------------|-------------|
| `div` | Text division | `<div class="div {subtype}" data-reference="{ref}" id="ref-{ref}">` |
| `p` | Paragraph | `<p class="p {rend}">` |
| `lb` | Line break | `<br class="lb" data-n="{n}">` |
| `pb` | Page break | `<div class="pb" data-n="{n}">Page {n}</div>` |
| `note` | Critical notes | `<div class="note {type}">` |
| `head` | Section heading | `<h3 class="head {rend}">` |
| `l` | Line of verse | `<span class="line {rend}">` |
| `quote` | Quotation | `<blockquote class="quote {rend}">` |
| `foreign` | Foreign language text | `<em class="foreign" data-lang="{lang}">` |
| `bibl` | Bibliographic citation | `<cite class="bibl">` |
| `ref` | Cross-reference | `<a href="{target}" class="ref">` |
| `milestone` | Section marker | `<span class="milestone {unit}" data-n="{n}">` |

## Troubleshooting

If you continue to see raw XML instead of transformed content after implementation:

1. Check server logs for errors in XML transformation
2. Verify that the correct route handler is being used
3. Check that the XMLProcessorService is correctly instantiated
4. Test with a simple XML file to isolate any issues with specific TEI elements
5. Verify that the template is receiving the transformed content

## Common Issues and Solutions

### Issue: Route is returning raw XML even without the raw parameter

**Solution**: Ensure that your route handler is properly checking the raw parameter and using the XML processor for transformation.

### Issue: XML transformation fails with an error

**Solution**: Check that the XML is well-formed and that the XMLProcessorService can handle all the TEI elements present.

### Issue: Template renders but styling is not applied

**Solution**: Verify that the CSS styles are correctly included in the template and that the HTML structure matches the CSS selectors.

### Issue: Greek text appears as squares or question marks

**Solution**: Ensure that proper Greek fonts are installed and configured in the CSS.

## Conclusion

With these changes, your Eulogos application should properly display TEI XML texts with scholarly formatting, including proper handling of Greek text, critical apparatus, and reference navigation.

This implementation follows TEI best practices and provides a rich reading experience for ancient Greek texts while maintaining the scholarly information needed for academic use.