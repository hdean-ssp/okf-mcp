---
inclusion: fileMatch
fileMatchPattern: "**/api/**,**/controllers/**,**/routes/**,**/openapi*.yaml,**/openapi*.yml"
---

# API Development Standards

Loaded when working on API code. These rules apply on top of the always-on standards.

## REST Conventions

- Resources are nouns, plural: `/customers`, `/orders`, `/invoices`
- HTTP verbs express action: GET, POST, PUT, PATCH, DELETE
- Nested resources reflect ownership: `/customers/{id}/orders`
- Avoid verbs in paths (`/users/{id}/activate` → prefer PATCH with status body)
- Query parameters for filtering, sorting, pagination: `?status=active&sort=-created_at&limit=50`

## Request and Response

- All request/response bodies are JSON
- Field names are camelCase (`customerId`, not `customer_id`)
- Dates in ISO 8601 format: `2026-05-06T14:30:00Z`
- Monetary values: integer cents, not floats (avoid floating-point errors)
- Enums as strings, not integers (`"active"`, not `1`)
- Empty arrays are `[]`, not `null`
- Optional fields omitted, not `null` (where the schema allows)

## Versioning

- API version in the URL path: `/api/v1/customers`
- Breaking changes bump the version
- Deprecated endpoints return a `Deprecation` header with sunset date
- Support at least one previous version for 6 months after deprecation

## Pagination

- Default page size: 50
- Maximum page size: 1000
- Use cursor-based pagination for large datasets
- Use offset/limit for small, bounded datasets
- Include pagination metadata in response: `{ items: [...], pagination: { ... } }`

## Errors

Standard error response shape:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Customer with id abc-123 not found",
    "correlationId": "req_abc123",
    "timestamp": "2026-05-06T14:30:00Z"
  }
}
```

HTTP status codes used correctly:
- `200` OK (GET, PATCH, PUT with content)
- `201` Created (POST that creates)
- `204` No Content (DELETE, PUT with no content)
- `400` Bad Request (validation)
- `401` Unauthorized (no/invalid auth)
- `403` Forbidden (auth valid but not allowed)
- `404` Not Found (resource doesn't exist)
- `409` Conflict (duplicate, version mismatch)
- `422` Unprocessable Entity (semantic validation)
- `429` Too Many Requests (rate limited)
- `500` Internal Server Error (our bug)
- `503` Service Unavailable (dependency down)

## OpenAPI

- Every endpoint documented in `openapi.yaml`
- Schemas reused via `$ref`
- Examples for every request and response
- OpenAPI spec committed to the repo, kept in sync with code (CI enforces)

## Performance

- Response time target: p95 < 200ms for read, < 500ms for write
- Responses streamable for large datasets (CSV exports, reports)
- Response compression enabled (gzip/brotli)
- Caching headers set appropriately (`Cache-Control`, `ETag`)

## Security (API-Specific)

- Authentication required on every endpoint (use middleware, not per-route)
- Rate limiting configured per endpoint class
- CORS configured explicitly; no wildcard origins for authenticated endpoints
- Request bodies size-limited to prevent DoS (default 10MB, less for non-file endpoints)
- Never trust the `Host` header for authorisation decisions
