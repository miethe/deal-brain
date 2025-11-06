# Custom Fields API Documentation

## Overview

The Custom Fields API provides a dynamic system for adding custom metadata fields to Deal Brain entities (listings, CPUs, GPUs, ports profiles). This system enables flexible data modeling without schema migrations while maintaining type safety, validation, and audit trails.

### Key Features

- **Dynamic Field Creation**: Add custom fields to any entity without database migrations
- **Multiple Data Types**: Support for string, number, boolean, enum, multi-select, text, and JSON
- **Validation Rules**: Define patterns, min/max values, and allowed values
- **Dropdown Management**: Inline creation of dropdown options without context switching
- **Default Values**: Configure default values for all field types
- **Field Locking**: Prevent type changes on fields with existing data
- **Audit Logging**: Track all field definition changes with actor and payload information
- **Usage Tracking**: Monitor field utilization across entities
- **Soft Deletes**: Non-destructive deletion with field archival

### Supported Entities

- `listing` - PC Listings with custom attributes like condition, seller notes, etc.
- `cpu` - CPU catalog entries with benchmarks and specifications
- `gpu` - GPU catalog entries
- `ports_profile` - Connectivity specifications for port profiles

---

## Field Definition Endpoints

### `GET /v1/fields` - List All Fields

List all custom field definitions with optional filtering.

#### Request Parameters

```typescript
interface ListFieldsQuery {
  entity?: string;           // Filter by entity type
  include_inactive?: boolean; // Include deactivated fields (default: false)
  include_deleted?: boolean;  // Include soft-deleted fields (default: false)
}
```

#### Response

```typescript
interface FieldListResponse {
  fields: CustomFieldResponse[];
}

interface CustomFieldResponse {
  id: number;
  entity: string;
  key: string;
  label: string;
  data_type: string;
  description?: string;
  required: boolean;
  default_value?: any;
  options?: string[];
  is_active: boolean;
  is_locked: boolean;
  visibility: string;
  created_by?: string;
  validation?: Record<string, any>;
  display_order: number;
  created_at: string;          // ISO 8601
  updated_at: string;          // ISO 8601
  deleted_at?: string | null;  // ISO 8601 or null
}
```

#### Examples

**cURL - List all active fields**

```bash
curl -X GET "http://localhost:8000/v1/fields" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**cURL - Filter by entity**

```bash
curl -X GET "http://localhost:8000/v1/fields?entity=listing" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**cURL - Include deleted fields**

```bash
curl -X GET "http://localhost:8000/v1/fields?include_deleted=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**TypeScript**

```typescript
import { useQuery } from '@tanstack/react-query';

export function useListFields(entity?: string) {
  return useQuery({
    queryKey: ['fields', entity],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (entity) params.append('entity', entity);

      const res = await fetch(`/api/v1/fields?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      return res.json();
    }
  });
}

// Usage
const { data: response } = useListFields('listing');
console.log(response.fields);
```

---

### `POST /v1/fields` - Create Field

Create a new custom field definition. Fields are uniquely identified by entity + key combination.

#### Request Body

```typescript
interface FieldCreateRequest {
  entity: string;              // Entity type (required)
  key: string;                 // Field key, normalized to snake_case (required)
  label: string;               // Human-readable label (required)
  data_type: string;           // 'string' | 'number' | 'boolean' | 'enum' | 'multi_select' | 'text' | 'json'
  description?: string;        // Field description
  required?: boolean;          // Is field required (default: false)
  default_value?: any;         // Default value for new records
  options?: string[];          // Required for enum/multi_select types
  is_active?: boolean;         // Active by default
  is_locked?: boolean;         // Prevent type changes (default: false)
  visibility?: string;         // 'public' | 'private' (default: 'public')
  created_by?: string;         // Username of creator
  validation?: Record<string, any>; // Validation rules
  display_order?: number;      // Sort order in UI (default: 100)
}
```

#### Validation Rules

Field type determines allowed validation keys:

- **string**: `pattern` (regex), `min_length`, `max_length`
- **number**: `min`, `max`
- **all types**: `allowed_values` (list of primitives)

#### Examples

**cURL - Create text field**

```bash
curl -X POST "http://localhost:8000/v1/fields" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "entity": "listing",
    "key": "seller_notes",
    "label": "Seller Notes",
    "data_type": "text",
    "description": "Additional seller notes about the listing",
    "is_active": true,
    "display_order": 10
  }'
```

**cURL - Create dropdown field with options**

```bash
curl -X POST "http://localhost:8000/v1/fields" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "entity": "listing",
    "key": "condition",
    "label": "Condition",
    "data_type": "enum",
    "required": true,
    "options": ["New", "Like New", "Good", "Fair", "Poor"],
    "default_value": "Good",
    "description": "Physical condition of the PC",
    "display_order": 20
  }'
```

**cURL - Create number field with validation**

```bash
curl -X POST "http://localhost:8000/v1/fields" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "entity": "cpu",
    "key": "boost_clock_ghz",
    "label": "Boost Clock (GHz)",
    "data_type": "number",
    "description": "CPU boost clock speed",
    "validation": {
      "min": 2.0,
      "max": 6.0
    }
  }'
```

**TypeScript - Create dropdown field**

```typescript
interface FieldCreatePayload {
  entity: string;
  key: string;
  label: string;
  data_type: 'enum' | 'multi_select' | 'string' | 'number' | 'boolean' | 'text' | 'json';
  options?: string[];
  validation?: Record<string, any>;
  required?: boolean;
  default_value?: any;
  display_order?: number;
}

export async function createField(payload: FieldCreatePayload) {
  const res = await fetch('/api/v1/fields', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail);
  }

  return res.json();
}

// Usage
const field = await createField({
  entity: 'listing',
  key: 'warranty_period_months',
  label: 'Warranty Period (Months)',
  data_type: 'number',
  default_value: 0,
  validation: { min: 0, max: 60 }
});
```

#### Response

Returns the created field with all properties populated.

#### Error Responses

- **400 Bad Request**: Validation error
  - Duplicate field (entity + key combination already exists)
  - Invalid data type
  - Missing required options for enum field
  - Invalid validation rules

- **422 Unprocessable Entity**: Validation failed

```typescript
interface ErrorResponse {
  detail: string;  // Error message
}
```

---

### `PATCH /v1/fields/{field_id}` - Update Field

Update field definition. Some constraints apply based on field state.

#### Path Parameters

- `field_id` (integer): Field definition ID

#### Query Parameters

- `force` (boolean): Allow updates despite dependencies (default: false)
- `actor` (string): Username performing the action

#### Request Body

All properties are optional. Only provided fields are updated.

```typescript
interface FieldUpdateRequest {
  label?: string;
  data_type?: string;
  description?: string;
  required?: boolean;
  default_value?: any;
  options?: string[];
  is_active?: boolean;
  is_locked?: boolean;
  visibility?: string;
  created_by?: string;
  validation?: Record<string, any>;
  display_order?: number;
}
```

#### Constraints

**Locked Fields**: If `is_locked` is true, type cannot be changed. Use `force=true` to bypass.

**Active Deactivation**: Deactivating a field with active values requires `force=true` (409 Conflict).

#### Examples

**cURL - Update field label and description**

```bash
curl -X PATCH "http://localhost:8000/v1/fields/42" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "label": "PC Condition Status",
    "description": "Current physical and functional state"
  }'
```

**cURL - Add validation to existing field**

```bash
curl -X PATCH "http://localhost:8000/v1/fields/15" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "validation": {
      "min": 0,
      "max": 100
    }
  }'
```

**cURL - Deactivate field with force**

```bash
curl -X PATCH "http://localhost:8000/v1/fields/7?force=true&actor=admin@example.com" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "is_active": false
  }'
```

**TypeScript - Update field with optimistic UI**

```typescript
export async function updateField(
  fieldId: number,
  updates: Partial<FieldUpdateRequest>,
  force = false
) {
  const params = new URLSearchParams();
  if (force) params.append('force', 'true');

  const res = await fetch(`/api/v1/fields/${fieldId}?${params}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(updates)
  });

  if (!res.ok) {
    const error = await res.json();

    // Handle dependency conflicts
    if (res.status === 409) {
      console.error('Dependency conflict:', error.detail);
      return { error: error.detail, usage: error.detail.usage };
    }

    throw new Error(error.detail);
  }

  return res.json();
}

// Usage
const result = await updateField(42, {
  label: 'Updated Label',
  description: 'New description'
});
```

#### Error Responses

- **404 Not Found**: Field not found
- **400 Bad Request**: Invalid update (e.g., invalid data type)
- **409 Conflict**: Dependency conflict (field has active values, cannot deactivate without force)

```typescript
interface ConflictError {
  detail: {
    message: string;
    usage: {
      total: number;
      counts: Record<string, number>;  // Usage per entity
    };
  };
}
```

---

### `DELETE /v1/fields/{field_id}` - Delete Field

Delete a field definition. By default, performs soft delete (marks as inactive).

#### Path Parameters

- `field_id` (integer): Field definition ID

#### Query Parameters

- `hard_delete` (boolean): Permanently remove field (default: false for soft delete)
- `force` (boolean): Allow deletion despite active values (default: false)
- `actor` (string): Username performing the action

#### Examples

**cURL - Soft delete (recommended)**

```bash
curl -X DELETE "http://localhost:8000/v1/fields/42" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**cURL - Force delete with usage**

```bash
curl -X DELETE "http://localhost:8000/v1/fields/42?force=true&hard_delete=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**TypeScript - Delete field with confirmation**

```typescript
export async function deleteField(fieldId: number, options = {}) {
  const params = new URLSearchParams();
  if (options.force) params.append('force', 'true');
  if (options.hardDelete) params.append('hard_delete', 'true');

  const res = await fetch(`/api/v1/fields/${fieldId}?${params}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (res.status === 204) {
    return { success: true };
  }

  if (!res.ok) {
    const error = await res.json();

    if (res.status === 409) {
      // Show confirmation dialog with usage info
      console.warn('Field is in use:', error.detail.usage);
      return { conflict: true, usage: error.detail.usage };
    }

    throw new Error(error.detail);
  }
}

// Usage with confirmation
const result = await deleteField(42);
if (result.conflict) {
  const confirmed = await showConfirmDialog(
    `This field is used ${result.usage.total} times. Delete anyway?`
  );
  if (confirmed) {
    await deleteField(42, { force: true });
  }
}
```

#### Response

- **204 No Content**: Successful deletion

#### Error Responses

- **404 Not Found**: Field not found
- **409 Conflict**: Field has active values and `force=false`

---

## Dropdown Options Management

### `POST /v1/reference/custom-fields/{field_id}/options` - Add Field Option

Add a new option to a dropdown or multi-select field. Enables inline option creation without leaving the UI.

#### Path Parameters

- `field_id` (integer): Dropdown field ID

#### Request Body

```typescript
interface AddFieldOptionRequest {
  value: string;  // Option value (required, non-empty)
}
```

#### Examples

**cURL - Add condition option**

```bash
curl -X POST "http://localhost:8000/v1/reference/custom-fields/12/options" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "value": "Refurbished"
  }'
```

**TypeScript - Add option from dropdown**

```typescript
export async function addDropdownOption(fieldId: number, value: string) {
  const res = await fetch(
    `/api/v1/reference/custom-fields/${fieldId}/options`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ value })
    }
  );

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail);
  }

  return res.json();
}

// Usage in dropdown UI
async function handleCreateOption(newValue: string) {
  try {
    const updated = await addDropdownOption(fieldId, newValue);
    setOptions(updated.options);
    setInputValue('');
    showSuccessToast(`Added "${newValue}"`);
  } catch (error) {
    showErrorToast(error.message);
  }
}
```

#### Response

```typescript
interface FieldOptionResponse {
  field_id: number;
  entity: string;
  key: string;
  options: string[];  // All options including the newly added one
}
```

#### Error Responses

- **404 Not Found**: Field not found
- **400 Bad Request**:
  - Field type doesn't support options
  - Option already exists
  - Empty value provided

---

## Global Fields Management

### `GET /v1/fields/{field_id}/history` - Get Field Audit Log

Retrieve audit trail of all changes to a field definition.

#### Path Parameters

- `field_id` (integer): Field definition ID

#### Query Parameters

- `limit` (integer): Maximum number of events (default: 200, max: 500)

#### Response

```typescript
interface FieldAuditEntry {
  id: number;
  field_id: number;
  action: string;  // 'created' | 'updated' | 'soft_deleted' | 'hard_deleted' | 'option_added'
  actor?: string;  // Username of actor
  payload?: Record<string, any>;  // Change details
  created_at: string;
  updated_at: string;
}

interface FieldAuditResponse {
  events: FieldAuditEntry[];
}
```

#### Examples

**cURL - Get recent field changes**

```bash
curl -X GET "http://localhost:8000/v1/fields/42/history?limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**TypeScript - Track field modifications**

```typescript
export function useFieldHistory(fieldId: number) {
  return useQuery({
    queryKey: ['field-history', fieldId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/fields/${fieldId}/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      return res.json();
    }
  });
}

// Component showing audit trail
export function FieldAuditTrail({ fieldId }: { fieldId: number }) {
  const { data } = useFieldHistory(fieldId);

  return (
    <div>
      {data?.events.map((event) => (
        <div key={event.id}>
          <p>{event.action} by {event.actor}</p>
          <p>{new Date(event.created_at).toLocaleString()}</p>
          {event.payload && <pre>{JSON.stringify(event.payload, null, 2)}</pre>}
        </div>
      ))}
    </div>
  );
}
```

---

### `GET /v1/fields/usage` - Get Field Usage Statistics

Track which fields are in use and how many times they appear across entities.

#### Query Parameters

- `entity` (string): Filter by entity type (optional)

#### Response

```typescript
interface FieldUsageRecord {
  field_id: number;
  entity: string;
  key: string;
  total: number;  // Total records using this field
  counts: Record<string, number>;  // Breakdown by entity
}

interface FieldUsageResponse {
  usage: FieldUsageRecord[];
}
```

#### Examples

**cURL - Get all field usage**

```bash
curl -X GET "http://localhost:8000/v1/fields/usage" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**cURL - Filter by entity**

```bash
curl -X GET "http://localhost:8000/v1/fields/usage?entity=listing" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**TypeScript - Usage dashboard**

```typescript
export function useFieldUsage(entity?: string) {
  return useQuery({
    queryKey: ['field-usage', entity],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (entity) params.append('entity', entity);

      const res = await fetch(`/api/v1/fields/usage?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      return res.json();
    }
  });
}

// Component showing which fields are in use
export function FieldUsageDashboard() {
  const { data } = useFieldUsage();

  return (
    <table>
      <thead>
        <tr>
          <th>Field</th>
          <th>Entity</th>
          <th>Usage Count</th>
        </tr>
      </thead>
      <tbody>
        {data?.usage.map((record) => (
          <tr key={record.field_id}>
            <td>{record.key}</td>
            <td>{record.entity}</td>
            <td>{record.total}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

### `GET /v1/fields/{field_name}/values` - Get Distinct Field Values

Retrieve distinct values for a field across all entities. Useful for autocomplete and filtering.

#### Path Parameters

- `field_name` (string): Field name in format `entity.key` (e.g., `listing.condition`)

#### Query Parameters

- `limit` (integer): Maximum values to return (default: 100, max: 1000)
- `search` (string): Optional filter to match values (partial match, case-insensitive)

#### Response

```typescript
interface FieldValuesResponse {
  field_name: string;
  values: string[];
  count: number;
}
```

#### Examples

**cURL - Get all condition values**

```bash
curl -X GET "http://localhost:8000/v1/fields/listing.condition/values?limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**cURL - Search for specific values**

```bash
curl -X GET "http://localhost:8000/v1/fields/listing.seller/values?search=ebay" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**TypeScript - Autocomplete component**

```typescript
export function useFieldValues(fieldName: string, search?: string) {
  return useQuery({
    queryKey: ['field-values', fieldName, search],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('limit', '100');
      if (search) params.append('search', search);

      const res = await fetch(
        `/api/v1/fields/${fieldName}/values?${params}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      return res.json();
    },
    staleTime: 5 * 60 * 1000  // Cache for 5 minutes
  });
}

// Autocomplete input component
export function FieldValueAutocomplete({ fieldName }: { fieldName: string }) {
  const [search, setSearch] = useState('');
  const { data } = useFieldValues(fieldName, search);

  return (
    <div>
      <input
        placeholder="Type to search..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <ul>
        {data?.values.map((value) => (
          <li key={value}>{value}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Entity Metadata and Catalog

### `GET /v1/fields-data/entities` - List Supported Entities

Get list of all entities that support custom fields.

#### Response

```typescript
interface EntityMetadata {
  entity: string;
  label: string;
  primary_key: string;
  supports_custom_fields: string;  // 'true' | 'false'
}

interface EntitiesResponse {
  entities: EntityMetadata[];
}
```

#### Examples

**cURL - List entities**

```bash
curl -X GET "http://localhost:8000/v1/fields-data/entities" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### `GET /v1/fields-data/{entity}/schema` - Get Entity Schema

Get complete schema for an entity including field definitions and catalog records.

#### Path Parameters

- `entity` (string): Entity type (listing, cpu, gpu, ports_profile)

#### Response

Returns comprehensive schema with field metadata and current catalog.

#### Examples

**cURL - Get listing schema**

```bash
curl -X GET "http://localhost:8000/v1/fields-data/listing/schema" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### `GET /v1/fields-data/{entity}/records` - List Entity Records

List all records for a given entity with pagination.

#### Path Parameters

- `entity` (string): Entity type

#### Query Parameters

- `limit` (integer): Records per page (default: 50, max: 200)
- `offset` (integer): Pagination offset (default: 0)

#### Examples

**cURL - List CPU records with pagination**

```bash
curl -X GET "http://localhost:8000/v1/fields-data/cpu/records?limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Data Types and Validation

### Supported Field Types

| Type | Description | Options | Validation Keys |
|------|-------------|---------|-----------------|
| `string` | Text field | None | `pattern`, `min_length`, `max_length` |
| `number` | Numeric value | None | `min`, `max` |
| `boolean` | True/false toggle | None | None |
| `enum` | Single-select dropdown | Required | None |
| `multi_select` | Multi-choice checkbox | Required | None |
| `text` | Long text (textarea) | None | `max_length` |
| `json` | Structured data | None | None |

### Validation Examples

**String Pattern Validation**

```typescript
const field = await createField({
  entity: 'listing',
  key: 'email',
  label: 'Seller Email',
  data_type: 'string',
  validation: {
    pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
  }
});
```

**Number Range Validation**

```typescript
const field = await createField({
  entity: 'cpu',
  key: 'cores',
  label: 'Core Count',
  data_type: 'number',
  validation: {
    min: 1,
    max: 128
  }
});
```

**Length Validation for Text**

```typescript
const field = await createField({
  entity: 'listing',
  key: 'description',
  label: 'Description',
  data_type: 'text',
  validation: {
    min_length: 10,
    max_length: 5000
  }
});
```

**Allowed Values Validation**

```typescript
const field = await createField({
  entity: 'listing',
  key: 'status',
  label: 'Status',
  data_type: 'string',
  validation: {
    allowed_values: ['active', 'inactive', 'archived']
  }
});
```

---

## Default Values

Set default values for fields that apply to new records:

```typescript
// String default
const field = await createField({
  entity: 'listing',
  key: 'notes',
  label: 'Notes',
  data_type: 'string',
  default_value: 'No notes provided'
});

// Numeric default
const field = await createField({
  entity: 'cpu',
  key: 'release_year',
  label: 'Release Year',
  data_type: 'number',
  default_value: 2024
});

// Boolean default
const field = await createField({
  entity: 'listing',
  key: 'is_verified',
  label: 'Verified',
  data_type: 'boolean',
  default_value: false
});

// Enum default
const field = await createField({
  entity: 'listing',
  key: 'condition',
  label: 'Condition',
  data_type: 'enum',
  options: ['New', 'Like New', 'Good', 'Fair'],
  default_value: 'Good'
});
```

---

## Error Handling

### Common Error Scenarios

**Field Already Exists**

```typescript
// Error Response
{
  "detail": "Custom field 'condition' already exists for entity 'listing'"
}
// Status: 400 Bad Request
```

**Field Type Change on Locked Field**

```typescript
// Error Response
{
  "detail": "Locked field 'condition' - type cannot be changed to maintain data integrity"
}
// Status: 400 Bad Request
```

**Field Has Active Values (Cannot Deactivate)**

```typescript
// Error Response
{
  "detail": {
    "message": "Field 'condition' is used 42 time(s) and cannot be deactivated without force",
    "usage": {
      "total": 42,
      "counts": { "listing": 42 }
    }
  }
}
// Status: 409 Conflict
```

**Field Not Found**

```typescript
// Error Response
{
  "detail": "Custom field not found"
}
// Status: 404 Not Found
```

**Invalid Validation Rules**

```typescript
// Error Response
{
  "detail": "Only numeric fields support 'min'/'max' validation"
}
// Status: 400 Bad Request
```

### Error Handling in TypeScript

```typescript
export async function handleFieldOperation<T>(
  operation: () => Promise<T>
): Promise<{ success: boolean; data?: T; error?: string; usage?: any }> {
  try {
    const data = await operation();
    return { success: true, data };
  } catch (error) {
    if (error.response?.status === 409) {
      return {
        success: false,
        error: error.response.data.detail.message,
        usage: error.response.data.detail.usage
      };
    }

    return {
      success: false,
      error: error.response?.data?.detail || error.message
    };
  }
}

// Usage
const result = await handleFieldOperation(() => updateField(42, { is_active: false }));
if (!result.success && result.usage) {
  console.warn(`Field used ${result.usage.total} times. Override with force=true`);
}
```

---

## Field Locking and Integrity

Lock fields to prevent accidental type changes when data already exists:

```typescript
// Create locked field
const field = await createField({
  entity: 'listing',
  key: 'condition',
  label: 'Condition',
  data_type: 'enum',
  options: ['New', 'Like New', 'Good', 'Fair'],
  is_locked: true  // Type cannot be changed
});

// Attempt to change type will fail
try {
  await updateField(field.id, { data_type: 'string' });
} catch (error) {
  console.error(error);  // Cannot change locked field type
}

// But other properties can be updated
await updateField(field.id, {
  label: 'PC Condition',
  description: 'Physical and functional condition'
});
```

---

## Visibility Levels

Control field visibility in the UI:

```typescript
// Public field (visible to all users)
const publicField = await createField({
  entity: 'listing',
  key: 'seller_notes',
  label: 'Seller Notes',
  data_type: 'text',
  visibility: 'public'
});

// Private field (visible to admins only)
const adminField = await createField({
  entity: 'listing',
  key: 'internal_notes',
  label: 'Internal Notes',
  data_type: 'text',
  visibility: 'private'
});
```

---

## Best Practices

1. **Use Consistent Naming**: Keys are auto-normalized to `snake_case`
   ```typescript
   key: 'seller notes'  // Becomes: 'seller_notes'
   ```

2. **Lock Fields Early**: Once a field has values, lock it to prevent type changes
   ```typescript
   await createField({ ..., is_locked: true });
   ```

3. **Provide Clear Labels**: Labels are displayed in the UI
   ```typescript
   key: 'seller_notes',
   label: 'Seller Notes'  // Clear, user-friendly
   ```

4. **Set Display Order**: Control field order in UI
   ```typescript
   display_order: 10  // Earlier numbers appear first
   ```

5. **Validate Early**: Define validation at creation time
   ```typescript
   validation: { min: 0, max: 100 }
   ```

6. **Document with Descriptions**: Help users understand field purpose
   ```typescript
   description: 'Additional seller notes about the listing condition'
   ```

7. **Use Defaults Wisely**: Set sensible defaults for better UX
   ```typescript
   default_value: 'Good'  // For condition field
   ```

8. **Handle Dependencies**: Check usage before deactivating
   ```typescript
   const usage = await getFieldUsage(fieldId);
   if (usage.total > 0) {
     // Show warning or require force flag
   }
   ```

---

## Complete Workflow Example

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

// Create a custom field
export async function setupConditionField() {
  // 1. Create the field definition
  const field = await fetch('/api/v1/fields', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      entity: 'listing',
      key: 'condition',
      label: 'PC Condition',
      data_type: 'enum',
      options: ['New', 'Like New', 'Good', 'Fair', 'Poor'],
      default_value: 'Good',
      required: true,
      is_locked: true,
      display_order: 5
    })
  }).then(r => r.json());

  // 2. Use in form
  return {
    fieldId: field.id,
    options: field.options,
    defaultValue: field.default_value
  };
}

// React component using the field
export function ListingForm() {
  const queryClient = useQueryClient();
  const { data: field } = useQuery({
    queryKey: ['field', 'condition'],
    queryFn: () => fetch('/api/v1/fields?entity=listing')
      .then(r => r.json())
      .then(r => r.fields.find(f => f.key === 'condition'))
  });

  const addOptionMutation = useMutation({
    mutationFn: (value: string) =>
      fetch(`/api/v1/reference/custom-fields/${field.id}/options`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value })
      }).then(r => r.json()),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['field', 'condition'] });
    }
  });

  return (
    <div>
      <select defaultValue={field?.default_value}>
        {field?.options.map(opt => (
          <option key={opt}>{opt}</option>
        ))}
      </select>

      <button onClick={() => addOptionMutation.mutate('Refurbished')}>
        Add Option
      </button>
    </div>
  );
}
```

---

## Rate Limiting and Performance

- Default API rate limit: 100 requests per minute
- Response headers include rate limit info:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

For field values queries with large result sets, use pagination:
```bash
# Paginate through distinct values
curl "http://localhost:8000/v1/fields/listing.seller/values?limit=100&offset=0"
```

---

## See Also

- [API README](./README.md)
- [Listings API](./listings.md)
- [Data Import](../technical/ingestion-pipeline.md)
