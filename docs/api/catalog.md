# Catalog API

The Catalog API manages the component database for Deal Brain, including CPUs, GPUs, RAM specifications, storage profiles, and ports profiles. It provides endpoints to manage these core hardware components and discover which listings use each component.

## Base URL

```
http://localhost:8000/api/v1/catalog
```

## Authentication

All Catalog API endpoints require Clerk JWT authentication via the `Authorization` header.

```typescript
const token = await getToken();
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

## Overview

The Catalog API is organized into logical sections:

| Resource | Purpose |
|----------|---------|
| CPUs | Processor specifications with benchmark data (CPU Mark, single-thread, iGPU) |
| GPUs | Discrete graphics processors with benchmark scores |
| RAM Specs | Memory specifications with generation, speed, capacity, and module info |
| Storage Profiles | Storage configurations (medium, interface, form factor, capacity, performance tier) |
| Ports Profiles | Physical port availability (USB, Thunderbolt, DisplayPort, networking) |
| Scoring Profiles | Valuation profiles with weighted metrics for listing scoring |
| Related Listings | Discover which listings use a specific catalog component |

---

## CPU Catalog

### `GET /cpus`

List all available CPUs in the catalog.

**Response:** `200 OK`

```typescript
interface CpuRead {
  id: number;
  name: string;                    // Unique CPU identifier (e.g., "Intel Core i5-8400")
  manufacturer: string;             // "Intel", "AMD", etc.
  socket: string | null;            // Socket type (e.g., "LGA1151", "AM4")
  cores: number | null;             // Physical core count
  threads: number | null;           // Logical thread count
  tdp_w: number | null;             // Thermal Design Power in watts
  igpu_model: string | null;        // Integrated GPU name (e.g., "UHD Graphics 630")
  cpu_mark_multi: number | null;    // PassMark multi-thread score
  cpu_mark_single: number | null;   // PassMark single-thread score
  igpu_mark: number | null;         // PassMark iGPU score
  release_year: number | null;      // Release year
  notes: string | null;             // Additional notes
  passmark_slug: string | null;     // PassMark identifier slug
  passmark_category: string | null; // PassMark category
  passmark_id: string | null;       // PassMark ID
  attributes: object;               // Custom attributes (JSON)
  created_at: string;               // ISO 8601 timestamp
  updated_at: string;               // ISO 8601 timestamp
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/cpus" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Example Response:**

```json
[
  {
    "id": 1,
    "name": "Intel Core i5-8400",
    "manufacturer": "Intel",
    "socket": "LGA1151",
    "cores": 6,
    "threads": 12,
    "tdp_w": 65,
    "igpu_model": "UHD Graphics 630",
    "cpu_mark_multi": 8456,
    "cpu_mark_single": 2234,
    "igpu_mark": 1450,
    "release_year": 2018,
    "notes": "Budget-friendly 8th gen processor",
    "passmark_slug": "intel-core-i5-8400",
    "passmark_category": "Core i5",
    "passmark_id": "3500",
    "attributes": {
      "generation": "8th Gen Kaby Lake",
      "lithography": "14nm"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

**TypeScript Example:**

```typescript
import { getToken } from '@clerk/nextjs';

async function listCpus() {
  const token = await getToken();
  const response = await fetch('http://localhost:8000/api/v1/catalog/cpus', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  const cpus = await response.json();
  return cpus;
}
```

---

### `GET /cpus/{cpu_id}`

Retrieve a single CPU by ID.

**Path Parameters:**
- `cpu_id` (integer, required): The CPU ID

**Response:** `200 OK` or `404 Not Found`

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/cpus/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```json
{
  "id": 1,
  "name": "Intel Core i5-8400",
  "manufacturer": "Intel",
  "socket": "LGA1151",
  "cores": 6,
  "threads": 12,
  "tdp_w": 65,
  "igpu_model": "UHD Graphics 630",
  "cpu_mark_multi": 8456,
  "cpu_mark_single": 2234,
  "igpu_mark": 1450,
  "release_year": 2018,
  "notes": null,
  "passmark_slug": "intel-core-i5-8400",
  "passmark_category": "Core i5",
  "passmark_id": "3500",
  "attributes": {},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Response (404):**

```json
{
  "detail": "CPU with id 999 not found"
}
```

---

### `POST /cpus`

Create a new CPU in the catalog.

**Request Body:**

```typescript
interface CpuCreate {
  name: string;                    // Required, must be unique
  manufacturer: string;             // Required
  socket?: string | null;
  cores?: number | null;
  threads?: number | null;
  tdp_w?: number | null;
  igpu_model?: string | null;
  cpu_mark_multi?: number | null;
  cpu_mark_single?: number | null;
  igpu_mark?: number | null;
  release_year?: number | null;
  notes?: string | null;
  passmark_slug?: string | null;
  passmark_category?: string | null;
  passmark_id?: string | null;
  attributes?: object;              // Custom attributes
}
```

**Response:** `201 Created`

Returns the created CPU with all fields.

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/catalog/cpus" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Intel Core i7-9700K",
    "manufacturer": "Intel",
    "socket": "LGA1151",
    "cores": 8,
    "threads": 8,
    "tdp_w": 95,
    "igpu_model": "UHD Graphics 630",
    "cpu_mark_multi": 12345,
    "cpu_mark_single": 2500,
    "igpu_mark": 1450,
    "release_year": 2019,
    "notes": "High-end 9th gen processor",
    "passmark_slug": "intel-core-i7-9700k",
    "passmark_category": "Core i7",
    "passmark_id": "3800",
    "attributes": {
      "generation": "9th Gen Coffee Lake",
      "lithography": "14nm"
    }
  }'
```

**Example Response:**

```json
{
  "id": 2,
  "name": "Intel Core i7-9700K",
  "manufacturer": "Intel",
  "socket": "LGA1151",
  "cores": 8,
  "threads": 8,
  "tdp_w": 95,
  "igpu_model": "UHD Graphics 630",
  "cpu_mark_multi": 12345,
  "cpu_mark_single": 2500,
  "igpu_mark": 1450,
  "release_year": 2019,
  "notes": "High-end 9th gen processor",
  "passmark_slug": "intel-core-i7-9700k",
  "passmark_category": "Core i7",
  "passmark_id": "3800",
  "attributes": {
    "generation": "9th Gen Coffee Lake",
    "lithography": "14nm"
  },
  "created_at": "2024-01-16T14:20:00Z",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

**Error Response (400):**

```json
{
  "detail": "CPU already exists"
}
```

**TypeScript Example:**

```typescript
async function createCpu(cpuData: CpuCreate) {
  const token = await getToken();
  const response = await fetch('http://localhost:8000/api/v1/catalog/cpus', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(cpuData)
  });

  if (!response.ok) {
    throw new Error('Failed to create CPU');
  }

  return response.json();
}
```

---

## GPU Catalog

### `GET /gpus`

List all available GPUs in the catalog.

**Response:** `200 OK`

```typescript
interface GpuRead {
  id: number;
  name: string;                    // Unique GPU identifier (e.g., "NVIDIA RTX 2080")
  manufacturer: string;             // "NVIDIA", "AMD", "Intel", etc.
  gpu_mark: number | null;         // PassMark score
  metal_score: number | null;      // Metal (Apple) benchmark score
  notes: string | null;             // Additional notes
  attributes: object;               // Custom attributes (JSON)
  created_at: string;               // ISO 8601 timestamp
  updated_at: string;               // ISO 8601 timestamp
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/gpus" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```json
[
  {
    "id": 1,
    "name": "NVIDIA RTX 2080",
    "manufacturer": "NVIDIA",
    "gpu_mark": 18500,
    "metal_score": null,
    "notes": "High-end gaming GPU",
    "attributes": {
      "memory_gb": 8,
      "architecture": "Turing"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### `GET /gpus/{gpu_id}`

Retrieve a single GPU by ID.

**Path Parameters:**
- `gpu_id` (integer, required): The GPU ID

**Response:** `200 OK` or `404 Not Found`

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/gpus/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### `POST /gpus`

Create a new GPU in the catalog.

**Request Body:**

```typescript
interface GpuCreate {
  name: string;                    // Required, must be unique
  manufacturer: string;             // Required
  gpu_mark?: number | null;
  metal_score?: number | null;
  notes?: string | null;
  attributes?: object;              // Custom attributes
}
```

**Response:** `201 Created`

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/catalog/gpus" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "NVIDIA RTX 3080",
    "manufacturer": "NVIDIA",
    "gpu_mark": 24500,
    "metal_score": null,
    "notes": "High-end gaming GPU",
    "attributes": {
      "memory_gb": 10,
      "architecture": "Ampere"
    }
  }'
```

**Error Response (400):**

```json
{
  "detail": "GPU already exists"
}
```

---

## RAM Specifications

### `GET /ram-specs`

List RAM specifications with optional filtering.

**Query Parameters:**
- `search` (string, optional): Filter by label, generation, or capacity. Performs substring matching.
- `generation` (enum, optional): Filter by RAM generation. Valid values:
  - `ddr3`, `ddr4`, `ddr5`, `lpddr4`, `lpddr4x`, `lpddr5`, `lpddr5x`, `hbm2`, `hbm3`, `unknown`
- `min_capacity_gb` (integer, optional): Minimum total capacity in GB
- `max_capacity_gb` (integer, optional): Maximum total capacity in GB
- `limit` (integer, optional): Maximum results to return (default: 50, max: 200)

**Response:** `200 OK`

```typescript
interface RamSpecRead {
  id: number;
  label: string | null;             // Display label (e.g., "DDR4 3200MHz 32GB (2x16GB)")
  ddr_generation: RamGeneration;    // RAM generation enum
  speed_mhz: number | null;          // Speed in MHz
  module_count: number | null;       // Number of modules
  capacity_per_module_gb: number | null;
  total_capacity_gb: number | null;  // Total capacity in GB
  attributes: object;
  notes: string | null;
  created_at: string;
  updated_at: string;
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/ram-specs?generation=ddr4&min_capacity_gb=16&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```json
[
  {
    "id": 1,
    "label": "DDR4 3200MHz 32GB (2x16GB)",
    "ddr_generation": "ddr4",
    "speed_mhz": 3200,
    "module_count": 2,
    "capacity_per_module_gb": 16,
    "total_capacity_gb": 32,
    "attributes": {},
    "notes": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "label": "DDR4 3600MHz 64GB (2x32GB)",
    "ddr_generation": "ddr4",
    "speed_mhz": 3600,
    "module_count": 2,
    "capacity_per_module_gb": 32,
    "total_capacity_gb": 64,
    "attributes": {},
    "notes": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

**TypeScript Example:**

```typescript
interface RamSpecFilters {
  search?: string;
  generation?: 'ddr3' | 'ddr4' | 'ddr5' | 'lpddr4' | 'lpddr5' | 'unknown';
  min_capacity_gb?: number;
  max_capacity_gb?: number;
  limit?: number;
}

async function listRamSpecs(filters?: RamSpecFilters) {
  const token = await getToken();
  const params = new URLSearchParams();

  if (filters) {
    if (filters.search) params.append('search', filters.search);
    if (filters.generation) params.append('generation', filters.generation);
    if (filters.min_capacity_gb) params.append('min_capacity_gb', filters.min_capacity_gb.toString());
    if (filters.max_capacity_gb) params.append('max_capacity_gb', filters.max_capacity_gb.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
  }

  const response = await fetch(
    `http://localhost:8000/api/v1/catalog/ram-specs?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );

  return response.json();
}
```

---

### `GET /ram-specs/{ram_spec_id}`

Retrieve a single RAM specification by ID.

**Path Parameters:**
- `ram_spec_id` (integer, required): The RAM spec ID

**Response:** `200 OK` or `404 Not Found`

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/ram-specs/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### `POST /ram-specs`

Create a new RAM specification. The endpoint intelligently normalizes input and deduplicates specs.

**Request Body:**

```typescript
interface RamSpecCreate {
  label?: string | null;
  ddr_generation?: RamGeneration;   // Default: "unknown"
  speed_mhz?: number | null;
  module_count?: number | null;
  capacity_per_module_gb?: number | null;
  total_capacity_gb?: number | null;  // Required if module_count/capacity_per_module not provided
  attributes?: object;
  notes?: string | null;
}
```

**Response:** `201 Created`

The endpoint will:
- Automatically generate a label if not provided
- Normalize field names (supports `ram_type`, `generation`, `speed`, `modules`, `module_capacity_gb`, etc.)
- Deduplicate: if a matching spec exists, it returns the existing one
- Validate that total capacity can be determined

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/catalog/ram-specs" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ddr_generation": "ddr5",
    "speed_mhz": 5600,
    "module_count": 2,
    "capacity_per_module_gb": 8,
    "total_capacity_gb": 16,
    "notes": "High-speed DDR5 memory"
  }'
```

**Example Response:**

```json
{
  "id": 3,
  "label": "DDR5 5600MHz 16GB (2x8GB)",
  "ddr_generation": "ddr5",
  "speed_mhz": 5600,
  "module_count": 2,
  "capacity_per_module_gb": 8,
  "total_capacity_gb": 16,
  "attributes": {},
  "notes": "High-speed DDR5 memory",
  "created_at": "2024-01-16T14:20:00Z",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

**Error Response (400):**

```json
{
  "detail": "Unable to determine RAM specification from payload"
}
```

---

## Storage Profiles

### `GET /storage-profiles`

List storage profiles with optional filtering and search.

**Query Parameters:**
- `search` (string, optional): Filter by label, medium, interface, form factor, or capacity. Performs substring matching.
- `medium` (enum, optional): Filter by storage medium. Valid values:
  - `nvme`, `sata_ssd`, `hdd`, `hybrid`, `emmc`, `ufs`, `unknown`
- `min_capacity_gb` (integer, optional): Minimum capacity in GB
- `max_capacity_gb` (integer, optional): Maximum capacity in GB
- `limit` (integer, optional): Maximum results to return (default: 50, max: 200)

**Response:** `200 OK`

```typescript
interface StorageProfileRead {
  id: number;
  label: string | null;             // Display label (e.g., "NVME · NVMe · 512GB")
  medium: StorageMedium;            // Storage type enum
  interface: string | null;         // Interface type (e.g., "NVMe", "SATA")
  form_factor: string | null;       // Form factor (e.g., "M.2", "2.5\"")
  capacity_gb: number | null;       // Capacity in GB
  performance_tier: string | null;  // Performance tier (e.g., "high", "medium")
  attributes: object;
  notes: string | null;
  created_at: string;
  updated_at: string;
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/storage-profiles?medium=nvme&min_capacity_gb=256&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```json
[
  {
    "id": 1,
    "label": "NVME · NVMe · 512GB · M.2",
    "medium": "nvme",
    "interface": "NVMe",
    "form_factor": "M.2",
    "capacity_gb": 512,
    "performance_tier": "high",
    "attributes": {},
    "notes": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

**TypeScript Example:**

```typescript
interface StorageProfileFilters {
  search?: string;
  medium?: 'nvme' | 'sata_ssd' | 'hdd' | 'hybrid' | 'emmc' | 'ufs' | 'unknown';
  min_capacity_gb?: number;
  max_capacity_gb?: number;
  limit?: number;
}

async function listStorageProfiles(filters?: StorageProfileFilters) {
  const token = await getToken();
  const params = new URLSearchParams();

  if (filters) {
    if (filters.search) params.append('search', filters.search);
    if (filters.medium) params.append('medium', filters.medium);
    if (filters.min_capacity_gb) params.append('min_capacity_gb', filters.min_capacity_gb.toString());
    if (filters.max_capacity_gb) params.append('max_capacity_gb', filters.max_capacity_gb.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
  }

  const response = await fetch(
    `http://localhost:8000/api/v1/catalog/storage-profiles?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );

  return response.json();
}
```

---

### `GET /storage-profiles/{storage_profile_id}`

Retrieve a single storage profile by ID.

**Path Parameters:**
- `storage_profile_id` (integer, required): The storage profile ID

**Response:** `200 OK` or `404 Not Found`

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/storage-profiles/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### `POST /storage-profiles`

Create a new storage profile. The endpoint intelligently normalizes input and deduplicates profiles.

**Request Body:**

```typescript
interface StorageProfileCreate {
  label?: string | null;
  medium?: StorageMedium;           // Default: "unknown"
  interface?: string | null;        // e.g., "NVMe", "SATA"
  form_factor?: string | null;      // e.g., "M.2", "2.5\""
  capacity_gb?: number | null;      // Required
  performance_tier?: string | null; // e.g., "high", "medium", "low"
  attributes?: object;
  notes?: string | null;
}
```

**Response:** `201 Created`

The endpoint will:
- Normalize storage medium (supports `ssd`, `sata`, `hard drive`, `hdd`, `pcie`, etc.)
- Automatically generate a label if not provided
- Normalize field names (supports `storage_type`, `bus`, `size`, `tier`, `storage_gb`, etc.)
- Deduplicate: if a matching profile exists, it returns the existing one
- Validate that capacity is provided

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/catalog/storage-profiles" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "medium": "nvme",
    "interface": "NVMe",
    "form_factor": "M.2",
    "capacity_gb": 1024,
    "performance_tier": "high",
    "notes": "High-performance NVMe SSD"
  }'
```

**Example Response:**

```json
{
  "id": 2,
  "label": "NVME · NVMe · 1024GB · M.2",
  "medium": "nvme",
  "interface": "NVMe",
  "form_factor": "M.2",
  "capacity_gb": 1024,
  "performance_tier": "high",
  "attributes": {},
  "notes": "High-performance NVMe SSD",
  "created_at": "2024-01-16T14:20:00Z",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

**Error Response (400):**

```json
{
  "detail": "Unable to determine storage profile from payload"
}
```

---

## Ports Profiles

### `GET /ports-profiles`

List all ports profiles.

**Response:** `200 OK`

```typescript
interface PortRead {
  id: number;
  type: string;                    // Port type (e.g., "usb_a", "hdmi", "thunderbolt")
  count: number;                   // Number of ports (default: 1)
  spec_notes: string | null;       // Additional specs (e.g., "3.1 Gen 2")
  created_at: string;
  updated_at: string;
}

interface PortsProfileRead {
  id: number;
  name: string;                    // Unique profile name
  description: string | null;
  attributes: object;
  ports: PortRead[];               // List of ports in this profile
  created_at: string;
  updated_at: string;
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/ports-profiles" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```json
[
  {
    "id": 1,
    "name": "MacBook Pro 16\" (2023)",
    "description": "Modern MacBook with Thunderbolt and standard ports",
    "attributes": {},
    "ports": [
      {
        "id": 1,
        "type": "usb_c",
        "count": 3,
        "spec_notes": "Thunderbolt 4",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      },
      {
        "id": 2,
        "type": "sdxc",
        "count": 1,
        "spec_notes": null,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### `POST /ports-profiles`

Create a new ports profile with associated ports.

**Request Body:**

```typescript
interface PortCreate {
  type: string;                    // Required (e.g., "usb_a", "usb_c", "hdmi", "thunderbolt", "displayport", "rj45_1g", "audio", "sdxc", "m2_slot", "sata_bay", "other")
  count?: number;                  // Default: 1
  spec_notes?: string | null;
}

interface PortsProfileCreate {
  name: string;                    // Required, must be unique
  description?: string | null;
  attributes?: object;
  ports?: PortCreate[] | null;     // Ports in this profile
}
```

**Response:** `201 Created`

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/catalog/ports-profiles" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Desktop Standard",
    "description": "Typical gaming PC port configuration",
    "attributes": {
      "form_factor": "ATX"
    },
    "ports": [
      {
        "type": "usb_a",
        "count": 4,
        "spec_notes": "3.0"
      },
      {
        "type": "usb_c",
        "count": 2,
        "spec_notes": "3.1 Gen 2"
      },
      {
        "type": "hdmi",
        "count": 1,
        "spec_notes": "2.1"
      },
      {
        "type": "displayport",
        "count": 1,
        "spec_notes": "1.4"
      },
      {
        "type": "rj45_1g",
        "count": 1,
        "spec_notes": null
      }
    ]
  }'
```

**Example Response:**

```json
{
  "id": 2,
  "name": "Gaming Desktop Standard",
  "description": "Typical gaming PC port configuration",
  "attributes": {
    "form_factor": "ATX"
  },
  "ports": [
    {
      "id": 10,
      "type": "usb_a",
      "count": 4,
      "spec_notes": "3.0",
      "created_at": "2024-01-16T14:20:00Z",
      "updated_at": "2024-01-16T14:20:00Z"
    },
    {
      "id": 11,
      "type": "usb_c",
      "count": 2,
      "spec_notes": "3.1 Gen 2",
      "created_at": "2024-01-16T14:20:00Z",
      "updated_at": "2024-01-16T14:20:00Z"
    }
  ],
  "created_at": "2024-01-16T14:20:00Z",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

**Error Response (400):**

```json
{
  "detail": "Ports profile already exists"
}
```

**TypeScript Example:**

```typescript
async function createPortsProfile(profileData: PortsProfileCreate) {
  const token = await getToken();
  const response = await fetch('http://localhost:8000/api/v1/catalog/ports-profiles', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(profileData)
  });

  if (!response.ok) {
    throw new Error('Failed to create ports profile');
  }

  return response.json();
}
```

---

## Scoring Profiles

### `GET /profiles`

List all scoring profiles used for valuation calculations.

**Response:** `200 OK`

```typescript
interface ProfileRead {
  id: number;
  name: string;                    // Unique profile name
  description: string | null;
  weights_json: {                  // Metric weights for composite scoring
    [key: string]: number;         // e.g., {"cpu_mark": 0.4, "gpu_mark": 0.3, "storage": 0.3}
  };
  rule_group_weights?: {           // Weights for rule groups
    [key: string]: number;
  };
  is_default: boolean;             // Whether this is the default profile
  created_at: string;
  updated_at: string;
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/profiles" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```json
[
  {
    "id": 1,
    "name": "Standard Profile",
    "description": "Balanced scoring for general-purpose PCs",
    "weights_json": {
      "cpu_mark_multi": 0.5,
      "cpu_mark_single": 0.3,
      "gpu_mark": 0.2
    },
    "rule_group_weights": {},
    "is_default": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### `POST /profiles`

Create a new scoring profile.

**Request Body:**

```typescript
interface ProfileCreate {
  name: string;                    // Required, must be unique
  description?: string | null;
  weights_json: {                  // Required
    [key: string]: number;
  };
  rule_group_weights?: {           // Optional
    [key: string]: number;
  };
  is_default?: boolean;            // Default: false
}
```

**Response:** `201 Created`

When `is_default` is true, all other profiles are automatically set to non-default.

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/catalog/profiles" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Profile",
    "description": "Emphasizes GPU performance for gaming",
    "weights_json": {
      "cpu_mark_multi": 0.3,
      "cpu_mark_single": 0.2,
      "gpu_mark": 0.5
    },
    "is_default": false
  }'
```

**Example Response:**

```json
{
  "id": 2,
  "name": "Gaming Profile",
  "description": "Emphasizes GPU performance for gaming",
  "weights_json": {
    "cpu_mark_multi": 0.3,
    "cpu_mark_single": 0.2,
    "gpu_mark": 0.5
  },
  "rule_group_weights": {},
  "is_default": false,
  "created_at": "2024-01-16T14:20:00Z",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

**Error Response (400):**

```json
{
  "detail": "Profile already exists"
}
```

---

## Related Listings

These endpoints discover which listings use a specific catalog component.

### `GET /cpus/{cpu_id}/listings`

Get all listings that use a specific CPU.

**Path Parameters:**
- `cpu_id` (integer, required): The CPU ID

**Query Parameters:**
- `limit` (integer, optional): Maximum listings to return (default: 50, max: 100)
- `offset` (integer, optional): Number of listings to skip (default: 0)

**Response:** `200 OK` - Array of `ListingRead` objects, or `404 Not Found` if CPU doesn't exist

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/cpus/1/listings?limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```json
[
  {
    "id": 1,
    "title": "Gaming PC with i5-8400",
    "listing_url": "https://example.com/listing/1",
    "seller": "TechStore",
    "price_usd": 899.99,
    "price_date": "2024-01-16T14:20:00Z",
    "condition": "used",
    "status": "active",
    "cpu_id": 1,
    "gpu_id": null,
    "ram_gb": 16,
    "primary_storage_gb": 512,
    "adjusted_price_usd": 850.00,
    "score_composite": 7.5,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-16T14:20:00Z"
  }
]
```

---

### `GET /gpus/{gpu_id}/listings`

Get all listings that use a specific GPU.

**Path Parameters:**
- `gpu_id` (integer, required): The GPU ID

**Query Parameters:**
- `limit` (integer, optional): Maximum listings to return (default: 50, max: 100)
- `offset` (integer, optional): Number of listings to skip (default: 0)

**Response:** `200 OK` - Array of `ListingRead` objects, or `404 Not Found` if GPU doesn't exist

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/gpus/1/listings?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### `GET /ram-specs/{ram_spec_id}/listings`

Get all listings that use a specific RAM specification.

**Path Parameters:**
- `ram_spec_id` (integer, required): The RAM spec ID

**Query Parameters:**
- `limit` (integer, optional): Maximum listings to return (default: 50, max: 100)
- `offset` (integer, optional): Number of listings to skip (default: 0)

**Response:** `200 OK` - Array of `ListingRead` objects, or `404 Not Found` if RAM spec doesn't exist

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/ram-specs/1/listings?limit=25" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### `GET /storage-profiles/{storage_profile_id}/listings`

Get all listings that use a specific storage profile (either primary or secondary storage).

**Path Parameters:**
- `storage_profile_id` (integer, required): The storage profile ID

**Query Parameters:**
- `limit` (integer, optional): Maximum listings to return (default: 50, max: 100)
- `offset` (integer, optional): Number of listings to skip (default: 0)

**Response:** `200 OK` - Array of `ListingRead` objects, or `404 Not Found` if storage profile doesn't exist

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/storage-profiles/1/listings" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**TypeScript Example:**

```typescript
interface ListingFilters {
  limit?: number;
  offset?: number;
}

async function getStorageProfileListings(
  storageProfileId: number,
  filters?: ListingFilters
) {
  const token = await getToken();
  const params = new URLSearchParams();

  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());

  const response = await fetch(
    `http://localhost:8000/api/v1/catalog/storage-profiles/${storageProfileId}/listings?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Storage profile ${storageProfileId} not found`);
  }

  return response.json();
}
```

---

## Error Handling

All endpoints return consistent error responses.

### Common Error Responses

**404 Not Found**

```json
{
  "detail": "CPU with id 999 not found"
}
```

**400 Bad Request**

```json
{
  "detail": "CPU already exists"
}
```

or

```json
{
  "detail": "Unable to determine RAM specification from payload"
}
```

**500 Internal Server Error**

```json
{
  "detail": "Internal server error"
}
```

### Error Handling in TypeScript

```typescript
async function safeCatalogRequest<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const token = await getToken();
  const response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options?.headers
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}

// Usage
try {
  const cpu = await safeCatalogRequest('/api/v1/catalog/cpus/1');
} catch (error) {
  console.error('Failed to fetch CPU:', error.message);
}
```

---

## Performance & Best Practices

### Pagination

For endpoints that support listing (CPU, GPU, profiles), results are ordered by most recent or relevant:

```typescript
// Fetch all results across multiple pages
async function fetchAllWithPagination(baseUrl: string) {
  const results = [];
  let offset = 0;
  const limit = 50;

  while (true) {
    const url = new URL(baseUrl);
    url.searchParams.append('limit', limit.toString());
    url.searchParams.append('offset', offset.toString());

    const batch = await safeCatalogRequest(url.toString());
    if (batch.length === 0) break;

    results.push(...batch);
    offset += limit;
  }

  return results;
}
```

### Search & Filtering

Use query parameters to reduce payload size:

```typescript
// Instead of fetching all and filtering locally
const token = await getToken();

// Good: Filter server-side
const response = await fetch(
  'http://localhost:8000/api/v1/catalog/ram-specs?generation=ddr4&min_capacity_gb=32',
  { headers: { 'Authorization': `Bearer ${token}` } }
);
```

### Deduplication

RAM specs and storage profiles are automatically deduplicated by the API:

```typescript
// If this spec already exists, you get the existing one back
const ramSpec = await createRamSpec({
  ddr_generation: 'ddr4',
  speed_mhz: 3200,
  total_capacity_gb: 32
});
// ramSpec.id might be an existing ID if this combination already exists
```

### Rate Limiting

The Catalog API is subject to standard rate limiting:

- 100 requests per minute per authenticated user
- Rate limit headers included in all responses:
  - `X-RateLimit-Limit`: Maximum requests per minute
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Unix timestamp of next reset

**Handling Rate Limits:**

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxAttempts = 3
): Promise<T> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429 && attempt < maxAttempts) {
        const retryAfter = parseInt(error.headers.get('Retry-After') || '60');
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retry attempts reached');
}
```

---

## Data Validation

### CPU Unique Constraint

CPU names must be globally unique:

```typescript
// This will fail with 400 if "Intel Core i5-8400" already exists
const cpu = await createCpu({
  name: "Intel Core i5-8400",
  manufacturer: "Intel"
});
```

### RAM Spec Uniqueness

RAM specs are uniquely identified by their dimensions. This combination is unique:
- `ddr_generation`
- `speed_mhz`
- `module_count`
- `capacity_per_module_gb`
- `total_capacity_gb`

```typescript
// These are considered different specs:
const spec1 = await createRamSpec({
  ddr_generation: 'ddr4',
  speed_mhz: 3200,
  total_capacity_gb: 16
});

const spec2 = await createRamSpec({
  ddr_generation: 'ddr4',
  speed_mhz: 3600,  // Different speed
  total_capacity_gb: 16
});
```

### Storage Profile Uniqueness

Storage profiles are uniquely identified by their dimensions:
- `medium`
- `interface`
- `form_factor`
- `capacity_gb`
- `performance_tier`

---

## Field Requirements & Defaults

### CPU

| Field | Required | Default |
|-------|----------|---------|
| name | Yes | |
| manufacturer | Yes | |
| socket | No | null |
| cores | No | null |
| threads | No | null |
| tdp_w | No | null |
| igpu_model | No | null |
| cpu_mark_multi | No | null |
| cpu_mark_single | No | null |
| igpu_mark | No | null |
| release_year | No | null |
| notes | No | null |
| attributes | No | {} |

### RAM Spec

| Field | Required | Default |
|-------|----------|---------|
| total_capacity_gb | Yes* | null |
| ddr_generation | No | unknown |
| speed_mhz | No | null |
| module_count | No | null |
| capacity_per_module_gb | No | null |
| label | No | Auto-generated |
| attributes | No | {} |
| notes | No | null |

*Either `total_capacity_gb` or both `module_count` and `capacity_per_module_gb` must be provided.

### Storage Profile

| Field | Required | Default |
|-------|----------|---------|
| capacity_gb | Yes | |
| medium | No | unknown |
| interface | No | null |
| form_factor | No | null |
| performance_tier | No | null |
| label | No | Auto-generated |
| attributes | No | {} |
| notes | No | null |

### Ports Profile

| Field | Required | Default |
|-------|----------|---------|
| name | Yes | |
| ports | No | [] |
| description | No | null |
| attributes | No | {} |

### Profile (Scoring)

| Field | Required | Default |
|-------|----------|---------|
| name | Yes | |
| weights_json | Yes | |
| description | No | null |
| rule_group_weights | No | {} |
| is_default | No | false |
