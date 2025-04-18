# ID-Based Endpoints in Eulogos

## Overview

Eulogos now uses a direct ID-based path resolution system instead of the previous URN-based approach. This document describes the available endpoints and how to use them.

## Why This Change?

URNs (Uniform Resource Names) were originally used to provide persistent, location-independent identifiers for texts. However, in practice, this introduced several issues:

1. The URN resolution process was complex and error-prone
2. URNs required additional parsing and validation steps
3. Path resolution involved multiple transformation steps
4. The "uniform" nature of URNs didn't align with how texts are actually stored

The new ID-based approach:
- Uses direct, stable IDs for each text
- Relies on the integrated catalog as the single source of truth
- Simplifies path resolution
- Eliminates unnecessary abstraction layers

## ID Format

Text IDs in Eulogos follow this structure:

```
{textgroup}.{work}.{version}
```

For example: `tlg0012.tlg001.perseus-grc1`

This format preserves the hierarchical nature of text identification while being simpler to work with than URNs.

## Available ID-Based Endpoints

### Reading Texts

```
GET /read/id/{text_id}
```

Parameters:
- `text_id`: The stable ID of the text
- `reference` (optional): Reference to navigate to (e.g., "1.1")
- `format_options` (optional): JSON object with formatting options

Example:
```
GET /read/id/tlg0012.tlg001.perseus-grc1
GET /read/id/tlg0012.tlg001.perseus-grc1?reference=1.1
```

### Document Information

```
GET /document/id/{text_id}
```

Parameters:
- `text_id`: The stable ID of the text

Example:
```
GET /document/id/tlg0012.tlg001.perseus-grc1
```

### Passages

```
GET /passage/id/{text_id}
```

Parameters:
- `text_id`: The stable ID of the text
- `reference`: The reference to retrieve
- `format`: Output format (html, text, xml)

Example:
```
GET /passage/id/tlg0012.tlg001.perseus-grc1?reference=1.1&format=html
```

## Finding Text IDs

You can find the ID for a text in the following ways:

1. Browse the catalog at `/browse` - text IDs are displayed alongside each text
2. Examine the `integrated_catalog.json` file

## Note on URN Removal

All URN-based endpoints and functionality have been completely removed from Eulogos. There is no backward compatibility with URN-based access. All code that previously used URNs must now use text IDs directly. 