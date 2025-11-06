# Deal Brain REST API

The Deal Brain API is a comprehensive FastAPI-based REST service for managing PC component inventory, listings, valuations, and pricing analysis. It provides endpoints for importing data, managing component catalogs, evaluating pricing based on configurable valuation rules, and generating ranked recommendations.

## Quick Start

### Base URL

**Development (Local):**
```
http://localhost:8000
```

**Docker:**
```
http://localhost:8020
```

**Production:**
Configure via `NEXT_PUBLIC_API_URL` environment variable (defaults to localhost:8000 in dev).

### Interactive Documentation

- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc`
- **OpenAPI Schema**: Available at `/openapi.json`

All endpoints are fully documented with request/response schemas, examples, and parameter descriptions in the interactive docs.

## Authentication

Currently, the API operates with **CORS enabled for all origins** and is primarily unauthenticated for general endpoints.

**Admin-only endpoints** (marked with `_user=Depends(require_admin)`) require admin authentication, but the auth module is optional and can be disabled:

```python
# If auth is not configured, these endpoints are accessible
try:
    from dealbrain_api.auth import require_admin
except Exception:
    async def require_admin() -> None:
        return None
```

**Future Authentication:**
The system is designed to integrate with Clerk JWT authentication. When enabled, protected endpoints will require:
```
Authorization: Bearer <jwt_token>
```

## Common Response Patterns

### Success Response

All successful responses return HTTP 200 (or appropriate 2xx status) with Pydantic-validated JSON:

```json
{
  "id": 123,
  "title": "Dell OptiPlex 7090",
  "price_usd": 450.50,
  "adjusted_price_usd": 425.00,
  "score_composite": 8.5
}
```

### Error Response

All errors follow a consistent pattern:

```json
{
  "detail": "CPU with id 999 not found"
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request (validation error, invalid input)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

## Pagination & Filtering

### Query Parameters

Most list endpoints support standard query parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `limit` | integer | Max results (default: 10, max: 100) | `?limit=50` |
| `offset` | integer | Results to skip | `?offset=20` |
| `metric` | string | Sort by metric (rankings) | `?metric=score_composite` |
| `budget` | float | Filter by max price (dashboard) | `?budget=500.0` |
| `entity` | string | Filter by entity type | `?entity=listing` |

### Filtering Example

```bash
# Get top 20 listings by performance per watt
GET /api/v1/rankings?metric=perf_per_watt&limit=20

# Get dashboard view with custom budget
GET /api/v1/dashboard?budget=600.0
```

## Rate Limiting

Currently, the API has **no rate limiting configured**. Per-user rate limiting can be enabled at the application layer if needed.

**Telemetry:**
- Metrics are collected via Prometheus
- Tracing can be enabled with OpenTelemetry
- Access logs follow the configured telemetry settings (console or JSON)

## API Modules

### Health Checks (`/api/v1/health`)

System health and subsystem monitoring endpoints.

**Endpoints:**
- `GET /` - Overall system health (database, baseline, API)
- `GET /baseline` - Baseline valuation system health check

**Response Example:**
```json
{
  "status": "healthy",
  "subsystems": {
    "baseline": "healthy",
    "database": "healthy",
    "api": "healthy"
  },
  "timestamp": "2024-11-05T10:30:00.000Z"
}
```

### Listings (`/v1/listings`)

Core listing management endpoints for PC inventory.

**Endpoints:**
- `GET` - List all listings with filtering
- `POST` - Create a new listing
- `GET /{listing_id}` - Get listing details
- `PUT /{listing_id}` - Update listing
- `PATCH /{listing_id}` - Partial update
- `DELETE /{listing_id}` - Delete listing
- `POST /bulk-update` - Batch update multiple listings
- `POST /apply-metrics` - Apply valuation metrics to listing
- `POST /bulk-recalculate` - Recalculate metrics for multiple listings
- `GET /{listing_id}/valuation-breakdown` - Get detailed valuation explanation
- `GET /{listing_id}/ports` - Get connected ports
- `PUT /{listing_id}/ports` - Update port configuration
- `GET /{listing_id}/fields` - Get schema for listing fields
- `POST /{listing_id}/overrides` - Apply valuation overrides

**Core Fields:**
- `title` (string, required) - Listing name
- `price_usd` (number, required) - Price in USD
- `adjusted_price_usd` (number, computed) - Price after valuation adjustments
- `condition` (enum) - "excellent", "good", "fair", "poor"
- `status` (enum) - "active", "sold", "pending"
- `cpu_id` (reference) - Linked CPU component
- `gpu_id` (reference) - Linked GPU component
- `ram_generation` (enum) - "DDR3", "DDR4", "DDR5"
- `storage_medium` (enum) - "SSD", "HDD", "NVMe"

**Valuation Fields (Computed):**
- `score_composite` - Overall composite score (0-10)
- `score_cpu_multi` - Multi-threaded CPU score
- `score_cpu_single` - Single-threaded CPU score
- `score_gpu` - GPU score
- `dollar_per_cpu_mark` - Price efficiency (lower is better)
- `dollar_per_single_mark` - Single-thread price efficiency
- `perf_per_watt` - Performance per watt consumed
- `valuation_breakdown` - JSON explaining all applied adjustments

**Example Request (Create):**
```typescript
POST /v1/listings
{
  "title": "Dell OptiPlex 7090",
  "price_usd": 450.00,
  "condition": "good",
  "cpu_id": 1,
  "ram_generation": "DDR4"
}
```

**Example Request (Get Valuation Breakdown):**
```typescript
GET /v1/listings/123/valuation-breakdown

Response:
{
  "listing_id": 123,
  "base_price": 450.00,
  "adjustments": [
    {
      "rule_id": 45,
      "rule_name": "CPU Mark Deduction",
      "action": "deduct",
      "amount": 25.00,
      "reason": "Below benchmark threshold"
    }
  ],
  "adjusted_price": 425.00,
  "timestamp": "2024-11-05T10:30:00.000Z"
}
```

### Catalog (`/v1/catalog`)

Component master data (CPUs, GPUs, RAM, Storage, Ports).

**Endpoints:**
- `GET /cpus` - List all CPUs
- `GET /cpus/{id}` - Get CPU details
- `POST /cpus` - Create CPU
- `PATCH /cpus/{id}` - Update CPU
- `GET /gpus` - List all GPUs
- `GET /gpus/{id}` - Get GPU details
- `POST /gpus` - Create GPU
- `GET /ram-specs` - List RAM specifications
- `GET /storage-profiles` - List storage profiles
- `GET /ports-profiles` - List port configurations
- `POST /ports-profiles` - Create port profile

**CPU Fields:**
```typescript
{
  "id": 1,
  "name": "Intel Core i7-13700K",
  "manufacturer": "Intel",
  "series": "Core i7",
  "model_number": "13700K",
  "cores": 16,
  "threads": 24,
  "base_clock_ghz": 3.4,
  "boost_clock_ghz": 5.4,
  "cpu_mark_score": 45000,
  "single_thread_score": 2800,
  "igpu_mark_score": null,
  "tdp_watts": 125
}
```

### Rankings (`/v1/rankings`)

Pre-calculated rankings by various metrics.

**Endpoints:**
- `GET` - Get top listings by metric

**Parameters:**
- `metric` (string) - One of: `score_composite`, `score_cpu_multi`, `score_cpu_single`, `score_gpu`, `dollar_per_cpu_mark`, `dollar_per_single_mark`, `adjusted_price_usd`, `perf_per_watt`
- `limit` (integer, default: 10, max: 100) - Number of results

**Example:**
```bash
# Top 20 listings by composite score
GET /v1/rankings?metric=score_composite&limit=20

# Most efficient CPUs by dollar per mark
GET /v1/rankings?metric=dollar_per_cpu_mark&limit=10
```

### Dashboard (`/v1/dashboard`)

Summary endpoint with curated top listings.

**Endpoints:**
- `GET` - Get dashboard summary

**Parameters:**
- `budget` (float, default: 400.0) - Budget threshold for "under budget" results

**Response:**
```json
{
  "best_value": {
    "id": 45,
    "title": "HP EliteDesk 800",
    "dollar_per_cpu_mark": 0.012
  },
  "best_perf_per_watt": {
    "id": 67,
    "title": "Lenovo ThinkCentre",
    "perf_per_watt": 0.85
  },
  "best_under_budget": [
    {"id": 12, "title": "Dell OptiPlex", "adjusted_price_usd": 350.00},
    {"id": 23, "title": "HP ProDesk", "adjusted_price_usd": 375.00}
  ]
}
```

### Imports (`/v1/imports`)

Excel workbook import workflow with preview and conflict detection.

**Endpoints:**
- `POST /sessions` - Create import session from Excel file
- `GET /sessions` - List import sessions
- `GET /sessions/{id}` - Get session details
- `PUT /sessions/{id}/mappings` - Update field mappings
- `POST /sessions/{id}/commit` - Commit import to database
- `POST /sessions/{id}/fields` - Create custom field during import
- `DELETE /sessions/{id}` - Cancel/delete import session

**Workflow:**
1. Upload Excel file → Create import session
2. Review sheet metadata, preview data, detect conflicts
3. Update field mappings if needed
4. Create custom fields if needed
5. Commit to apply import

**Example (Create Session):**
```bash
POST /v1/imports/sessions
Content-Type: multipart/form-data

file: (binary Excel file)
declared_entities: {"cpu_column": "Processor"}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "listings.xlsx",
  "status": "preview",
  "sheet_meta": [
    {"name": "Listings", "row_count": 150},
    {"name": "CPUs", "row_count": 30}
  ],
  "mappings": {},
  "preview": {
    "Listings": [
      {"title": "Dell OptiPlex", "price_usd": 450.00}
    ]
  },
  "conflicts": {},
  "created_at": "2024-11-05T10:30:00.000Z"
}
```

### Ingestion (`/api/v1/ingest`)

URL-based ingestion for marketplace listings (eBay, Amazon, etc.).

**Endpoints:**
- `POST /url` - Ingest single URL
- `POST /bulk` - Bulk ingestion from CSV/JSON file
- `GET /bulk/{batch_id}` - Get bulk ingestion status
- `POST /bulk/{batch_id}/status` - Detailed status for batch

**URL Adapters:**
- **eBay** - Extracts title, price, condition, item specifications
- **JSON-LD** - Generic JSON-LD structured data extraction
- **Amazon** - Placeholder for future P1 implementation

**Example (Single URL):**
```bash
POST /api/v1/ingest/url
{
  "url": "https://www.ebay.com/itm/123456789",
  "source_type": "ebay"
}

Response:
{
  "listing_id": 789,
  "source_url": "https://www.ebay.com/itm/123456789",
  "title": "Dell OptiPlex 7090",
  "price_usd": 450.00,
  "extracted_fields": {
    "condition": "good",
    "cpu": "Intel Core i7"
  },
  "status": "pending_review"
}
```

**Example (Bulk from CSV):**
```bash
POST /api/v1/ingest/bulk
Content-Type: multipart/form-data

file: (CSV or JSON with URLs)

CSV Format:
url
https://www.ebay.com/itm/123456789
https://www.ebay.com/itm/987654321
```

### Custom Fields (`/v1/reference/custom-fields`)

Dynamic field management for extended listing metadata.

**Endpoints:**
- `GET` - List custom fields (filter by entity)
- `POST` - Create custom field
- `PATCH /{id}` - Update field definition
- `DELETE /{id}` - Delete field
- `POST /{id}/options` - Add option to enum field
- `DELETE /{id}/options/{option_id}` - Remove option

**Field Types Supported:**
- `string` - Text input (searchable)
- `number` - Numeric input (for metrics)
- `enum` - Dropdown options (manage via `/options` endpoints)
- `list` - Array of values (URLs, tags)
- `boolean` - Checkbox (true/false)
- `date` - Date picker (ISO 8601)
- `reference` - Foreign key to another entity

**Example (Create Field):**
```bash
POST /v1/reference/custom-fields
{
  "entity": "listing",
  "key": "warranty_months",
  "label": "Warranty (Months)",
  "data_type": "number",
  "description": "Warranty period in months",
  "required": false,
  "default_value": 0,
  "validation": {"min": 0, "max": 60},
  "display_order": 10
}
```

### Rules (`/api/v1/rulesets`, `/api/v1/rule-groups`, `/api/v1/rules`)

Valuation rule management system with condition/action framework.

**Endpoint Groups:**

**Rulesets** (`/rulesets`)
- `POST` - Create ruleset
- `GET` - List rulesets
- `GET /{id}` - Get ruleset details
- `PATCH /{id}` - Update ruleset
- `POST /{id}/activate` - Activate ruleset
- `POST /apply/{id}` - Apply ruleset to listings

**Rule Groups** (`/rule-groups`)
- `POST` - Create group within ruleset
- `GET` - List groups
- `PATCH /{id}` - Update group
- `DELETE /{id}` - Delete group

**Rules** (`/rules`)
- `POST` - Create rule
- `GET` - List rules
- `PATCH /{id}` - Update rule
- `DELETE /{id}` - Delete rule
- `POST /evaluate` - Evaluate rule against test data
- `POST /bulk-evaluate` - Evaluate rules on multiple listings

**Baseline Management:**
- `GET /baseline/summary` - Get baseline metadata
- `POST /baseline/update` - Update baseline system
- `POST /baseline/import` - Import baseline from package

**Rule Structure:**
```typescript
{
  "id": 1,
  "ruleset_id": 1,
  "group_id": 5,
  "name": "CPU Mark Deduction",
  "description": "Deduct 5% for below-average CPU",
  "conditions": [
    {
      "entity": "listing",
      "field": "cpu_mark_score",
      "operator": "less_than",
      "value": 30000
    }
  ],
  "action": {
    "type": "deduct_amount",
    "amount": 25.00,
    "formula": "price_usd * 0.05"
  },
  "priority": 10,
  "is_active": true
}
```

### Admin (`/v1/admin`)

Administrative operations for data management and bulk processing (requires admin auth).

**Endpoints:**
- `POST /tasks/recalculate-valuations` - Queue valuation recalculation job
- `POST /tasks/recalculate-metrics` - Queue metrics recalculation job
- `POST /tasks/import-passmark` - Import CPU benchmark data (CSV)
- `POST /tasks/import-entities` - Import entity definitions
- `GET /tasks/{id}/status` - Get task status

**Example (Recalculate Valuations):**
```bash
POST /v1/admin/tasks/recalculate-valuations
{
  "listing_ids": [1, 2, 3],
  "ruleset_id": 5,
  "batch_size": 50,
  "reason": "Updated baseline rules"
}

Response:
{
  "task_id": "abc123def456",
  "action": "tasks.valuation.recalculate_listings",
  "status": "queued",
  "metadata": {
    "requested_ids": [1, 2, 3],
    "reason": "Updated baseline rules"
  }
}
```

**Task Status Response:**
```json
{
  "task_id": "abc123def456",
  "action": "tasks.valuation.recalculate_listings",
  "status": "in_progress",
  "state": "PROGRESS",
  "result": {"processed": 2, "failed": 0}
}
```

### Entities (`/entities`)

Entity and field metadata for building rule conditions.

**Endpoints:**
- `GET /metadata` - Get all entity definitions with fields and operators

**Response Structure:**
```json
{
  "entities": [
    {
      "key": "listing",
      "label": "PC Listing",
      "fields": [
        {
          "key": "price_usd",
          "label": "Price (USD)",
          "data_type": "number",
          "description": "Asking price",
          "is_custom": false,
          "validation": {"min": 0}
        }
      ]
    }
  ],
  "operators": [
    {
      "value": "equals",
      "label": "Equals",
      "field_types": ["string", "number", "enum"]
    }
  ]
}
```

### Fields (`/v1/reference/fields`)

Core field metadata endpoints.

**Endpoints:**
- `GET` - List all fields (both core and custom)
- `GET /{id}/options` - Get options for enum field
- `POST /{id}/options` - Add option to field
- `DELETE /{id}/options/{option_id}` - Remove option

### Field Data (`/v1/field-data`)

Entity field value management.

**Endpoints:**
- `GET` - List field values for entity
- `POST` - Create field value
- `PUT/{entity_id}/{field_id}` - Update field value for entity
- `DELETE/{entity_id}/{field_id}` - Delete field value

### Settings (`/v1/settings`)

Application settings management.

**Endpoints:**
- `GET` - Get current settings
- `PATCH` - Update settings

**Settings Available:**
- Valuation thresholds (good deal, great deal, premium)
- Default budget amounts
- UI preferences
- Import pipeline settings

### Metrics (`/v1/metrics`)

Performance metrics endpoints.

**Endpoints:**
- `GET` - Get system performance metrics
- `GET/summary` - Get metrics summary
- `GET/{listing_id}` - Get metrics for specific listing

### Telemetry (`/v1/telemetry`)

Logging and observability endpoints.

**Endpoints:**
- `GET /health` - Telemetry system health
- `POST /logs` - Submit telemetry logs
- `GET /config` - Get telemetry configuration

### Baseline (`/v1/baseline`)

Baseline valuation system endpoints.

**Endpoints:**
- `GET /summary` - Baseline summary and version
- `GET /rules` - Get active baseline rules
- `POST /apply` - Apply baseline to listings
- `GET /health` - Baseline health check

## Error Handling

### HTTP Status Codes

| Code | Meaning | When to Handle |
|------|---------|----------------|
| 200 | OK | Success |
| 201 | Created | Resource created |
| 204 | No Content | Deletion successful |
| 400 | Bad Request | Invalid input, validation failed |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource, conflicting data |
| 422 | Unprocessable Entity | Schema validation error |
| 500 | Server Error | Internal error, retry with exponential backoff |

### Example Error Response

```json
{
  "detail": "Validation error: 'title' field is required"
}
```

### Handling Import Conflicts

During Excel import, conflicts are detected and returned:

```json
{
  "conflicts": {
    "duplicate_cpus": [
      {
        "name": "Intel Core i7-13700K",
        "existing_id": 1,
        "action": "skip_or_merge"
      }
    ],
    "duplicate_listings": [
      {
        "title": "Dell OptiPlex 7090",
        "existing_id": 123,
        "checksum": "abc123..."
      }
    ]
  }
}
```

## Performance Considerations

### Database Queries

- All endpoints use async SQLAlchemy for non-blocking I/O
- Listings endpoint pre-loads related components (CPU, GPU) via `selectinload`
- Large result sets are paginated (default limit: 10, max: 100)

### Caching

- CPU/GPU catalog endpoints can be safely cached (rarely changes)
- Ranking metrics are computed on-demand but can be cached for 5-10 minutes
- Custom fields metadata is cached per session

### Bulk Operations

- Bulk updates use batch processing (default: 100 items/batch)
- Recalculation tasks are queued via Celery for async processing
- Monitor task status via `GET /v1/admin/tasks/{task_id}/status`

## Async/Await Pattern

All endpoints are **async** and non-blocking:

```python
@router.get("/listings/{listing_id}")
async def get_listing(listing_id: int, session: AsyncSession = Depends(session_dependency)):
    # Non-blocking database query
    result = await session.get(Listing, listing_id)
    return ListingRead.model_validate(result)
```

The API automatically handles:
- Transaction commit/rollback
- Connection pooling
- Session cleanup

## Development & Testing

### Running Locally

```bash
# Start API server in dev mode
make api

# With auto-reload on code changes
poetry run uvicorn dealbrain_api.main:get_app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all API tests
make test

# Run specific endpoint tests
poetry run pytest tests/test_listings_api.py -v

# Test with database
poetry run pytest tests/test_imports_api.py -v
```

### Environment Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dealbrain
SYNC_DATABASE_URL=postgresql://user:pass@localhost/dealbrain

# Redis (for Celery tasks)
REDIS_URL=redis://localhost:6379/0

# File paths
IMPORT_ROOT=data/imports
EXPORT_ROOT=data/exports
UPLOAD_ROOT=data/uploads

# Telemetry
TELEMETRY__DESTINATION=console
TELEMETRY__LEVEL=INFO
TELEMETRY__ENABLE_TRACING=false
TELEMETRY__OTEL_ENDPOINT=http://localhost:4317

# Ingestion adapters
INGESTION__INGESTION_ENABLED=true
INGESTION__EBAY__ENABLED=true
EBAY_API_KEY=your_ebay_key
```

## API Client Examples

### cURL

```bash
# Get top listings
curl -X GET "http://localhost:8000/api/v1/rankings?metric=score_composite&limit=10" \
  -H "Content-Type: application/json"

# Create listing
curl -X POST "http://localhost:8000/v1/listings" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Dell OptiPlex 7090",
    "price_usd": 450.00,
    "condition": "good",
    "cpu_id": 1
  }'
```

### JavaScript/TypeScript

```typescript
import fetch from 'node-fetch';

// Get rankings
const response = await fetch(
  'http://localhost:8000/api/v1/rankings?metric=score_composite&limit=10'
);
const listings = await response.json();

// Create listing
const createResponse = await fetch('http://localhost:8000/v1/listings', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'Dell OptiPlex 7090',
    price_usd: 450.00,
    condition: 'good',
    cpu_id: 1
  })
});
const newListing = await createResponse.json();
```

### Python

```python
import httpx

# Get rankings
async with httpx.AsyncClient() as client:
    response = await client.get(
        'http://localhost:8000/api/v1/rankings',
        params={'metric': 'score_composite', 'limit': 10}
    )
    listings = response.json()

    # Create listing
    create_response = await client.post(
        'http://localhost:8000/v1/listings',
        json={
            'title': 'Dell OptiPlex 7090',
            'price_usd': 450.00,
            'condition': 'good',
            'cpu_id': 1
        }
    )
    new_listing = create_response.json()
```

## Architecture Notes

### Layered Design

The API follows a clean layered architecture:

1. **Router Layer** (`/api/`) - HTTP handling, request validation, response formatting
2. **Service Layer** (`/services/`) - Business logic, database operations, valuation/scoring calculations
3. **Repository Layer** (via services) - Database access via SQLAlchemy ORM
4. **Models** (`/models/`) - SQLAlchemy ORM definitions
5. **Schemas** (`/schemas/`) - Pydantic request/response contracts

**Domain Logic** shared between API and CLI lives in `packages/core/`:
- `valuation.py` - Pricing adjustments
- `scoring.py` - Composite scoring
- `schemas/` - Data contracts
- `enums.py` - Shared enumerations

### Database Integration

- **ORM**: SQLAlchemy 2.0 async
- **Migrations**: Alembic with auto-generate
- **Transactions**: Automatic commit/rollback per request
- **Connection Pooling**: Configured with pre-ping for connection health

### Task Processing

Long-running operations use Celery background task queue:

```python
# In admin endpoints
recalculate_listings_task.delay(listing_ids=[1,2,3], ruleset_id=5)

# Check status
task_status = AsyncResult(task_id).status
```

## Integration with Frontend

The Next.js frontend communicates with the API via:

```typescript
// apps/web/lib/utils.ts
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// In components
const response = await fetch(`${API_URL}/v1/listings`);
```

Environment variable `NEXT_PUBLIC_API_URL` must be set during build for production deployments.

## Further Reading

- **Listings Detail Guide**: See `/docs/api/listings.md` (coming soon)
- **Import Workflow Guide**: See `/docs/guides/import-workflow.md` (coming soon)
- **Rules & Valuation System**: See `/docs/guides/valuation-rules.md` (coming soon)
- **URL Ingestion Guide**: See `/docs/integrations/url-ingestion.md` (coming soon)
- **Component Catalog**: See `/docs/api/catalog.md` (coming soon)

## Support & Troubleshooting

### Common Issues

**Connection Refused (localhost:8000)**
- Ensure API server is running: `make api`
- Check port is not in use: `lsof -i :8000`

**Database Connection Error**
- Verify `DATABASE_URL` in `.env`
- Ensure Postgres is running: `docker-compose ps`
- Check migrations applied: `make migrate`

**Task Queue Issues**
- Verify Redis running: `docker-compose ps`
- Check Celery worker: `docker-compose logs worker`
- Restart worker: `docker-compose restart worker`

### Debug Mode

Enable verbose logging:

```bash
# Console logs with DEBUG level
TELEMETRY__LEVEL=DEBUG make api

# JSON structured logs
TELEMETRY__LOG_FORMAT=json make api
```

Check Prometheus metrics:
```
http://localhost:9090
```

Check Grafana dashboards:
```
http://localhost:3021 (admin/admin)
```

## Contributing

- All endpoints should have clear docstrings and type hints
- Use Pydantic models for request/response validation
- Follow async/await pattern consistently
- Add tests to `/tests/` for new endpoints
- Run `make format` and `make lint` before committing

## Version History

- **v0.1.0** (Current) - Initial API release with core listing management, catalog, and valuation endpoints

## License

See project LICENSE file.
