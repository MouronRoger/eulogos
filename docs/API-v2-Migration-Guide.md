# Eulogos API v2 Migration Guide

This guide provides instructions for migrating from Eulogos API v1 to v2. The v2 API provides improved functionality, better error handling, and more consistent responses.

## Overview

The Eulogos API v2 is available alongside v1 to allow for a smooth transition. The v1 API will be deprecated on December 31, 2025. We recommend migrating to v2 as soon as possible to take advantage of the new features and improvements.

## Key Differences

| Feature | API v1 | API v2 |
|---------|--------|--------|
| Endpoint Prefix | `/api` | `/api/v2` |
| Response Format | Mixed (HTML/JSON) | Consistent JSON with proper status codes |
| Error Handling | Basic | Comprehensive with detailed error messages |
| Batch Operations | Limited | Full support for batch operations |
| Documentation | Limited | Comprehensive OpenAPI documentation |
| Metadata | Limited | Extensive metadata in responses |

## Feature Toggles

You can control API version behavior using the following environment variables:

- `EULOGOS_API_VERSION` - Default API version (1 or 2)
- `EULOGOS_ENABLE_API_REDIRECTS` - Enable automatic redirects from v1 to v2 API (default: true)
- `EULOGOS_DEPRECATE_V1_API` - Add deprecation headers to v1 API responses (default: false)
- `EULOGOS_V1_SUNSET_DATE` - Sunset date for v1 API (ISO format, default: "2025-12-31")

## Endpoint Mapping

### Browse Endpoints

| v1 Endpoint | v2 Endpoint | Description |
|-------------|-------------|-------------|
| `GET /api/browse` | `GET /api/v2/browse` | Browse texts with filters |
| N/A | `GET /api/v2/statistics` | Get catalog statistics |

### Text Management Endpoints

| v1 Endpoint | v2 Endpoint | Description |
|-------------|-------------|-------------|
| `POST /api/texts/{urn}/archive` | `POST /api/v2/texts/{urn}/archive` | Archive/unarchive a text |
| `POST /api/texts/{urn}/favorite` | `POST /api/v2/texts/{urn}/favorite` | Favorite/unfavorite a text |
| `DELETE /api/texts/{urn}` | `DELETE /api/v2/texts/{urn}` | Delete a text |
| N/A | `POST /api/v2/texts/batch` | Batch operations on texts |

### Reader Endpoints

| v1 Endpoint | v2 Endpoint | Description |
|-------------|-------------|-------------|
| `GET /api/references/{urn}` | `GET /api/v2/references/{urn}` | Get references for a text |
| N/A | `GET /api/v2/document/{urn}` | Get document information |
| N/A | `GET /api/v2/passage/{urn}` | Get a specific passage |

### Export Endpoints

| v1 Endpoint | v2 Endpoint | Description |
|-------------|-------------|-------------|
| `GET /api/export/{urn}` | `GET /api/v2/export/{urn}` | Export text in specified format |
| N/A | `POST /api/v2/export/batch` | Batch export texts |
| N/A | `GET /api/v2/export/status/{id}` | Check export job status |

## Response Format Changes

### Browse Response

#### v1
```json
{
  "authors": [
    {
      "id": "123",
      "name": "Author Name",
      "works": [...]
    }
  ]
}
```

#### v2
```json
{
  "authors": [
    {
      "id": "123",
      "name": "Author Name",
      "century": 4,
      "archived": false,
      "works": [...],
      "metadata": {
        "birth_date": "350",
        "death_date": "404"
      }
    }
  ],
  "count": 1,
  "filters_applied": {
    "show": "all",
    "era": null,
    "search": null
  }
}
```

### Text Operations Response

#### v1
```json
{
  "status": "success"
}
```

#### v2
```json
{
  "status": "success",
  "operation": "archive",
  "text": {
    "urn": "urn:cts:greekLit:tlg0012.tlg001.perseus-grc1",
    "archived": true,
    "updated_at": "2025-05-01T12:34:56Z"
  }
}
```

## Error Handling

### v1
```json
{
  "detail": "Error message"
}
```

### v2
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

## Frontend Update Guide

### HTMX Requests

Update all HTMX requests to use v2 endpoints:

```html
<!-- Before -->
<button hx-get="/api/browse" hx-target="#result">Browse</button>

<!-- After -->
<button hx-get="/api/v2/browse" hx-target="#result">Browse</button>
```

### JavaScript Fetch

```javascript
// Before
fetch('/api/texts/urn:cts:greekLit:tlg0012.tlg001.perseus-grc1/archive')
  .then(response => response.json())
  .then(data => console.log(data));

// After
fetch('/api/v2/texts/urn:cts:greekLit:tlg0012.tlg001.perseus-grc1/archive')
  .then(response => response.json())
  .then(data => console.log(data));
```

## Testing Strategies

1. **Parallel Testing**: Run tests against both v1 and v2 endpoints to ensure consistency
2. **Migration Testing**: Test the automatic redirects from v1 to v2 endpoints
3. **Feature Toggle Testing**: Test with different combinations of feature toggle settings
4. **Response Format Testing**: Verify the response format changes and handle accordingly

## Monitoring and Debugging

1. **Logging**: Add logging for API version usage to track migration progress
2. **Error Tracking**: Monitor for increased error rates during migration
3. **Performance Monitoring**: Compare performance between v1 and v2 endpoints
4. **Usage Analytics**: Track which endpoints are most frequently used to prioritize testing

## Gradual Migration Approach

1. **Update Documentation**: Ensure all documentation references v2 endpoints
2. **Update Frontend**: Update all frontend code to use v2 endpoints directly
3. **Enable Redirects**: Enable automatic redirects from v1 to v2 endpoints
4. **Monitor Usage**: Monitor usage patterns to identify any issues
5. **Enable Deprecation Headers**: Add deprecation headers to v1 responses
6. **Communicate Sunset Date**: Notify users of the v1 sunset date
7. **Disable v1 Endpoints**: Once all clients have migrated, disable v1 endpoints

## API Documentation

For detailed documentation of all v2 endpoints, refer to our [API Documentation](/api/v2/docs).
