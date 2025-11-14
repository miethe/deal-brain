# Imports API

The Imports API provides endpoints for managing Excel workbook imports with support for field mapping, conflict resolution, and custom field creation during the import process.

## Overview

The import workflow follows these stages:

1. **Upload & Parse**: Upload Excel workbook, detect sheets and columns
2. **Map Fields**: Manually adjust field mappings with suggestions
3. **Resolve Conflicts**: Handle CPU/component conflicts from existing catalog
4. **Commit**: Finalize import with conflict resolutions

All endpoints use the UUID-based import session pattern for state tracking across requests.

---

## Endpoints

### Create Import Session

Create a new import session from Excel workbook upload.

```http
POST /v1/imports/sessions
Content-Type: multipart/form-data

file: <Excel workbook>
declared_entities?: {"Listings": "listing", "CPUs": "cpu"}
```

**Request Parameters:**
- `file` (UploadFile, required): Excel workbook file (.xlsx, .xls)
- `declared_entities` (string, optional): JSON object mapping sheet names to entity types

**Response (201 Created):**

```typescript
interface ImportSessionSnapshot {
  id: string;                    // UUID of import session
  filename: string;              // Original filename
  content_type: string | null;   // MIME type
  status: string;                // "pending" | "mapping" | "reviewing" | "completed"
  checksum: string | null;       // File checksum for deduplication
  sheet_meta: SheetMeta[];       // Detected sheets and columns
  mappings: {                    // Field mappings per entity
    [entity: string]: EntityMapping;
  };
  preview: {                     // Preview of parsed data
    [entity: string]: EntityPreview;
  };
  conflicts: {                   // Detected conflicts
    [key: string]: any;
  };
  declared_entities: {           // Declared entity types
    [sheetName: string]: string;
  };
  created_at: string;            // ISO 8601 timestamp
  updated_at: string;            // ISO 8601 timestamp
}

interface SheetMeta {
  sheet_name: string;
  row_count: number;
  columns: {
    name: string;
    samples: string[];
  }[];
  entity: string | null;         // Detected entity type
  entity_label: string | null;
  confidence: number;            // 0-1 confidence score
  declared_entity: string | null;
}

interface EntityMapping {
  sheet: string | null;
  fields: {
    [fieldKey: string]: FieldMapping;
  };
}

interface FieldMapping {
  field: string;
  label: string;
  required: boolean;
  data_type: string;
  column: string | null;         // Mapped column name
  status: "auto" | "manual" | "missing";
  confidence: number;            // 0-1 confidence score
  suggestions: {
    column: string;
    confidence: number;
    reason?: string;
  }[];
}

interface EntityPreview {
  rows: Record<string, any>[];   // Sample rows
  missing_required_fields: string[];
  total_rows: number;
  mapped_field_count: number;
  component_matches?: ComponentMatch[];
}

interface ComponentMatch {
  row_index: number;
  value: string;
  status: "auto" | "review" | "unmatched";
  auto_match: string | null;    // Matched component
  suggestions: {
    match: string;
    confidence: number;
  }[];
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 400 | BAD_REQUEST | Invalid file format or empty file |
| 422 | UNPROCESSABLE_ENTITY | Invalid JSON in declared_entities |
| 500 | INTERNAL_SERVER_ERROR | Server processing error |

**Examples:**

cURL:
```bash
curl -X POST http://localhost:8000/v1/imports/sessions \
  -F "file=@listings.xlsx" \
  -F 'declared_entities={"Listings":"listing","CPUs":"cpu"}'
```

TypeScript:
```typescript
const formData = new FormData();
formData.append('file', excelFile);
formData.append('declared_entities', JSON.stringify({
  Listings: 'listing',
  CPUs: 'cpu'
}));

const response = await fetch('/v1/imports/sessions', {
  method: 'POST',
  body: formData
});

const session: ImportSessionSnapshot = await response.json();
console.log(`Session created: ${session.id}`);
console.log(`Found ${session.sheet_meta.length} sheets`);
```

---

### List Import Sessions

Retrieve all import sessions in reverse chronological order.

```http
GET /v1/imports/sessions
```

**Query Parameters:** None

**Response (200 OK):**

```typescript
interface ImportSessionListModel {
  sessions: ImportSessionSnapshot[];
}
```

**Examples:**

cURL:
```bash
curl http://localhost:8000/v1/imports/sessions
```

TypeScript:
```typescript
const response = await fetch('/v1/imports/sessions');
const data = await response.json();

console.log(`Found ${data.sessions.length} import sessions`);
data.sessions.forEach(session => {
  console.log(`${session.filename} - ${session.status} (${session.id})`);
});
```

---

### Get Import Session

Retrieve a specific import session with current state.

```http
GET /v1/imports/sessions/{session_id}
```

**Path Parameters:**
- `session_id` (string, required): UUID of the import session

**Response (200 OK):**

```typescript
// Returns ImportSessionSnapshot (same as create endpoint)
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 404 | NOT_FOUND | Session not found |

**Examples:**

cURL:
```bash
curl http://localhost:8000/v1/imports/sessions/550e8400-e29b-41d4-a716-446655440000
```

TypeScript:
```typescript
const sessionId = '550e8400-e29b-41d4-a716-446655440000';
const response = await fetch(`/v1/imports/sessions/${sessionId}`);
const session: ImportSessionSnapshot = await response.json();

console.log(`Session status: ${session.status}`);
console.log(`Total rows: ${session.preview.listing?.total_rows || 0}`);
```

---

### Update Import Mappings

Update field mappings for one or more entities. Triggers preview refresh and conflict detection.

```http
POST /v1/imports/sessions/{session_id}/mappings
Content-Type: application/json

{
  "mappings": {
    "listing": {
      "sheet": "Listings",
      "fields": {
        "title": {
          "column": "Product Name",
          "status": "manual",
          "confidence": 0.95
        }
      }
    }
  }
}
```

**Path Parameters:**
- `session_id` (string, required): UUID of the import session

**Request Body:**

```typescript
interface UpdateMappingsRequest {
  mappings: {
    [entity: string]: {
      sheet?: string;            // Optional sheet name override
      fields?: {
        [fieldKey: string]: {
          column?: string;       // Column to map to
          status?: "auto" | "manual" | "missing";
          confidence?: number;   // 0-1 confidence score
        };
      };
    };
  };
}
```

**Response (200 OK):**

```typescript
// Returns updated ImportSessionSnapshot
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 400 | BAD_REQUEST | Invalid mapping configuration |
| 404 | NOT_FOUND | Session not found |

**Examples:**

cURL:
```bash
curl -X POST http://localhost:8000/v1/imports/sessions/550e8400-e29b-41d4-a716-446655440000/mappings \
  -H "Content-Type: application/json" \
  -d '{
    "mappings": {
      "listing": {
        "sheet": "Listings",
        "fields": {
          "title": {
            "column": "Product Name",
            "status": "manual"
          },
          "price": {
            "column": "Price (USD)",
            "status": "manual"
          }
        }
      }
    }
  }'
```

TypeScript:
```typescript
const sessionId = '550e8400-e29b-41d4-a716-446655440000';
const mappingUpdates = {
  mappings: {
    listing: {
      sheet: 'Listings',
      fields: {
        title: { column: 'Product Name', status: 'manual' as const },
        price: { column: 'Price (USD)', status: 'manual' as const },
        condition: { column: 'Condition', status: 'manual' as const }
      }
    }
  }
};

const response = await fetch(
  `/v1/imports/sessions/${sessionId}/mappings`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(mappingUpdates)
  }
);

const updated: ImportSessionSnapshot = await response.json();
console.log('Mappings updated, conflicts:', updated.conflicts);
```

---

### Refresh Conflicts

Detect and recompute conflicts between imported data and existing catalog.

```http
POST /v1/imports/sessions/{session_id}/conflicts
```

**Path Parameters:**
- `session_id` (string, required): UUID of the import session

**Response (200 OK):**

```typescript
// Returns updated ImportSessionSnapshot with conflicts field populated
```

**Conflict Example:**

```typescript
{
  "conflicts": {
    "cpu_conflicts": [
      {
        "name": "Intel Core i7-10700K",
        "existing": {
          "tdp": 125,
          "base_ghz": 3.8
        },
        "incoming": {
          "tdp": 130,
          "base_ghz": 3.8
        },
        "fields": [
          {
            "field": "tdp",
            "existing": 125,
            "incoming": 130
          }
        ]
      }
    ]
  }
}
```

**Examples:**

cURL:
```bash
curl -X POST http://localhost:8000/v1/imports/sessions/550e8400-e29b-41d4-a716-446655440000/conflicts
```

TypeScript:
```typescript
const sessionId = '550e8400-e29b-41d4-a716-446655440000';
const response = await fetch(
  `/v1/imports/sessions/${sessionId}/conflicts`,
  { method: 'POST' }
);

const session: ImportSessionSnapshot = await response.json();
const cpuConflicts = session.conflicts.cpu_conflicts || [];
console.log(`Found ${cpuConflicts.length} CPU conflicts to resolve`);
```

---

### Commit Import Session

Finalize the import with conflict resolutions and component overrides. Creates records in database.

```http
POST /v1/imports/sessions/{session_id}/commit
Content-Type: application/json

{
  "conflict_resolutions": [
    {
      "entity": "cpu",
      "identifier": "intel-core-i7-10700k",
      "action": "keep"
    }
  ],
  "component_overrides": [
    {
      "entity": "listing",
      "row_index": 5,
      "cpu_match": "intel-core-i7-11700k",
      "gpu_match": "intel-iris-xe"
    }
  ],
  "notes": "Manual override due to listing error"
}
```

**Path Parameters:**
- `session_id` (string, required): UUID of the import session

**Request Body:**

```typescript
interface CommitImportRequest {
  conflict_resolutions?: {
    entity: "cpu";
    identifier: string;          // CPU identifier
    action: "update" | "skip" | "keep";
  }[];
  component_overrides?: {
    entity: "listing";
    row_index: number;
    cpu_match?: string | null;   // CPU to use
    gpu_match?: string | null;   // GPU to use
  }[];
  notes?: string;                // Commit notes
}
```

**Response (200 OK):**

```typescript
interface CommitImportResponse {
  status: string;                // "completed"
  counts: {
    listings_created: number;
    listings_updated: number;
    cpus_created: number;
    cpus_updated: number;
    gpus_created: number;
    gpus_updated: number;
    rules_created: number;
    [key: string]: number;
  };
  session: ImportSessionSnapshot;
  auto_created_cpus: string[];   // CPUs auto-created during import
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 400 | BAD_REQUEST | Invalid resolution or override data |
| 404 | NOT_FOUND | Session not found |
| 422 | UNPROCESSABLE_ENTITY | Conflict validation failed |

**Examples:**

cURL:
```bash
curl -X POST http://localhost:8000/v1/imports/sessions/550e8400-e29b-41d4-a716-446655440000/commit \
  -H "Content-Type: application/json" \
  -d '{
    "conflict_resolutions": [
      {
        "entity": "cpu",
        "identifier": "intel-core-i7-10700k",
        "action": "keep"
      }
    ],
    "component_overrides": [],
    "notes": "Imported from supplier list"
  }'
```

TypeScript:
```typescript
const sessionId = '550e8400-e29b-41d4-a716-446655440000';
const commitRequest = {
  conflict_resolutions: [
    {
      entity: 'cpu',
      identifier: 'intel-core-i7-10700k',
      action: 'keep'
    }
  ],
  component_overrides: [
    {
      entity: 'listing',
      row_index: 0,
      cpu_match: 'intel-core-i7-10700k'
    }
  ],
  notes: 'Bulk import from supplier'
};

const response = await fetch(
  `/v1/imports/sessions/${sessionId}/commit`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(commitRequest)
  }
);

const result = await response.json() as CommitImportResponse;
console.log(`Import complete!`);
console.log(`Created ${result.counts.listings_created} listings`);
console.log(`Auto-created CPUs: ${result.auto_created_cpus.join(', ')}`);
```

---

### Create Custom Field During Import

Create a new custom field and attach it to the import session for mapping.

```http
POST /v1/imports/sessions/{session_id}/fields
Content-Type: application/json

{
  "entity": "listing",
  "key": "ebay_item_number",
  "label": "eBay Item Number",
  "data_type": "string",
  "description": "eBay item ID from listing URL",
  "required": false,
  "default_value": null,
  "options": null,
  "is_active": true,
  "visibility": "standard",
  "created_by": "admin",
  "validation": null,
  "display_order": 10
}
```

**Path Parameters:**
- `session_id` (string, required): UUID of the import session

**Request Body:**

```typescript
interface ImporterFieldCreateRequest {
  entity: string;                // Entity type
  key: string;                   // Field key (alphanumeric, underscore)
  label: string;                 // Display label
  data_type: string;             // "string" | "number" | "boolean" | "date" | "select"
  description?: string;
  required?: boolean;
  default_value?: any;           // Default value (must match data_type)
  options?: {                    // For "select" type
    label: string;
    value: string;
  }[];
  is_active?: boolean;
  visibility?: string;           // "standard" | "advanced" | "hidden"
  created_by?: string;
  validation?: {                 // Optional validation rules
    pattern?: string;            // Regex pattern
    min_length?: number;
    max_length?: number;
    min?: number;
    max?: number;
  };
  display_order?: number;
}
```

**Response (201 Created):**

```typescript
interface ImporterFieldCreateResponse {
  field: {
    id: number;
    entity: string;
    key: string;
    label: string;
    data_type: string;
    description?: string;
    required: boolean;
    default_value?: any;
    options?: any[];
    is_active: boolean;
    is_custom: boolean;
    visibility: string;
    created_by?: string;
    created_at: string;
    updated_at: string;
  };
  session: ImportSessionSnapshot;
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 400 | BAD_REQUEST | Invalid field configuration or key already exists |
| 404 | NOT_FOUND | Session not found |

**Examples:**

cURL:
```bash
curl -X POST http://localhost:8000/v1/imports/sessions/550e8400-e29b-41d4-a716-446655440000/fields \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "listing",
    "key": "ebay_item_number",
    "label": "eBay Item Number",
    "data_type": "string",
    "description": "eBay item ID",
    "required": false,
    "is_active": true
  }'
```

TypeScript:
```typescript
const sessionId = '550e8400-e29b-41d4-a716-446655440000';
const fieldRequest = {
  entity: 'listing',
  key: 'ebay_item_number',
  label: 'eBay Item Number',
  data_type: 'string',
  description: 'eBay item ID from listing URL',
  required: false,
  is_active: true
};

const response = await fetch(
  `/v1/imports/sessions/${sessionId}/fields`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fieldRequest)
  }
);

const result = await response.json();
console.log(`Field created: ${result.field.label}`);
```

---

### Import Workbook (Direct)

Synchronous workbook import from server-side file path. Used for seeding and CLI integration.

```http
POST /v1/imports/workbook
Content-Type: application/json

{
  "path": "/data/listings.xlsx"
}
```

**Request Body:**

```typescript
interface ImportRequest {
  path: string;                  // Absolute file path
}
```

**Response (200 OK):**

```typescript
interface ImportResponse {
  status: string;                // "completed"
  path: string;                  // File path
  counts: {
    listings_created: number;
    listings_updated: number;
    cpus_created: number;
    cpus_updated: number;
    gpus_created: number;
    gpus_updated: number;
    rules_created: number;
    [key: string]: number;
  };
}
```

**Error Responses:**

| Status | Error Code | Description |
|--------|-----------|-------------|
| 404 | NOT_FOUND | Workbook file not found |
| 400 | BAD_REQUEST | Invalid workbook format |
| 500 | INTERNAL_SERVER_ERROR | Import processing error |

**Examples:**

cURL:
```bash
curl -X POST http://localhost:8000/v1/imports/workbook \
  -H "Content-Type: application/json" \
  -d '{"path": "/data/listings.xlsx"}'
```

TypeScript:
```typescript
const response = await fetch('/v1/imports/workbook', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    path: '/data/listings.xlsx'
  })
});

const result = await response.json();
console.log(`Imported ${result.counts.listings_created} listings`);
```

---

## Status Lifecycle

Import sessions follow this status progression:

```
pending → mapping → reviewing → completed
```

- **pending**: Initial state after upload
- **mapping**: Field mappings being configured
- **reviewing**: Conflicts being resolved before commit
- **completed**: Import committed, records created

## Error Handling

All endpoints return structured error responses:

```typescript
interface ErrorResponse {
  error: {
    code: string;                // Error code
    message: string;             // Human-readable message
    details?: {
      field?: string;
      constraint?: string;
      [key: string]: any;
    };
  };
  request_id: string;            // Request ID for debugging
}
```

---

## Rate Limiting

- **Import session creation**: 10 per minute per user
- **Commit operations**: 5 per minute per user
- **List/Get operations**: 100 per minute per user

Response headers:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp
