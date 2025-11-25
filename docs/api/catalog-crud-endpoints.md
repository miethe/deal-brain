---
title: "Catalog CRUD API Reference"
description: "Complete API reference for catalog entity CRUD operations including CPU, GPU, RAM specifications, storage profiles, ports profiles, and scoring profiles with full update/delete endpoints"
audience: [developers, ai-agents]
tags:
  - api
  - catalog
  - crud
  - endpoints
  - rest
  - cpu
  - gpu
  - ram
  - storage
  - profiles
created: 2025-11-14
updated: 2025-11-14
category: api
status: active
related:
  - /docs/api/catalog-get-endpoints.md
---

# Catalog CRUD API Reference

Complete reference for all CRUD (Create, Read, Update, Delete) operations on catalog entities in Deal Brain. These endpoints manage the core component catalog including CPUs, GPUs, RAM specifications, storage profiles, ports profiles, and scoring profiles.

## Overview

The catalog API provides full CRUD operations for 6 entity types:

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| CPU | POST | GET | PUT/PATCH | DELETE |
| GPU | POST | GET | PUT/PATCH | DELETE |
| RAM Specification | POST | GET | PUT/PATCH | DELETE |
| Storage Profile | POST | GET | PUT/PATCH | DELETE |
| Ports Profile | POST | GET | PUT/PATCH | DELETE |
| Scoring Profile | POST | GET | PUT/PATCH | DELETE |

### HTTP Methods

- **PUT**: Full replacement update (all fields provided)
- **PATCH**: Partial update (only changed fields provided)
- **DELETE**: Hard delete with cascade protection validation

### Response Formats

All endpoints follow consistent response patterns:

**Success Responses:**
- 200 OK (UPDATE operations)
- 201 Created (CREATE operations)
- 204 No Content (DELETE operations)

**Error Responses:**
- 400 Bad Request: Entity already exists or invalid input
- 404 Not Found: Entity doesn't exist
- 409 Conflict: Entity in use, cannot delete
- 422 Unprocessable Entity: Validation error on update

## Common Error Codes

| Status | Code | When | Example |
|--------|------|------|---------|
| 400 | Bad Request | Entity with name already exists on CREATE | `{"detail": "CPU already exists"}` |
| 404 | Not Found | Entity ID doesn't exist | `{"detail": "CPU with id 999 not found"}` |
| 409 | Conflict | Entity in use (DELETE) or only default profile (Profile DELETE) | `{"detail": "Cannot delete CPU: used in 15 listing(s)"}` |
| 422 | Unprocessable Entity | Validation error or unique constraint violation | `{"detail": "CPU with name 'Intel i7' already exists"}` |

## Standard Response Schema

### Success Response (200/201)

All CREATE and UPDATE endpoints return the full entity:

```typescript
interface EntityResponse {
  id: number;
  name: string;
  // ... entity-specific fields
  created_at: string;    // ISO 8601 timestamp
  updated_at: string;    // ISO 8601 timestamp
}
```

### Error Response

```typescript
interface ErrorResponse {
  detail: string | Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}
```

---

# CPU Endpoints

## Update CPU (Full)

### PUT /v1/catalog/cpus/{id}

Updates all fields of a CPU entity. All provided fields replace the existing values.

**Path Parameters:**
- `id` (integer, required): CPU ID

**Request Body:**

```typescript
interface CpuUpdate {
  name: string;                    // CPU model name (required if updating)
  manufacturer: string;             // Intel, AMD, etc.
  socket: string | null;            // Socket type (e.g., "LGA1700")
  cores: integer | null;            // 1-256, physical cores
  threads: integer | null;          // 1-512, logical threads
  tdp_w: integer | null;            // 1-1000, thermal design power in watts
  igpu_model: string | null;        // Integrated GPU model
  cpu_mark_multi: integer | null;   // MultiCore CPU Mark score
  cpu_mark_single: integer | null;  // Single-thread CPU Mark score
  igpu_mark: integer | null;        // iGPU benchmark score
  release_year: integer | null;     // 1970-2100, release year
  notes: string | null;             // Free-form notes
  passmark_slug: string | null;     // PassMark database slug
  passmark_category: string | null; // PassMark category classification
  passmark_id: string | null;       // PassMark database ID
  attributes: object | null;        // Custom attributes (merged on PUT)
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/v1/catalog/cpus/123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Intel Core i7-13700K",
    "manufacturer": "Intel",
    "socket": "LGA1700",
    "cores": 16,
    "threads": 24,
    "tdp_w": 125,
    "cpu_mark_multi": 45000,
    "cpu_mark_single": 4200,
    "igpu_mark": 2500,
    "release_year": 2023,
    "notes": "Raptor Lake architecture, excellent gaming performance",
    "attributes": {
      "generation": "13th Gen",
      "codename": "Raptor Lake"
    }
  }'
```

**Response (200 OK):**

```json
{
  "id": 123,
  "name": "Intel Core i7-13700K",
  "manufacturer": "Intel",
  "socket": "LGA1700",
  "cores": 16,
  "threads": 24,
  "tdp_w": 125,
  "igpu_model": null,
  "cpu_mark_multi": 45000,
  "cpu_mark_single": 4200,
  "igpu_mark": 2500,
  "release_year": 2023,
  "notes": "Raptor Lake architecture, excellent gaming performance",
  "passmark_slug": null,
  "passmark_category": null,
  "passmark_id": null,
  "attributes": {
    "generation": "13th Gen",
    "codename": "Raptor Lake"
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-16T14:30:00Z"
}
```

**Error Responses:**

**404 Not Found** - CPU doesn't exist:
```json
{
  "detail": "CPU with id 999 not found"
}
```

**422 Unprocessable Entity** - Name already exists:
```json
{
  "detail": "CPU with name 'Intel Core i7-13700K' already exists"
}
```

**422 Unprocessable Entity** - Invalid field value:
```json
{
  "detail": [
    {
      "loc": ["body", "cores"],
      "msg": "Input should be less than or equal to 256 [type=less_than_equal, input_value=512, input_type=int]",
      "type": "less_than_equal"
    }
  ]
}
```

**Business Logic:**
- Name must be unique across all CPUs
- Cores: 1-256
- Threads: 1-512
- TDP: 1-1000 watts
- Release year: 1970-2100
- Benchmark scores must be non-negative (>= 0)
- PUT replaces entire attributes object

---

## Update CPU (Partial)

### PATCH /v1/catalog/cpus/{id}

Partially updates a CPU entity. Only provided fields are modified; omitted fields retain their current values.

**Path Parameters:**
- `id` (integer, required): CPU ID

**Request Body:**

Same schema as PUT, but all fields are optional.

```typescript
interface CpuUpdate {
  name?: string;
  manufacturer?: string;
  socket?: string | null;
  cores?: integer | null;
  // ... all fields optional
  attributes?: object | null;  // Merged with existing attributes
}
```

**Example Request (Partial Update):**

```bash
curl -X PATCH http://localhost:8000/v1/catalog/cpus/123 \
  -H "Content-Type: application/json" \
  -d '{
    "cpu_mark_multi": 45500,
    "attributes": {
      "new_key": "added_value"
    }
  }'
```

**Response (200 OK):**

Returns complete CPU with updated fields:

```json
{
  "id": 123,
  "name": "Intel Core i7-13700K",
  "manufacturer": "Intel",
  "socket": "LGA1700",
  "cores": 16,
  "threads": 24,
  "tdp_w": 125,
  "cpu_mark_multi": 45500,
  "cpu_mark_single": 4200,
  "igpu_mark": 2500,
  "release_year": 2023,
  "attributes": {
    "generation": "13th Gen",
    "codename": "Raptor Lake",
    "new_key": "added_value"
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-16T14:45:00Z"
}
```

**Business Logic:**
- Name must remain unique if changed
- Attributes are merged (not replaced) with existing values
- All validation rules same as PUT
- `created_at` timestamp never changes
- `updated_at` timestamp is set to current time

---

## Delete CPU

### DELETE /v1/catalog/cpus/{id}

Deletes a CPU from the catalog. Blocked if the CPU is used in any listings.

**Path Parameters:**
- `id` (integer, required): CPU ID

**Response (204 No Content):**

No body returned on success.

```bash
curl -X DELETE http://localhost:8000/v1/catalog/cpus/123
# Returns 204 No Content with empty body
```

**Error Responses:**

**404 Not Found** - CPU doesn't exist:
```json
{
  "detail": "CPU with id 999 not found"
}
```

**409 Conflict** - CPU is in use:
```json
{
  "detail": "Cannot delete CPU: used in 15 listing(s)"
}
```

**Business Logic:**
- CPU deletion is only allowed if no listings reference it
- Error message includes count of listings using the CPU
- Useful for detecting which entities are safe to delete
- Hard delete from database on success

---

# GPU Endpoints

## Update GPU (Full)

### PUT /v1/catalog/gpus/{id}

Updates all fields of a GPU entity.

**Path Parameters:**
- `id` (integer, required): GPU ID

**Request Body:**

```typescript
interface GpuUpdate {
  name: string;                 // GPU model name (required if updating)
  manufacturer: string;         // NVIDIA, AMD, Intel, etc.
  gpu_mark: integer | null;     // PassMark GPU Mark score
  metal_score: integer | null;  // Metal benchmark score
  notes: string | null;         // Free-form notes
  attributes: object | null;    // Custom attributes
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/v1/catalog/gpus/45 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "RTX 4090",
    "manufacturer": "NVIDIA",
    "gpu_mark": 275000,
    "metal_score": 85000,
    "notes": "Ada Lovelace, flagship consumer GPU",
    "attributes": {
      "memory_gb": 24,
      "memory_type": "GDDR6X",
      "tensor_cores": 16384
    }
  }'
```

**Response (200 OK):**

```json
{
  "id": 45,
  "name": "RTX 4090",
  "manufacturer": "NVIDIA",
  "gpu_mark": 275000,
  "metal_score": 85000,
  "notes": "Ada Lovelace, flagship consumer GPU",
  "attributes": {
    "memory_gb": 24,
    "memory_type": "GDDR6X",
    "tensor_cores": 16384
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-16T14:30:00Z"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "GPU with id 999 not found"
}
```

**422 Unprocessable Entity** - Duplicate name:
```json
{
  "detail": "GPU with name 'RTX 4090' already exists"
}
```

**Business Logic:**
- Name must be unique across all GPUs
- Benchmark scores must be non-negative (>= 0)
- PUT replaces entire attributes object

---

## Update GPU (Partial)

### PATCH /v1/catalog/gpus/{id}

Partially updates a GPU entity. Attributes are merged with existing values.

**Path Parameters:**
- `id` (integer, required): GPU ID

**Request Body:**

All fields optional:

```typescript
interface GpuUpdate {
  name?: string;
  manufacturer?: string;
  gpu_mark?: integer | null;
  metal_score?: integer | null;
  notes?: string | null;
  attributes?: object | null;  // Merged
}
```

**Example Request:**

```bash
curl -X PATCH http://localhost:8000/v1/catalog/gpus/45 \
  -H "Content-Type: application/json" \
  -d '{
    "gpu_mark": 276000,
    "attributes": {
      "power_consumption_w": 450
    }
  }'
```

**Response (200 OK):**

Returns complete GPU with merged attributes.

---

## Delete GPU

### DELETE /v1/catalog/gpus/{id}

Deletes a GPU from the catalog if not in use.

**Path Parameters:**
- `id` (integer, required): GPU ID

**Response (204 No Content):**

No body on success.

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "GPU with id 999 not found"
}
```

**409 Conflict** - In use:
```json
{
  "detail": "Cannot delete GPU: used in 8 listing(s)"
}
```

**Business Logic:**
- Same cascade protection as CPU
- Hard delete on success

---

# RAM Specification Endpoints

## Update RAM Spec (Full)

### PUT /v1/catalog/ram-specs/{id}

Updates all fields of a RAM specification entity.

**Path Parameters:**
- `id` (integer, required): RAM Spec ID

**Request Body:**

```typescript
interface RamSpecUpdate {
  label: string | null;                    // Human-readable label (e.g., "16GB DDR4 3600MHz")
  ddr_generation: RamGeneration;           // DDR3, DDR4, DDR5, LPDDR4, LPDDR5, UNKNOWN
  speed_mhz: integer | null;               // 0-10000, clock speed
  module_count: integer | null;            // 1-8, number of modules
  capacity_per_module_gb: integer | null;  // 1-256, capacity per module
  total_capacity_gb: integer | null;       // 1-2048, total capacity
  notes: string | null;                    // Free-form notes
  attributes: object | null;               // Custom attributes
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/v1/catalog/ram-specs/78 \
  -H "Content-Type: application/json" \
  -d '{
    "label": "32GB DDR5 6000MHz",
    "ddr_generation": "DDR5",
    "speed_mhz": 6000,
    "module_count": 2,
    "capacity_per_module_gb": 16,
    "total_capacity_gb": 32,
    "notes": "High-speed DDR5 for workstations",
    "attributes": {
      "latency_ns": 30,
      "voltage_v": 1.25,
      "cl": 30
    }
  }'
```

**Response (200 OK):**

```json
{
  "id": 78,
  "label": "32GB DDR5 6000MHz",
  "ddr_generation": "DDR5",
  "speed_mhz": 6000,
  "module_count": 2,
  "capacity_per_module_gb": 16,
  "total_capacity_gb": 32,
  "notes": "High-speed DDR5 for workstations",
  "attributes": {
    "latency_ns": 30,
    "voltage_v": 1.25,
    "cl": 30
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-16T14:30:00Z"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "RAM spec with id 999 not found"
}
```

**422 Unprocessable Entity** - Duplicate specification:
```json
{
  "detail": "RAM spec with these specifications already exists"
}
```

**Unique Constraint:**
The combination of (ddr_generation, speed_mhz, module_count, capacity_per_module_gb, total_capacity_gb) must be unique.

**Validation Rules:**
- Speed: 0-10000 MHz
- Module count: 1-8
- Capacity per module: 1-256 GB
- Total capacity: 1-2048 GB

---

## Update RAM Spec (Partial)

### PATCH /v1/catalog/ram-specs/{id}

Partially updates a RAM specification. Attributes are merged.

**Path Parameters:**
- `id` (integer, required): RAM Spec ID

**Request Body:**

All fields optional.

**Example Request:**

```bash
curl -X PATCH http://localhost:8000/v1/catalog/ram-specs/78 \
  -H "Content-Type: application/json" \
  -d '{
    "speed_mhz": 6200,
    "attributes": {
      "brand": "Corsair"
    }
  }'
```

**Response (200 OK):**

Returns complete RAM spec with updated fields.

---

## Delete RAM Spec

### DELETE /v1/catalog/ram-specs/{id}

Deletes a RAM specification from the catalog.

**Path Parameters:**
- `id` (integer, required): RAM Spec ID

**Response (204 No Content):**

No body on success.

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "RAM spec with id 999 not found"
}
```

**409 Conflict** - In use:
```json
{
  "detail": "Cannot delete RAM Spec: used in 12 listing(s)"
}
```

---

# Storage Profile Endpoints

## Update Storage Profile (Full)

### PUT /v1/catalog/storage-profiles/{id}

Updates all fields of a storage profile entity.

**Path Parameters:**
- `id` (integer, required): Storage Profile ID

**Request Body:**

```typescript
interface StorageProfileUpdate {
  label: string | null;               // Human-readable label (e.g., "1TB SSD NVMe")
  medium: StorageMedium;              // SSD, HDD, HYBRID, NVME, UNKNOWN
  interface: string | null;           // SATA, NVMe, SCSI, etc.
  form_factor: string | null;         // M.2, 2.5", 3.5", etc.
  capacity_gb: integer | null;        // 1-100000, capacity in GB
  performance_tier: string | null;    // Consumer, Professional, Enterprise
  notes: string | null;               // Free-form notes
  attributes: object | null;          // Custom attributes
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/v1/catalog/storage-profiles/92 \
  -H "Content-Type: application/json" \
  -d '{
    "label": "2TB NVMe SSD M.2",
    "medium": "NVME",
    "interface": "NVMe",
    "form_factor": "M.2",
    "capacity_gb": 2000,
    "performance_tier": "Consumer",
    "notes": "Fast PCIe 4.0 drive",
    "attributes": {
      "read_speed_mbs": 7100,
      "write_speed_mbs": 6000,
      "pcie_gen": 4,
      "brand": "Samsung 990 Pro"
    }
  }'
```

**Response (200 OK):**

```json
{
  "id": 92,
  "label": "2TB NVMe SSD M.2",
  "medium": "NVME",
  "interface": "NVMe",
  "form_factor": "M.2",
  "capacity_gb": 2000,
  "performance_tier": "Consumer",
  "notes": "Fast PCIe 4.0 drive",
  "attributes": {
    "read_speed_mbs": 7100,
    "write_speed_mbs": 6000,
    "pcie_gen": 4,
    "brand": "Samsung 990 Pro"
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-16T14:30:00Z"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "Storage profile with id 999 not found"
}
```

**422 Unprocessable Entity** - Duplicate specification:
```json
{
  "detail": "Storage profile with these specifications already exists"
}
```

**Unique Constraint:**
The combination of (medium, interface, form_factor, capacity_gb, performance_tier) must be unique.

**Validation Rules:**
- Capacity: 1-100000 GB
- Storage medium normalized to standard values

---

## Update Storage Profile (Partial)

### PATCH /v1/catalog/storage-profiles/{id}

Partially updates a storage profile. Attributes are merged.

**Path Parameters:**
- `id` (integer, required): Storage Profile ID

**Request Body:**

All fields optional.

**Example Request:**

```bash
curl -X PATCH http://localhost:8000/v1/catalog/storage-profiles/92 \
  -H "Content-Type: application/json" \
  -d '{
    "performance_tier": "Professional",
    "attributes": {
      "warranty_years": 5
    }
  }'
```

**Response (200 OK):**

Returns complete storage profile with merged attributes.

---

## Delete Storage Profile

### DELETE /v1/catalog/storage-profiles/{id}

Deletes a storage profile from the catalog.

**Path Parameters:**
- `id` (integer, required): Storage Profile ID

**Response (204 No Content):**

No body on success.

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "Storage profile with id 999 not found"
}
```

**409 Conflict** - In use (primary or secondary storage):
```json
{
  "detail": "Cannot delete Storage Profile: used in 24 listing(s)"
}
```

**Business Logic:**
- Checks if profile is used as primary OR secondary storage
- Usage count includes all referencing listings

---

# Ports Profile Endpoints

## Update Ports Profile (Full)

### PUT /v1/catalog/ports-profiles/{id}

Updates all fields of a ports profile entity and replaces all associated ports.

**Path Parameters:**
- `id` (integer, required): Ports Profile ID

**Request Body:**

```typescript
interface PortsProfileUpdate {
  name: string;                           // Profile name (required if updating)
  description: string | null;             // Free-form description
  attributes: object | null;              // Custom attributes
  ports: Array<{                          // Replace all ports
    type: string;                         // USB-A, USB-C, HDMI, DisplayPort, etc.
    count: integer;                       // 1+, number of this port type
    spec_notes: string | null;            // Version or specification notes
  }> | null;
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/v1/catalog/ports-profiles/156 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Connectivity",
    "description": "Full suite of modern ports",
    "attributes": {
      "audio_jacks": true,
      "headphone_jack": true
    },
    "ports": [
      {
        "type": "USB-A",
        "count": 3,
        "spec_notes": "USB 3.2 Gen 1"
      },
      {
        "type": "USB-C",
        "count": 2,
        "spec_notes": "Thunderbolt 4, 40Gbps"
      },
      {
        "type": "HDMI",
        "count": 1,
        "spec_notes": "HDMI 2.1"
      },
      {
        "type": "DisplayPort",
        "count": 1,
        "spec_notes": "1.4, 8K@60Hz"
      }
    ]
  }'
```

**Response (200 OK):**

```json
{
  "id": 156,
  "name": "Premium Connectivity",
  "description": "Full suite of modern ports",
  "attributes": {
    "audio_jacks": true,
    "headphone_jack": true
  },
  "ports": [
    {
      "id": 301,
      "type": "USB-A",
      "count": 3,
      "spec_notes": "USB 3.2 Gen 1",
      "created_at": "2025-01-16T14:30:00Z",
      "updated_at": "2025-01-16T14:30:00Z"
    },
    {
      "id": 302,
      "type": "USB-C",
      "count": 2,
      "spec_notes": "Thunderbolt 4, 40Gbps",
      "created_at": "2025-01-16T14:30:00Z",
      "updated_at": "2025-01-16T14:30:00Z"
    },
    {
      "id": 303,
      "type": "HDMI",
      "count": 1,
      "spec_notes": "HDMI 2.1",
      "created_at": "2025-01-16T14:30:00Z",
      "updated_at": "2025-01-16T14:30:00Z"
    },
    {
      "id": 304,
      "type": "DisplayPort",
      "count": 1,
      "spec_notes": "1.4, 8K@60Hz",
      "created_at": "2025-01-16T14:30:00Z",
      "updated_at": "2025-01-16T14:30:00Z"
    }
  ],
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-16T14:30:00Z"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "Ports profile with id 999 not found"
}
```

**422 Unprocessable Entity** - Duplicate name:
```json
{
  "detail": "Ports profile with name 'Premium Connectivity' already exists"
}
```

**Business Logic:**
- Name must be unique
- PUT completely replaces the ports list
- Old Port entities are deleted and new ones created
- Port cascade delete handled automatically by database

---

## Update Ports Profile (Partial)

### PATCH /v1/catalog/ports-profiles/{id}

Partially updates a ports profile. Attributes are merged. Ports list replaces all if provided.

**Path Parameters:**
- `id` (integer, required): Ports Profile ID

**Request Body:**

All fields optional. If `ports` array is omitted, existing ports remain unchanged.

```typescript
interface PortsProfileUpdate {
  name?: string;
  description?: string | null;
  attributes?: object | null;        // Merged
  ports?: Array<PortCreate> | null;  // Replace all if provided
}
```

**Example Request (Update Description and Merge Attributes):**

```bash
curl -X PATCH http://localhost:8000/v1/catalog/ports-profiles/156 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated connectivity suite with Thunderbolt 5",
    "attributes": {
      "supports_video": true
    }
  }'
```

**Response (200 OK):**

Returns complete ports profile with merged attributes. Existing ports unchanged.

**Example Request (Replace Ports):**

```bash
curl -X PATCH http://localhost:8000/v1/catalog/ports-profiles/156 \
  -H "Content-Type: application/json" \
  -d '{
    "ports": [
      {
        "type": "USB-C",
        "count": 3,
        "spec_notes": "Thunderbolt 5, 120Gbps"
      },
      {
        "type": "HDMI",
        "count": 1,
        "spec_notes": "HDMI 2.1"
      }
    ]
  }'
```

---

## Delete Ports Profile

### DELETE /v1/catalog/ports-profiles/{id}

Deletes a ports profile and all associated Port entities (cascade delete).

**Path Parameters:**
- `id` (integer, required): Ports Profile ID

**Response (204 No Content):**

No body on success. Associated Port entities are automatically deleted by database cascade.

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "Ports profile with id 999 not found"
}
```

**409 Conflict** - In use:
```json
{
  "detail": "Cannot delete Ports Profile: used in 18 listing(s)"
}
```

**Business Logic:**
- Prevents deletion if any listing references the profile
- Related Port entities automatically deleted by database cascade
- All ports in the profile are removed with the profile

---

# Scoring Profile Endpoints

## Update Scoring Profile (Full)

### PUT /v1/catalog/profiles/{id}

Updates all fields of a scoring profile entity.

**Path Parameters:**
- `id` (integer, required): Profile ID

**Request Body:**

```typescript
interface ProfileUpdate {
  name: string;                    // Profile name (required if updating)
  description: string | null;      // Free-form description
  weights_json: object;            // Scoring weights (e.g., {cpu_mark: 0.3, gpu_mark: 0.2, ...})
  is_default: boolean | null;      // Mark as default profile
}
```

**Example Request:**

```bash
curl -X PUT http://localhost:8000/v1/catalog/profiles/203 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Performance",
    "description": "Optimized weights for gaming workloads",
    "weights_json": {
      "cpu_mark_single": 0.15,
      "gpu_mark": 0.50,
      "ram_capacity": 0.15,
      "storage_speed": 0.10,
      "ports_variety": 0.10
    },
    "is_default": false
  }'
```

**Response (200 OK):**

```json
{
  "id": 203,
  "name": "Gaming Performance",
  "description": "Optimized weights for gaming workloads",
  "weights_json": {
    "cpu_mark_single": 0.15,
    "gpu_mark": 0.50,
    "ram_capacity": 0.15,
    "storage_speed": 0.10,
    "ports_variety": 0.10
  },
  "is_default": false,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-16T14:30:00Z"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "Profile with id 999 not found"
}
```

**422 Unprocessable Entity** - Duplicate name:
```json
{
  "detail": "Profile with name 'Gaming Performance' already exists"
}
```

**422 Unprocessable Entity** - Cannot unset only default:
```json
{
  "detail": "Cannot unset is_default from the only default profile"
}
```

**Business Logic:**
- Name must be unique
- At least one profile must be marked as default
- Cannot unset `is_default` if this is the only default profile
- Setting `is_default` to true automatically unsets other profiles
- PUT replaces entire weights_json object

---

## Update Scoring Profile (Partial)

### PATCH /v1/catalog/profiles/{id}

Partially updates a scoring profile. Weights are merged with existing values.

**Path Parameters:**
- `id` (integer, required): Profile ID

**Request Body:**

All fields optional. Weights are merged, not replaced.

```typescript
interface ProfileUpdate {
  name?: string;
  description?: string | null;
  weights_json?: object | null;  // Merged with existing
  is_default?: boolean | null;
}
```

**Example Request (Update Weights Only):**

```bash
curl -X PATCH http://localhost:8000/v1/catalog/profiles/203 \
  -H "Content-Type: application/json" \
  -d '{
    "weights_json": {
      "cpu_mark_single": 0.20,
      "gpu_mark": 0.55,
      "ram_capacity": 0.10,
      "storage_speed": 0.08,
      "ports_variety": 0.07
    }
  }'
```

**Response (200 OK):**

Returns complete profile with merged weights.

**Business Logic:**
- Weights are merged (new weights combined with existing)
- Same default profile constraints apply
- All validation rules same as PUT

---

## Delete Scoring Profile

### DELETE /v1/catalog/profiles/{id}

Deletes a scoring profile from the catalog.

**Path Parameters:**
- `id` (integer, required): Profile ID

**Response (204 No Content):**

No body on success.

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "Profile with id 999 not found"
}
```

**409 Conflict** - Only default profile:
```json
{
  "detail": "Cannot delete the only default profile"
}
```

**409 Conflict** - In use:
```json
{
  "detail": "Cannot delete Scoring Profile: used in 42 listing(s)"
}
```

**Business Logic:**
- Cannot delete if profile is the only default profile
- Cannot delete if any listing uses this profile
- At least one default profile must always exist
- Hard delete on success

---

## Related Endpoints

### Get Profile Listings

### GET /v1/catalog/profiles/{profile_id}/listings

Retrieves all listings using a specific scoring profile (useful for understanding impact before deletion).

**Path Parameters:**
- `profile_id` (integer, required): Profile ID

**Query Parameters:**
- `limit` (integer, default=50, 1-100): Max results
- `offset` (integer, default=0, >=0): Skip N results

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "name": "Dell XPS 13",
    "price_usd": 1299.00,
    "active_profile_id": 203,
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-16T14:30:00Z"
  },
  // ... more listings
]
```

---

# "Used In" Endpoints

These read-only endpoints show which listings use each catalog entity (useful before deletion):

### GET /v1/catalog/cpus/{cpu_id}/listings
Get all listings using a specific CPU.

### GET /v1/catalog/gpus/{gpu_id}/listings
Get all listings using a specific GPU.

### GET /v1/catalog/ram-specs/{ram_spec_id}/listings
Get all listings using a specific RAM spec.

### GET /v1/catalog/storage-profiles/{storage_profile_id}/listings
Get all listings using a specific storage profile (primary or secondary).

### GET /v1/catalog/ports-profiles/{profile_id}/listings
Get all listings using a specific ports profile.

**Query Parameters (all endpoints):**
- `limit` (integer, default=50, 1-100): Max results
- `offset` (integer, default=0, >=0): Skip N results

**Response (200 OK):**

Returns array of ListingRead schemas with references to the requested entity.

---

# Attributes Field

All catalog entities support custom attributes via the `attributes` field:

**PUT Behavior:**
- Attributes object is completely replaced
- Send full attributes object even for small changes
- Omitted attributes are removed

**PATCH Behavior:**
- Attributes are merged with existing values
- Only provided attributes are updated
- Omitted attributes are preserved

**Example - PUT (Replace):**

```bash
curl -X PUT http://localhost:8000/v1/catalog/cpus/123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Intel Core i7",
    "attributes": {
      "generation": "13th Gen",
      "codename": "Raptor Lake"
    }
  }'
# Old attributes completely replaced
```

**Example - PATCH (Merge):**

```bash
curl -X PATCH http://localhost:8000/v1/catalog/cpus/123 \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "new_field": "new_value"
    }
  }'
# Results in: {"generation": "13th Gen", "codename": "Raptor Lake", "new_field": "new_value"}
```

---

# Changelog

## Phase 1 (Entity Modifications)
- Added PUT endpoints for full updates on all 6 catalog entities
- Added PATCH endpoints for partial updates with attribute merging
- Unique constraint validation on updates
- Tracing integration for all update/delete operations

## Phase 2 (Delete Protection)
- Added DELETE endpoints for all 6 catalog entities
- Cascade protection: prevents deletion of entities in use
- Usage count reporting in error messages
- Cascade delete validation for related entities (e.g., Ports with PortsProfile)
- Default profile protection (cannot delete only default)

---

# Best Practices

## Before Deleting

Always check if an entity is in use before attempting deletion:

```bash
# Check what listings use this CPU
curl http://localhost:8000/v1/catalog/cpus/123/listings

# If the returned array is empty, the DELETE will succeed
# If populated, you'll get a 409 Conflict error with the count
```

## PUT vs PATCH

**Use PUT for:**
- Complete rewrites of an entity
- Certain you want to replace all fields
- Working with full entity representations from GET

**Use PATCH for:**
- Minor updates (e.g., changing one field)
- Updating attributes without providing all other fields
- Batch updates where you want to preserve most existing data

## Handling Conflicts

When a DELETE returns 409 Conflict:

```json
{
  "detail": "Cannot delete CPU: used in 15 listing(s)"
}
```

Query the related endpoint to see which listings need updating:

```bash
curl http://localhost:8000/v1/catalog/cpus/123/listings?limit=100
```

Then reassign those listings to a different CPU before retrying the delete.

---

# Error Handling Reference

| Status | Scenario | Action |
|--------|----------|--------|
| 404 | Entity doesn't exist | Verify ID is correct, may need to create entity |
| 409 | Entity in use (DELETE) | Query usage endpoint, reassign listings, retry delete |
| 409 | Only default profile (Profile DELETE) | Create another default profile first, then delete |
| 422 | Name already exists | Choose different name or verify intent |
| 422 | Validation error | Check field constraints (ranges, types, uniqueness) |

---

# See Also

- [Catalog GET Endpoints](/docs/api/catalog-get-endpoints.md)
- [Catalog CREATE Endpoints](/docs/api/catalog-create-endpoints.md)
- [Deal Brain API Reference](/docs/api/README.md)
