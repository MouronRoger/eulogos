# Eulogos API Reference

## Introduction

This document provides comprehensive documentation for the Eulogos API, which allows programmatic access to ancient Greek texts and related functionality. All API endpoints use standard HTTP methods and return JSON responses unless otherwise specified.

## Base URL

```
https://api.eulogos-project.org/api/v1
```

For local development, use:

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API is available without authentication. Future versions may implement authentication for write operations.

## Response Format

All responses are in JSON format and include:

- `status`: Success or failure status
- `data`: The response data (for successful requests)
- `error`: Error details (for failed requests)

Example success response:
```json
{
  "status": "success",
  "data": {
    "content": "<div class=\"text-part\" data-reference=\"1.1\">...</div>",
    "metadata": {
      "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
      "language": "grc",
      "title": "Iliad",
      "author": "Homer"
    }
  }
}
```

If format is "xml":
```json
{
  "status": "success",
  "data": {
    "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><TEI xmlns=\"http://www.tei-c.org/ns/1.0\">...</TEI>",
    "metadata": {
      "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
      "language": "grc",
      "title": "Iliad",
      "author": "Homer"
    }
  }
}
```

#### Get References for a Text

```
GET /reader/{urn}/references
```

Retrieve the reference structure for a text.

**Path Parameters:**
- `urn` (string, required): Text URN (e.g., "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

**Response:**
```json
{
  "status": "success",
  "data": {
    "references": {
      "1": {
        "children": {
          "1": {
            "children": {},
            "ref": "1.1"
          },
          "2": {
            "children": {},
            "ref": "1.2"
          }
        },
        "ref": "1"
      },
      "2": {
        "children": {
          "1": {
            "children": {},
            "ref": "2.1"
          }
        },
        "ref": "2"
      }
    }
  }
}
```

#### Get Adjacent References

```
GET /reader/{urn}/adjacent
```

Get previous and next references relative to a specific reference.

**Path Parameters:**
- `urn` (string, required): Text URN (e.g., "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

**Query Parameters:**
- `reference` (string, required): Current reference (e.g., "1.1")

**Response:**
```json
{
  "status": "success",
  "data": {
    "prev": null,
    "current": "1.1",
    "next": "1.2"
  }
}
```

### Export API

#### Export Text

```
GET /export/{urn}
```

Export a text in the specified format.

**Path Parameters:**
- `urn` (string, required): Text URN (e.g., "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

**Query Parameters:**
- `format` (string, required): Export format (pdf, epub, mobi, markdown, docx, latex, html)
- Various format-specific options (see below)

**Common Options:**
- `include_toc` (boolean, optional): Include table of contents (default: true)
- `include_line_numbers` (boolean, optional): Include line numbers (default: true)

**PDF Options:**
- `font_size` (integer, optional): Font size in points (default: 12)
- `paper_size` (string, optional): Paper size (A4, Letter, etc.) (default: "A4")
- `margins` (integer, optional): Margins in mm (default: 20)

**ePub/MOBI Options:**
- `include_cover` (boolean, optional): Include cover image (default: true)
- `font` (string, optional): Font name (default: "New Athena Unicode")

**Response:**
- Binary file with appropriate Content-Type header

#### Get Export Options

```
GET /export/options
```

Get available export options.

**Response:**
```json
{
  "status": "success",
  "data": {
    "formats": [
      {
        "id": "pdf",
        "name": "PDF",
        "description": "Portable Document Format",
        "options": [
          {
            "name": "font_size",
            "type": "integer",
            "default": 12,
            "description": "Font size in points"
          },
          {
            "name": "paper_size",
            "type": "string",
            "default": "A4",
            "options": ["A4", "Letter", "Legal"],
            "description": "Paper size"
          }
        ]
      },
      {
        "id": "epub",
        "name": "ePub",
        "description": "Electronic Publication format for e-readers",
        "options": [
          {
            "name": "include_cover",
            "type": "boolean",
            "default": true,
            "description": "Include cover image"
          }
        ]
      }
    ]
  }
}
```

### Search API

#### Search Texts

```
GET /search
```

Search for texts matching specific criteria.

**Query Parameters:**
- `query` (string, required): Search query
- `mode` (string, optional): Search mode (terms, all_terms, exact, proximity, similar) (default: "terms")
- `language` (string, optional): Filter by language (e.g., "grc", "eng")
- `author_id` (string, optional): Filter by author ID
- `context` (integer, optional): Number of context lines to include (default: 10)
- `sort` (string, optional): Sort order (relevance, chronological, chronological_desc, alphabetical) (default: "relevance")
- `century_min` (integer, optional): Earliest century to include (negative for BCE)
- `century_max` (integer, optional): Latest century to include (negative for BCE)
- `author_type` (string, optional): Filter by author type
- `offset` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Maximum results to return (default: 20)

**Response:**
```json
{
  "status": "success",
  "data": {
    "total": 25,
    "offset": 0,
    "limit": 20,
    "author_count": 5,
    "work_count": 10,
    "items": [
      {
        "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
        "author_name": "Homer",
        "work_title": "Iliad",
        "language": "grc",
        "edition_info": "Homeri Opera",
        "century": -8,
        "line_number": "1.1",
        "context": [
          {
            "text": "Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος",
            "is_match": true
          },
          {
            "text": "οὐλομένην, ἣ μυρί᾽ Ἀχαιοῖς ἄλγε᾽ ἔθηκε,",
            "is_match": false
          }
        ]
      }
    ]
  }
}
```

#### Paste Search

```
POST /search/paste
```

Search for passages similar to pasted text.

**Request Body:**
```json
{
  "pasted_text": "Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος",
  "context": 10
}
```

**Response:**
Same as search endpoint.

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input parameters |
| 404 | Not Found - Requested resource does not exist |
| 500 | Internal Server Error - Unexpected server error |
| 503 | Service Unavailable - Server temporarily unavailable |

## Rate Limiting

API requests are limited to 100 requests per minute per IP address. If you exceed this limit, you will receive a 429 (Too Many Requests) response.

## Versioning

The API is versioned using URL path versioning (e.g., /api/v1/). When breaking changes are introduced, a new version will be released.

## Further Help

For additional help or to report issues with the API, please contact api@eulogos-project.org or visit the GitHub repository at https://github.com/eulogos-project/eulogos.
{
  "status": "success",
  "data": {
    "id": "tlg0012",
    "name": "Homer"
  }
}
```

Example error response:
```json
{
  "status": "error",
  "error": {
    "code": 404,
    "message": "Text not found"
  }
}
```

## API Endpoints

### Browse API

#### Get All Authors

```
GET /authors
```

Retrieve a list of all authors in the catalog.

**Query Parameters:**
- `archived` (boolean, optional): Include archived authors (default: false)
- `sort` (string, optional): Sort by "name", "century", or "count" (default: "name")
- `filter` (string, optional): Filter by author name
- `era` (string, optional): Filter by era ("pre-socratic", "hellenistic", "imperial", "late-antiquity")

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "tlg0012",
      "name": "Homer",
      "century": -8,
      "type": "Poet",
      "work_count": 2,
      "archived": false
    },
    {
      "id": "tlg0059",
      "name": "Plato",
      "century": -4,
      "type": "Philosopher",
      "work_count": 35,
      "archived": false
    }
  ],
  "metadata": {
    "total": 1024,
    "filtered": 2
  }
}
```

#### Get Author Details

```
GET /authors/{author_id}
```

Retrieve details for a specific author.

**Path Parameters:**
- `author_id` (string, required): Author identifier (e.g., "tlg0012")

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "tlg0012",
    "name": "Homer",
    "century": -8,
    "type": "Poet",
    "archived": false,
    "works": [
      {
        "id": "tlg001",
        "title": "Iliad",
        "language": "grc",
        "urn": "urn:cts:greekLit:tlg0012.tlg001",
        "editions": [
          {
            "id": "perseus-grc2",
            "label": "Iliad, Homeri Opera",
            "language": "grc"
          }
        ],
        "translations": [
          {
            "id": "murray-eng1",
            "label": "Iliad, translated by A.T. Murray",
            "language": "eng"
          }
        ]
      },
      {
        "id": "tlg002",
        "title": "Odyssey",
        "language": "grc",
        "urn": "urn:cts:greekLit:tlg0012.tlg002"
      }
    ]
  }
}
```

#### Archive/Unarchive Author

```
POST /authors/{author_id}/archive
```

Archive or unarchive an author.

**Path Parameters:**
- `author_id` (string, required): Author identifier (e.g., "tlg0012")

**Query Parameters:**
- `archive` (boolean, optional): Whether to archive (true) or unarchive (false) (default: true)

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "tlg0012",
    "archived": true
  }
}
```

#### Get Author Works

```
GET /authors/{author_id}/works
```

Retrieve works for a specific author.

**Path Parameters:**
- `author_id` (string, required): Author identifier (e.g., "tlg0012")

**Query Parameters:**
- `archived` (boolean, optional): Include archived works (default: false)
- `language` (string, optional): Filter by language (e.g., "grc", "eng")

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "tlg001",
      "title": "Iliad",
      "language": "grc",
      "urn": "urn:cts:greekLit:tlg0012.tlg001",
      "archived": false,
      "favorite": false,
      "editions": [
        {
          "id": "perseus-grc2",
          "label": "Iliad, Homeri Opera",
          "language": "grc"
        }
      ]
    },
    {
      "id": "tlg002",
      "title": "Odyssey",
      "language": "grc",
      "urn": "urn:cts:greekLit:tlg0012.tlg002",
      "archived": false,
      "favorite": true
    }
  ]
}
```

### Text API

#### Get Text Details

```
GET /texts/{urn}
```

Retrieve details for a specific text.

**Path Parameters:**
- `urn` (string, required): Text URN (e.g., "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

**Response:**
```json
{
  "status": "success",
  "data": {
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
    "author_id": "tlg0012",
    "author_name": "Homer",
    "title": "Iliad",
    "language": "grc",
    "wordcount": 115661,
    "archived": false,
    "favorite": false,
    "metadata": {
      "editor": "D. B. Monro, Thomas W. Allen",
      "publisher": "Oxford, Clarendon Press",
      "date": "1920"
    }
  }
}
```

#### Archive/Unarchive Text

```
POST /texts/{urn}/archive
```

Archive or unarchive a text.

**Path Parameters:**
- `urn` (string, required): Text URN (e.g., "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

**Query Parameters:**
- `archive` (boolean, optional): Whether to archive (true) or unarchive (false) (default: true)

**Response:**
```json
{
  "status": "success",
  "data": {
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
    "archived": true
  }
}
```

#### Toggle Favorite Status

```
POST /texts/{urn}/favorite
```

Toggle whether a text is favorited.

**Path Parameters:**
- `urn` (string, required): Text URN (e.g., "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

**Response:**
```json
{
  "status": "success",
  "data": {
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
    "favorite": true
  }
}
```

#### Delete Text

```
DELETE /texts/{urn}
```

Delete a text (this action is permanent).

**Path Parameters:**
- `urn` (string, required): Text URN (e.g., "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

**Query Parameters:**
- `confirmation` (boolean, required): Must be true to confirm deletion

**Response:**
```json
{
  "status": "success",
  "data": {
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2",
    "deleted": true
  }
}
```

### Reader API

#### Get Text Content

```
GET /reader/{urn}
```

Retrieve the content of a text.

**Path Parameters:**
- `urn` (string, required): Text URN (e.g., "urn:cts:greekLit:tlg0012.tlg001.perseus-grc2")

**Query Parameters:**
- `reference` (string, optional): Specific reference to retrieve (e.g., "1.1")
- `format` (string, optional): Response format: "html" or "xml" (default: "html")

**Response:**
If format is "html":
```json
