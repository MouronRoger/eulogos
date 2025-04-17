# Eulogos API v2 Documentation

This document provides comprehensive documentation for the Eulogos API v2. The v2 API provides improved functionality, better error handling, and more consistent responses compared to the v1 API.

## Authentication

Currently, the API does not require authentication for most endpoints. However, certain administrative endpoints may require authentication in the future.

## Base URL

All API endpoints are relative to the base URL of your Eulogos installation. For example, if your Eulogos installation is at `https://example.com`, the base URL would be `https://example.com/api/v2`.

## API Endpoints

### Browse Endpoints

#### Get Texts

```http
GET /browse
```

Browse texts with filtering options.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `show` | string | Filter by status: `all`, `favorites`, `archived` (default: `all`) |
| `era` | string | Filter by era: `pre-socratic`, `hellenistic`, `imperial`, `late-antiquity` |
| `search` | string | Search term for filtering texts |
| `author_id` | string | Filter by author ID |
| `language` | string | Filter by language |
| `limit` | integer | Maximum number of results to return |
| `offset` | integer | Number of results to skip |

**Response:**

```json
{
  "authors": [
    {
      "id": "tlg0012",
      "name": "Homer",
      "century": -8,
      "archived": false,
      "works": [
        {
          "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
          "work_name": "Iliad",
          "language": "Greek",
          "archived": false,
          "favorite": true,
          "wordcount": 123456
        }
      ]
    }
  ],
  "count": 1,
  "total": 373,
  "filters_applied": {
    "show": "all",
    "era": null,
    "search": null
  }
}
```

#### Get Catalog Statistics

```http
GET /statistics
```

Get statistics about the catalog.

**Response:**

```json
{
  "authors": {
    "total": 373,
    "archived": 45,
    "by_century": {
      "-8": 3,
      "-7": 5,
      "-6": 12
    }
  },
  "texts": {
    "total": 3779,
    "editions": 1849,
    "translations": 850,
    "archived": 420,
    "favorites": 135,
    "by_language": {
      "Greek": 1875,
      "Latin": 850,
      "English": 965
    }
  },
  "word_count": {
    "total": 12345678,
    "average_per_text": 3267
  }
}
```

### Text Management Endpoints

#### Archive/Unarchive Text

```http
POST /texts/{urn}/archive
```

Archive or unarchive a text.

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `urn` | string | URN of the text |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `archive` | boolean | `true` to archive, `false` to unarchive (default: `true`) |

**Response:**

```json
{
  "status": "success",
  "operation": "archive",
  "archived": true,
  "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
}
```

#### Favorite/Unfavorite Text

```http
POST /texts/{urn}/favorite
```

Toggle favorite status for a text.

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `urn` | string | URN of the text |

**Response:**

```json
{
  "status": "success",
  "operation": "favorite",
  "favorite": true,
  "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
}
```

#### Delete Text

```http
DELETE /texts/{urn}
```

Delete a text.

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `urn` | string | URN of the text |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `confirmation` | boolean | Confirmation for deletion (required: `true`) |

**Response:**

```json
{
  "status": "success",
  "operation": "delete",
  "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
}
```

#### Batch Operations

```http
POST /texts/batch
```

Perform batch operations on multiple texts.

**Request Body:**

```json
{
  "urns": [
    "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
    "urn:cts:greekLit:tlg0012.tlg002.perseus-grc1"
  ],
  "operation": "archive",
  "confirmation": true
}
```

**Response:**

```json
{
  "status": "success",
  "operation": "archive",
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "results": {
    "successful": [
      "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
      "urn:cts:greekLit:tlg0012.tlg002.perseus-grc1"
    ],
    "failed": []
  }
}
```

### Reader Endpoints

#### Get References

```http
GET /references/{urn}
```

Get references for a text.

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `urn` | string | URN of the text |

**Response:**

```json
{
  "references": [
    {
      "reference": "1",
      "label": "Book 1",
      "children": [
        {
          "reference": "1.1",
          "label": "Book 1, Line 1",
          "children": []
        }
      ]
    }
  ],
  "count": 24,
  "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1"
}
```

#### Get Document Information

```http
GET /document/{urn}
```

Get document information for a text.

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `urn` | string | URN of the text |

**Response:**

```json
{
  "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
  "text": {
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
    "work_name": "Iliad",
    "group_name": "Homer",
    "language": "Greek",
    "archived": false,
    "favorite": true,
    "wordcount": 123456
  },
  "metadata": {
    "title": "Iliad",
    "author": "Homer",
    "language": "Greek",
    "date": "8th century BCE",
    "editor": "Gregory Nagy",
    "publisher": "Perseus Digital Library",
    "source": "Homer. The Iliad. Cambridge, MA., Harvard University Press; London, William Heinemann, Ltd. 1924."
  },
  "reference_count": 24,
  "statistics": {
    "word_count": 123456,
    "character_count": 654321,
    "line_count": 12345
  }
}
```

#### Get Passage

```http
GET /passage/{urn}
```

Get a specific passage from a document.

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `urn` | string | URN of the text |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `reference` | string | Reference to retrieve |
| `format` | string | Output format: `html`, `text`, `xml` (default: `html`) |

**Response:**

For `format=html`:
```html
<div class="passage">
  <p>Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος</p>
</div>
```

For `format=text`:
```json
{
  "text": "Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος",
  "reference": "1.1"
}
```

For `format=xml`:
```json
{
  "xml": "<l n=\"1\">Μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος</l>",
  "reference": "1.1"
}
```

### Export Endpoints

#### Export Text

```http
GET /export/{urn}
```

Export text in specified format.

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `urn` | string | URN of the text |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Export format: `html`, `markdown`, `latex`, `pdf`, `epub`, `mobi`, `docx` |
| `reference` | string | Reference to export (optional) |
| `filename` | string | Custom filename (optional) |
| `include_metadata` | boolean | Include metadata in export (default: `true`) |

**Response:**

File download in the requested format.

#### Batch Export

```http
POST /export/batch
```

Batch export texts.

**Request Body:**

```json
{
  "urns": [
    "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
    "urn:cts:greekLit:tlg0012.tlg002.perseus-grc1"
  ],
  "format": "pdf",
  "options": {
    "include_metadata": true,
    "compress": true
  }
}
```

**Response:**

```json
{
  "status": "pending",
  "job_id": "12345",
  "message": "Export job started",
  "estimated_completion_time": "2025-05-01T12:34:56Z"
}
```

#### Check Export Status

```http
GET /export/status/{id}
```

Check the status of a batch export job.

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Job ID from the batch export response |

**Response:**

```json
{
  "status": "completed",
  "job_id": "12345",
  "progress": 100,
  "download_url": "/api/v2/export/download/12345",
  "expiration_time": "2025-05-02T12:34:56Z"
}
```

## Error Handling

All API endpoints use proper error handling and return appropriate HTTP status codes:

- 200: Success
- 400: Bad Request (e.g., invalid URN format)
- 404: Not Found (text not found)
- 500: Internal Server Error

Error responses include details about the error:

```json
{
  "status": "error",
  "code": "text_not_found",
  "message": "Text not found with URN: urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
  "details": {
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
    "resolution_path": "data/tlg0012/tlg001/tlg0012.tlg001.perseus-grc1.xml"
  }
}
```

## Pagination

Endpoints that return lists of items support pagination through `limit` and `offset` parameters:

```http
GET /browse?limit=10&offset=20
```

Response includes pagination metadata:

```json
{
  "authors": [...],
  "count": 10,
  "total": 373,
  "offset": 20,
  "limit": 10,
  "next": "/api/v2/browse?limit=10&offset=30",
  "previous": "/api/v2/browse?limit=10&offset=10"
}
```

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) for all endpoints, allowing browser-based applications to make requests to the API from different domains.

## Rate Limiting

The API implements rate limiting to prevent abuse. Rate limits are applied on a per-IP basis:

- 100 requests per minute for most endpoints
- 10 requests per minute for export endpoints

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1620000000
```

## API Versioning

The API uses URL-based versioning with the prefix `/api/v2`. Future versions will use `/api/v3`, etc.

## API Reference Sources

This documentation is based on the following source files:

- `app/routers/v2/browse.py`: Browse endpoints
- `app/routers/v2/texts.py`: Text management endpoints
- `app/routers/v2/reader.py`: Reader endpoints
- `app/routers/v2/export.py`: Export endpoints
