# Deal Brain Core Fields Mapping

**Generated:** 2025-10-11
**Purpose:** Comprehensive mapping of all core entity fields across the full stack (Database → Backend → Frontend)

---

## Table of Contents

1. [Overview](#overview)
2. [Core Entities](#core-entities)
   - [Listing](#listing)
   - [CPU](#cpu)
   - [GPU](#gpu)
   - [RamSpec](#ramspec)
   - [StorageProfile](#storageprofile)
   - [ListingComponent](#listingcomponent)
   - [PortsProfile & Port](#portsprofile--port)
3. [Valuation System](#valuation-system)
   - [ValuationRuleset](#valuationruleset)
   - [ValuationRuleGroup](#valuationrulegroup)
   - [ValuationRuleV2](#valuationrulev2)
   - [ValuationRuleCondition](#valuationrulecondition)
   - [ValuationRuleAction](#valuationruleaction)
4. [Supporting Entities](#supporting-entities)
   - [Profile](#profile)
   - [ApplicationSettings](#applicationsettings)
   - [CustomFieldDefinition](#customfielddefinition)
5. [Import/Export Entities](#importexport-entities)
6. [Enumerations](#enumerations)
7. [Discrepancies & Notes](#discrepancies--notes)

---

## Overview

This document provides a complete mapping of all entity fields across the Deal Brain application stack:

- **Database Layer:** PostgreSQL columns (SQLAlchemy models)
- **Backend Layer:** Python types (Pydantic schemas, service layer)
- **Frontend Layer:** TypeScript types (API clients, React components)
- **API Layer:** JSON keys used in HTTP requests/responses

### Mapping Key

- **✓** Field exists and is consistent
- **⚠** Field exists with differences
- **✗** Field missing in this layer
- **→** Derived/computed field

---

## Core Entities

### Listing

The primary entity representing a PC listing with pricing, specifications, and valuation data.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity & Metadata** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Listing Fields** |
| title | `title` | `str` | `string` | `title` | Listing title/name | NOT NULL, max 255 |
| listing_url | `listing_url` | `str \| None` | `string \| null` | `listing_url` | Primary external URL | Text, nullable |
| other_urls | `other_urls` | `list[ListingLink]` | `ListingLink[]` | `other_urls` | Additional URLs with labels | JSON, default=[] |
| seller | `seller` | `str \| None` | `string \| null` | `seller` | Seller name/identifier | Max 128, nullable |
| **Pricing & Status** |
| price_usd | `price_usd` | `float` | `number` | `price_usd` | Listed price in USD | NOT NULL, float |
| price_date | `price_date` | `datetime \| None` | `string \| null` | `price_date` | When price was observed | Nullable |
| condition | `condition` | `Condition` | `string` | `condition` | Item condition | Enum: new/refurb/used |
| status | `status` | `ListingStatus` | `string` | `status` | Listing status | Enum: active/archived/pending |
| **Component References** |
| cpu_id | `cpu_id` | `int \| None` | `number \| null` | `cpu_id` | Foreign key to CPU | FK(cpu.id) |
| gpu_id | `gpu_id` | `int \| None` | `number \| null` | `gpu_id` | Foreign key to GPU | FK(gpu.id) |
| ports_profile_id | `ports_profile_id` | `int \| None` | `number \| null` | `ports_profile_id` | Foreign key to PortsProfile | FK(ports_profile.id) |
| ram_spec_id | `ram_spec_id` | `int \| None` | `number \| null` | `ram_spec_id` | Foreign key to RamSpec | FK(ram_spec.id) |
| primary_storage_profile_id | `primary_storage_profile_id` | `int \| None` | `number \| null` | `primary_storage_profile_id` | FK to primary storage | FK(storage_profile.id) |
| secondary_storage_profile_id | `secondary_storage_profile_id` | `int \| None` | `number \| null` | `secondary_storage_profile_id` | FK to secondary storage | FK(storage_profile.id) |
| **Legacy RAM Fields** |
| ram_gb | `ram_gb` | `int` | `number` | `ram_gb` | Total RAM in GB | Default 0 |
| ram_notes | `ram_notes` | `str \| None` | `string \| null` | `ram_notes` | Additional RAM notes | Text, nullable |
| **Derived RAM Fields (from RamSpec)** |
| ram_type | ✗ (property) | `str \| None` | `string \| null` | `ram_type` | DDR generation (from ram_spec) | → Computed from ram_spec.ddr_generation |
| ram_speed_mhz | ✗ (property) | `int \| None` | `number \| null` | `ram_speed_mhz` | RAM speed (from ram_spec) | → Computed from ram_spec.speed_mhz |
| **Legacy Storage Fields** |
| primary_storage_gb | `primary_storage_gb` | `int` | `number` | `primary_storage_gb` | Primary storage capacity | Default 0 |
| primary_storage_type | `primary_storage_type` | `str \| None` | `string \| null` | `primary_storage_type` | Primary storage type | Max 64, nullable |
| secondary_storage_gb | `secondary_storage_gb` | `int \| None` | `number \| null` | `secondary_storage_gb` | Secondary storage capacity | Nullable |
| secondary_storage_type | `secondary_storage_type` | `str \| None` | `string \| null` | `secondary_storage_type` | Secondary storage type | Max 64, nullable |
| **Other Components** |
| device_model | `device_model` | `str \| None` | `string \| null` | `device_model` | Device model identifier | Max 255, nullable |
| os_license | `os_license` | `str \| None` | `string \| null` | `os_license` | Operating system license | Max 64, nullable |
| other_components | `other_components` | `list[str]` | `string[]` | `other_components` | Additional components | JSON array, default=[] |
| notes | `notes` | `str \| None` | `string \| null` | `notes` | General notes | Text, nullable |
| **Product Metadata (NEW)** |
| manufacturer | `manufacturer` | `str \| None` | `string \| null` | `manufacturer` | Product manufacturer | Max 64, nullable |
| series | `series` | `str \| None` | `string \| null` | `series` | Product series | Max 128, nullable |
| model_number | `model_number` | `str \| None` | `string \| null` | `model_number` | Model number | Max 128, nullable |
| form_factor | `form_factor` | `str \| None` | `string \| null` | `form_factor` | Form factor (SFF, NUC, etc.) | Max 32, nullable |
| **Valuation Fields** |
| adjusted_price_usd | `adjusted_price_usd` | `float \| None` | `number \| null` | `adjusted_price_usd` | Price after valuation rules | Nullable, computed |
| valuation_breakdown | `valuation_breakdown` | `dict[str, Any] \| None` | `ValuationBreakdown \| null` | `valuation_breakdown` | Detailed valuation data | JSON, nullable |
| ruleset_id | `ruleset_id` | `int \| None` | `number \| null` | `ruleset_id` | Static ruleset override | FK(valuation_ruleset.id) |
| **Performance Metrics (Legacy)** |
| score_cpu_multi | `score_cpu_multi` | `float \| None` | `number \| null` | `score_cpu_multi` | Multi-core CPU score | Nullable, computed |
| score_cpu_single | `score_cpu_single` | `float \| None` | `number \| null` | `score_cpu_single` | Single-core CPU score | Nullable, computed |
| score_gpu | `score_gpu` | `float \| None` | `number \| null` | `score_gpu` | GPU score | Nullable, computed |
| score_composite | `score_composite` | `float \| None` | `number \| null` | `score_composite` | Composite score | Nullable, computed |
| dollar_per_cpu_mark | `dollar_per_cpu_mark` | `float \| None` | `number \| null` | `dollar_per_cpu_mark` | Legacy CPU mark metric | Nullable, computed |
| dollar_per_single_mark | `dollar_per_single_mark` | `float \| None` | `number \| null` | `dollar_per_single_mark` | Legacy single-thread metric | Nullable, computed |
| perf_per_watt | `perf_per_watt` | `float \| None` | `number \| null` | `perf_per_watt` | Performance per watt | Nullable, computed |
| **Performance Metrics (NEW)** |
| dollar_per_cpu_mark_single | `dollar_per_cpu_mark_single` | `float \| None` | `number \| null` | `dollar_per_cpu_mark_single` | $/single-thread mark (base) | Nullable, computed |
| dollar_per_cpu_mark_single_adjusted | `dollar_per_cpu_mark_single_adjusted` | `float \| None` | `number \| null` | `dollar_per_cpu_mark_single_adjusted` | $/single-thread (adjusted) | Nullable, computed |
| dollar_per_cpu_mark_multi | `dollar_per_cpu_mark_multi` | `float \| None` | `number \| null` | `dollar_per_cpu_mark_multi` | $/multi-thread mark (base) | Nullable, computed |
| dollar_per_cpu_mark_multi_adjusted | `dollar_per_cpu_mark_multi_adjusted` | `float \| None` | `number \| null` | `dollar_per_cpu_mark_multi_adjusted` | $/multi-thread (adjusted) | Nullable, computed |
| **Profile & Miscellaneous** |
| active_profile_id | `active_profile_id` | `int \| None` | `number \| null` | `active_profile_id` | Active scoring profile | FK(profile.id) |
| raw_listing_json | `raw_listing_json` | `dict[str, Any] \| None` | ✗ | ✗ | Raw import data | JSON, nullable, internal |
| attributes_json | `attributes_json` | `dict[str, Any]` | `Record<string, unknown>` | `attributes` | Custom field values | JSON, default={} |
| **Relationships (Nested Objects in API)** |
| cpu | ✗ (relationship) | `CpuRead \| None` | `CpuRecord \| null` | `cpu` | Nested CPU object | Lazy joined |
| gpu | ✗ (relationship) | `GpuRead \| None` | `object \| null` | `gpu` | Nested GPU object | Lazy joined |
| ram_spec | ✗ (relationship) | `RamSpecRead \| None` | `RamSpecRecord \| null` | `ram_spec` | Nested RamSpec object | Lazy joined |
| primary_storage_profile | ✗ (relationship) | `StorageProfileRead \| None` | `StorageProfileRecord \| null` | `primary_storage_profile` | Nested storage profile | Lazy joined |
| secondary_storage_profile | ✗ (relationship) | `StorageProfileRead \| None` | `StorageProfileRecord \| null` | `secondary_storage_profile` | Nested storage profile | Lazy joined |
| ports_profile | ✗ (relationship) | `PortsProfileRead \| None` | `PortsProfileRecord \| null` | `ports_profile` | Nested ports data | Lazy joined |
| components | ✗ (relationship) | `list[ListingComponentRead]` | ✗ | `components` | Listing components | Cascade delete |

**Custom Fields Support:** ✓ (via `attributes_json` / `attributes`)

---

### CPU

CPU catalog with PassMark benchmark data.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK, indexed |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| name | `name` | `str` | `string` | `name` | CPU name/model | NOT NULL, unique, max 255 |
| manufacturer | `manufacturer` | `str` | `string` | `manufacturer` | Manufacturer (Intel/AMD) | NOT NULL, max 64 |
| socket | `socket` | `str \| None` | `string \| null` | `socket` | CPU socket type | Max 64, nullable |
| cores | `cores` | `int \| None` | `number \| null` | `cores` | Number of cores | Nullable |
| threads | `threads` | `int \| None` | `number \| null` | `threads` | Number of threads | Nullable |
| tdp_w | `tdp_w` | `int \| None` | `number \| null` | `tdp_w` | Thermal Design Power (Watts) | Nullable |
| **Graphics** |
| igpu_model | `igpu_model` | `str \| None` | `string \| null` | `igpu_model` | Integrated GPU model | Max 255, nullable |
| igpu_mark | `igpu_mark` | `int \| None` | `number \| null` | `igpu_mark` | iGPU PassMark score | Nullable |
| **Benchmark Scores** |
| cpu_mark_multi | `cpu_mark_multi` | `int \| None` | `number \| null` | `cpu_mark_multi` | Multi-thread PassMark score | Nullable |
| cpu_mark_single | `cpu_mark_single` | `int \| None` | `number \| null` | `cpu_mark_single` | Single-thread PassMark score | Nullable |
| **Metadata** |
| release_year | `release_year` | `int \| None` | `number \| null` | `release_year` | Year of release | Nullable |
| notes | `notes` | `str \| None` | `string \| null` | `notes` | Additional notes | Text, nullable |
| **PassMark Integration** |
| passmark_slug | `passmark_slug` | `str \| None` | ✗ | ✗ | PassMark URL slug | Max 512, nullable |
| passmark_category | `passmark_category` | `str \| None` | ✗ | ✗ | PassMark category | Max 64, nullable |
| passmark_id | `passmark_id` | `str \| None` | ✗ | ✗ | PassMark identifier | Max 64, nullable |
| **Custom Fields** |
| attributes_json | `attributes_json` | `dict[str, Any]` | ✗ | `attributes` | Custom attributes | JSON, default={} |

**Custom Fields Support:** ✓ (via `attributes_json`)

---

### GPU

GPU catalog with benchmark data.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK, indexed |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| name | `name` | `str` | `string` | `name` | GPU name/model | NOT NULL, unique, max 255 |
| manufacturer | `manufacturer` | `str` | `string` | `manufacturer` | Manufacturer (NVIDIA/AMD/Intel) | NOT NULL, max 64 |
| **Benchmark Scores** |
| gpu_mark | `gpu_mark` | `int \| None` | `number \| null` | `gpu_mark` | PassMark GPU score | Nullable |
| metal_score | `metal_score` | `int \| None` | `number \| null` | `metal_score` | Metal benchmark score | Nullable |
| **Metadata** |
| notes | `notes` | `str \| None` | `string \| null` | `notes` | Additional notes | Text, nullable |
| attributes_json | `attributes_json` | `dict[str, Any]` | ✗ | `attributes` | Custom attributes | JSON, default={} |

**Custom Fields Support:** ✓ (via `attributes_json`)

---

### RamSpec

RAM specification catalog (NEW - added for granular RAM valuation).

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| label | `label` | `str \| None` | `string \| null` | `label` | Human-readable label | Max 128, nullable |
| ddr_generation | `ddr_generation` | `RamGeneration` | `string` | `ddr_generation` | DDR type (ddr3/ddr4/ddr5, etc.) | Enum, NOT NULL, default=UNKNOWN |
| speed_mhz | `speed_mhz` | `int \| None` | `number \| null` | `speed_mhz` | RAM speed in MHz | Nullable |
| module_count | `module_count` | `int \| None` | `number \| null` | `module_count` | Number of modules | Nullable |
| capacity_per_module_gb | `capacity_per_module_gb` | `int \| None` | `number \| null` | `capacity_per_module_gb` | GB per module | Nullable |
| total_capacity_gb | `total_capacity_gb` | `int \| None` | `number \| null` | `total_capacity_gb` | Total capacity in GB | Nullable |
| **Metadata** |
| notes | `notes` | `str \| None` | `string \| null` | `notes` | Additional notes | Text, nullable |
| attributes_json | `attributes_json` | `dict[str, Any]` | ✗ | `attributes` | Custom attributes | JSON, default={} |

**Unique Constraint:** `(ddr_generation, speed_mhz, module_count, capacity_per_module_gb, total_capacity_gb)`

---

### StorageProfile

Storage profile catalog (NEW - added for granular storage valuation).

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| label | `label` | `str \| None` | `string \| null` | `label` | Human-readable label | Max 128, nullable |
| medium | `medium` | `StorageMedium` | `string` | `medium` | Storage type (nvme/sata_ssd/hdd) | Enum, NOT NULL, default=UNKNOWN |
| interface | `interface` | `str \| None` | `string \| null` | `interface` | Interface type (PCIe 3.0/4.0) | Max 64, nullable |
| form_factor | `form_factor` | `str \| None` | `string \| null` | `form_factor` | Form factor (M.2/2.5"/3.5") | Max 64, nullable |
| capacity_gb | `capacity_gb` | `int \| None` | `number \| null` | `capacity_gb` | Capacity in GB | Nullable |
| performance_tier | `performance_tier` | `str \| None` | `string \| null` | `performance_tier` | Performance tier (budget/mid/high) | Max 64, nullable |
| **Metadata** |
| notes | `notes` | `str \| None` | `string \| null` | `notes` | Additional notes | Text, nullable |
| attributes_json | `attributes_json` | `dict[str, Any]` | ✗ | `attributes` | Custom attributes | JSON, default={} |

**Unique Constraint:** `(medium, interface, form_factor, capacity_gb, performance_tier)`

---

### ListingComponent

Components associated with a listing (for legacy valuation system).

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| listing_id | `listing_id` | `int` | ✗ | ✗ | Parent listing ID | FK(listing.id), cascade delete |
| component_type | `component_type` | `ComponentType` | `ComponentType` | `component_type` | Type of component | Enum, NOT NULL, max 32 |
| name | `name` | `str \| None` | `string \| null` | `name` | Component name/model | Max 255, nullable |
| quantity | `quantity` | `int` | `number` | `quantity` | Quantity of component | Default 1 |
| metadata_json | `metadata_json` | `dict[str, Any] \| None` | `Record<string, unknown> \| null` | `metadata_json` | Additional metadata | JSON, nullable |
| adjustment_value_usd | `adjustment_value_usd` | `float \| None` | `number \| null` | `adjustment_value_usd` | Valuation adjustment | Nullable |
| rule_id | `rule_id` | `int \| None` | ⚠ (not in model) | ⚠ | Associated rule ID | ⚠ Added in schema, not in DB |

**Note:** `rule_id` appears in Pydantic schema but not in SQLAlchemy model - potential inconsistency.

---

### PortsProfile & Port

Port configuration profiles for connectivity data.

#### PortsProfile

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| name | `name` | `str` | `string` | `name` | Profile name | NOT NULL, unique, max 128 |
| description | `description` | `str \| None` | `string \| null` | `description` | Profile description | Text, nullable |
| attributes_json | `attributes_json` | `dict[str, Any]` | ✗ | `attributes` | Custom attributes | JSON, default={} |
| **Relationships** |
| ports | ✗ (relationship) | `list[PortRead]` | `PortRecord[]` | `ports` | Associated ports | Cascade delete |

#### Port

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| ports_profile_id | `ports_profile_id` | `int` | ✗ | ✗ | Parent profile ID | FK(ports_profile.id), cascade delete |
| type | `type` | `str` | `string` | `port_type` / `type` | Port type (usb_a, hdmi, etc.) | NOT NULL, max 32 |
| count | `count` | `int` | `number` | `quantity` / `count` | Number of ports | Default 1 |
| spec_notes | `spec_notes` | `str \| None` | `string \| null` | `version` / `notes` / `spec_notes` | Spec details (USB 3.2 Gen 2) | Max 255, nullable |

**Unique Constraint:** `(ports_profile_id, type, spec_notes)`

**⚠ Field Name Inconsistencies:**
- `type` → `port_type` (frontend)
- `count` → `quantity` (some frontend contexts)
- `spec_notes` → `version` or `notes` (some frontend contexts)

---

## Valuation System

### ValuationRuleset

Top-level container for valuation rules.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| name | `name` | `str` | `string` | `name` | Ruleset name | NOT NULL, unique, max 128 |
| description | `description` | `str \| None` | `string \| null` | `description` | Ruleset description | Text, nullable |
| version | `version` | `str` | `string` | `version` | Semantic version | NOT NULL, max 32, default="1.0.0" |
| is_active | `is_active` | `bool` | `boolean` | `is_active` | Whether ruleset is active | NOT NULL, default=True |
| created_by | `created_by` | `str \| None` | `string \| null` | `created_by` | Creator identifier | Max 128, nullable |
| **Configuration** |
| priority | `priority` | `int` | `number` | `priority` | Execution priority (lower first) | NOT NULL, default=10 |
| conditions_json | `conditions_json` | `dict[str, Any]` | `Record<string, any>` | `conditions` | Ruleset-level conditions | JSON, default={} |
| metadata_json | `metadata_json` | `dict[str, Any]` | `Record<string, any>` | `metadata` | Additional metadata | JSON, default={} |
| **Relationships** |
| rule_groups | ✗ (relationship) | `list[RuleGroupResponse]` | `RuleGroup[]` | `rule_groups` | Child rule groups | Cascade delete |

---

### ValuationRuleGroup

Logical grouping of rules within a ruleset.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| ruleset_id | `ruleset_id` | `int` | `number` | `ruleset_id` | Parent ruleset ID | FK(valuation_ruleset.id), cascade delete |
| name | `name` | `str` | `string` | `name` | Group name | NOT NULL, max 128 |
| category | `category` | `str` | `string` | `category` | Category (ram/storage/cpu/etc.) | NOT NULL, max 64 |
| description | `description` | `str \| None` | `string \| null` | `description` | Group description | Text, nullable |
| **Configuration** |
| display_order | `display_order` | `int` | `number` | `display_order` | Display order | NOT NULL, default=100 |
| weight | `weight` | `float` | `number` | `weight` | Group weight | Default=1.0, nullable |
| is_active | `is_active` | `bool` | `boolean` | `is_active` | Whether group is active | NOT NULL, default=True |
| **Relationships** |
| rules | ✗ (relationship) | `list[RuleResponse]` | `Rule[]` | `rules` | Child rules | Cascade delete |

**Unique Constraint:** `(ruleset_id, name)`

---

### ValuationRuleV2

Individual valuation rule with conditions and actions.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| group_id | `group_id` | `int` | `number` | `group_id` | Parent group ID | FK(valuation_rule_group.id), cascade delete |
| name | `name` | `str` | `string` | `name` | Rule name | NOT NULL, max 128 |
| description | `description` | `str \| None` | `string \| null` | `description` | Rule description | Text, nullable |
| **Execution Control** |
| priority | `priority` | `int` | `number` | `priority` | Rule priority | NOT NULL, default=100 |
| is_active | `is_active` | `bool` | `boolean` | `is_active` | Whether rule is active | NOT NULL, default=True |
| evaluation_order | `evaluation_order` | `int` | `number` | `evaluation_order` | Evaluation order | NOT NULL, default=100 |
| **Metadata** |
| metadata_json | `metadata_json` | `dict[str, Any]` | `Record<string, any>` | `metadata` | Additional metadata | JSON, default={} |
| created_by | `created_by` | `str \| None` | `string \| null` | `created_by` | Creator identifier | Max 128, nullable |
| version | `version` | `int` | `number` | `version` | Rule version | NOT NULL, default=1 |
| **Relationships** |
| conditions | ✗ (relationship) | `list[ConditionSchema]` | `Condition[]` | `conditions` | Rule conditions | Cascade delete |
| actions | ✗ (relationship) | `list[ActionSchema]` | `Action[]` | `actions` | Rule actions | Cascade delete |

**Unique Constraint:** `(group_id, name)`

---

### ValuationRuleCondition

Condition logic for rule evaluation.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | ✗ | ✗ | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | ✗ | ✗ | Creation timestamp | Auto (func.now()) |
| **Core Fields** |
| rule_id | `rule_id` | `int` | ✗ | ✗ | Parent rule ID | FK(valuation_rule_v2.id), cascade delete |
| parent_condition_id | `parent_condition_id` | `int \| None` | ✗ | ✗ | Parent for nested conditions | FK(self), cascade delete |
| field_name | `field_name` | `str` | `string` | `field_name` | Field to evaluate (dot notation) | NOT NULL, max 128 |
| field_type | `field_type` | `str` | `string` | `field_type` | Data type of field | NOT NULL, max 32 |
| operator | `operator` | `str` | `string` | `operator` | Comparison operator | NOT NULL, max 32 |
| value_json | `value_json` | `Any` | `any` | `value` | Comparison value | JSON, NOT NULL |
| logical_operator | `logical_operator` | `str \| None` | `string \| null` | `logical_operator` | AND/OR for grouping | Max 8, nullable |
| group_order | `group_order` | `int` | `number` | `group_order` | Order in condition group | NOT NULL, default=0 |

---

### ValuationRuleAction

Action to execute when rule matches.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | ✗ | ✗ | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | ✗ | ✗ | Creation timestamp | Auto (func.now()) |
| **Core Fields** |
| rule_id | `rule_id` | `int` | ✗ | ✗ | Parent rule ID | FK(valuation_rule_v2.id), cascade delete |
| action_type | `action_type` | `str` | `string` | `action_type` | Type of action | NOT NULL, max 32 |
| metric | `metric` | `str \| None` | `string \| null` | `metric` | Metric for calculation | Max 32, nullable |
| value_usd | `value_usd` | `float \| None` | `number \| null` | `value_usd` | USD value | Nullable |
| unit_type | `unit_type` | `str \| None` | `string \| null` | `unit_type` | Unit for calculation | Max 32, nullable |
| formula | `formula` | `str \| None` | `string \| null` | `formula` | Custom formula | Text, nullable |
| modifiers_json | `modifiers_json` | `dict[str, Any]` | `Record<string, any>` | `modifiers` | Modifiers (condition multipliers) | JSON, default={} |
| display_order | `display_order` | `int` | ✗ | ✗ | Display order | NOT NULL, default=0 |

---

## Supporting Entities

### Profile

Scoring profile for weighted metrics.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| name | `name` | `str` | `string` | `name` | Profile name | NOT NULL, unique, max 128 |
| description | `description` | `str \| None` | `string \| null` | `description` | Profile description | Text, nullable |
| weights_json | `weights_json` | `dict[str, float]` | `Record<string, number>` | `weights_json` | Metric weights | JSON, default={} |
| rule_group_weights | `rule_group_weights` | `dict[str, float]` | ✗ | ✗ | Rule group weights | JSON, default={} |
| is_default | `is_default` | `bool` | `boolean` | `is_default` | Whether default profile | NOT NULL, default=False |

---

### ApplicationSettings

Global application settings (key-value store).

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| key | `key` | `str` | `string` | `key` | Settings key | PK, max 64 |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| **Core Fields** |
| value_json | `value_json` | `dict[str, Any]` | `Record<string, any>` | `value_json` | Settings value | JSON, NOT NULL |
| description | `description` | `str \| None` | `string \| null` | `description` | Setting description | Text, nullable |

**Notable Settings:**
- `valuation_thresholds`: Color-coded pricing thresholds (good_deal, great_deal, premium)

---

### CustomFieldDefinition

Custom field definitions for entities.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| **Identity** |
| id | `id` | `int` | `number` | `id` | Primary key | Auto-increment, PK |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| deleted_at | `deleted_at` | `datetime \| None` | `string \| null` | `deleted_at` | Soft delete timestamp | Nullable |
| **Core Fields** |
| entity | `entity` | `str` | `string` | `entity` | Entity type (listing/cpu/etc.) | NOT NULL, max 64 |
| key | `key` | `str` | `string` | `key` | Field key (unique per entity) | NOT NULL, max 64 |
| label | `label` | `str` | `string` | `label` | Display label | NOT NULL, max 128 |
| data_type | `data_type` | `str` | `string` | `data_type` | Data type (string/number/etc.) | NOT NULL, max 32, default="string" |
| description | `description` | `str \| None` | `string \| null` | `description` | Field description | Text, nullable |
| **Validation** |
| required | `required` | `bool` | `boolean` | `required` | Whether field is required | NOT NULL, default=False |
| default_value | `default_value` | `Any \| None` | `unknown` | `default_value` | Default value | JSON, nullable |
| options | `options` | `list[str] \| None` | `string[] \| null` | `options` | Dropdown options | JSON, nullable |
| validation_json | `validation_json` | `dict[str, Any] \| None` | `Record<string, any> \| null` | `validation` | Validation rules | JSON, default={} |
| **Access Control** |
| is_active | `is_active` | `bool` | `boolean` | `is_active` | Whether field is active | NOT NULL, default=True |
| is_locked | `is_locked` | `bool` | `boolean` | `is_locked` | Whether field is locked | NOT NULL, default=False |
| visibility | `visibility` | `str` | `string` | `visibility` | Visibility level | NOT NULL, max 32, default="public" |
| created_by | `created_by` | `str \| None` | `string \| null` | `created_by` | Creator identifier | Max 128, nullable |
| display_order | `display_order` | `int` | `number` | `display_order` | Display order | NOT NULL, default=100 |

**Unique Constraint:** `(entity, key)`

**Indexes:**
- `ix_custom_field_definition_entity` on `entity`
- `ix_custom_field_definition_order` on `(entity, display_order)`

---

## Import/Export Entities

### ImportSession

Session tracking for Excel imports.

| Field Name | DB Column | Backend Type | Frontend Type | API Key | Description | Constraints |
|------------|-----------|--------------|---------------|---------|-------------|-------------|
| id | `id` | `UUID` | `string` | `id` | Primary key (UUID) | PK, UUID |
| created_at | `created_at` | `datetime` | `string` | `created_at` | Creation timestamp | Auto (func.now()) |
| updated_at | `updated_at` | `datetime` | `string` | `updated_at` | Last update timestamp | Auto (onupdate) |
| filename | `filename` | `str` | `string` | `filename` | Original filename | NOT NULL, max 255 |
| content_type | `content_type` | `str \| None` | `string \| null` | `content_type` | MIME type | Max 128, nullable |
| checksum | `checksum` | `str \| None` | `string \| null` | `checksum` | File checksum | Max 64, nullable |
| upload_path | `upload_path` | `str` | `string` | `upload_path` | Server file path | NOT NULL, Text |
| status | `status` | `str` | `string` | `status` | Session status | NOT NULL, max 32, default="pending" |
| sheet_meta_json | `sheet_meta_json` | `dict[str, Any]` | ✗ | `sheet_meta_json` | Sheet metadata | JSON, default={} |
| mappings_json | `mappings_json` | `dict[str, Any]` | ✗ | `mappings_json` | Column mappings | JSON, default={} |
| conflicts_json | `conflicts_json` | `dict[str, Any]` | ✗ | `conflicts_json` | Import conflicts | JSON, default={} |
| preview_json | `preview_json` | `dict[str, Any]` | ✗ | `preview_json` | Preview data | JSON, default={} |
| declared_entities_json | `declared_entities_json` | `dict[str, Any]` | ✗ | `declared_entities_json` | Declared entities | JSON, default={} |
| created_by | `created_by` | `str \| None` | `string \| null` | `created_by` | Creator identifier | Max 128, nullable |

---

## Enumerations

### Condition

Listing condition enumeration.

| Value | Label | Used In |
|-------|-------|---------|
| `new` | New | Listing.condition |
| `refurb` | Refurbished | Listing.condition |
| `used` | Used | Listing.condition |

### ListingStatus

Listing status enumeration.

| Value | Label | Used In |
|-------|-------|---------|
| `active` | Active | Listing.status |
| `archived` | Archived | Listing.status |
| `pending` | Pending | Listing.status |

### RamGeneration

RAM generation/type enumeration.

| Value | Label | Used In |
|-------|-------|---------|
| `ddr3` | DDR3 | RamSpec.ddr_generation |
| `ddr4` | DDR4 | RamSpec.ddr_generation |
| `ddr5` | DDR5 | RamSpec.ddr_generation |
| `lpddr4` | LPDDR4 | RamSpec.ddr_generation |
| `lpddr4x` | LPDDR4X | RamSpec.ddr_generation |
| `lpddr5` | LPDDR5 | RamSpec.ddr_generation |
| `lpddr5x` | LPDDR5X | RamSpec.ddr_generation |
| `hbm2` | HBM2 | RamSpec.ddr_generation |
| `hbm3` | HBM3 | RamSpec.ddr_generation |
| `unknown` | Unknown | RamSpec.ddr_generation (default) |

### StorageMedium

Storage medium/type enumeration.

| Value | Label | Used In |
|-------|-------|---------|
| `nvme` | NVMe | StorageProfile.medium |
| `sata_ssd` | SATA SSD | StorageProfile.medium |
| `hdd` | HDD | StorageProfile.medium |
| `hybrid` | Hybrid | StorageProfile.medium |
| `emmc` | eMMC | StorageProfile.medium |
| `ufs` | UFS | StorageProfile.medium |
| `unknown` | Unknown | StorageProfile.medium (default) |

### ComponentType

Component type for ListingComponent (legacy valuation).

| Value | Label |
|-------|-------|
| `ram` | RAM |
| `ssd` | SSD |
| `hdd` | HDD |
| `os_license` | OS License |
| `wifi` | WiFi |
| `gpu` | GPU |
| `misc` | Miscellaneous |

### PortType

Port type enumeration.

| Value | Label |
|-------|-------|
| `usb_a` | USB-A |
| `usb_c` | USB-C |
| `thunderbolt` | Thunderbolt |
| `hdmi` | HDMI |
| `displayport` | DisplayPort |
| `rj45_1g` | RJ45 (1G) |
| `rj45_2_5g` | RJ45 (2.5G) |
| `rj45_10g` | RJ45 (10G) |
| `audio` | Audio |
| `sdxc` | SDXC |
| `pcie_x16` | PCIe x16 |
| `pcie_x8` | PCIe x8 |
| `m2_slot` | M.2 Slot |
| `sata_bay` | SATA Bay |
| `other` | Other |

---

## Discrepancies & Notes

### 1. Port Field Name Inconsistencies

**Issue:** Port fields have inconsistent naming across layers.

- **DB:** `type`, `count`, `spec_notes`
- **Frontend (TypeScript):** `port_type`, `quantity`, `version`/`notes`

**Impact:** Requires mapping in API layer and frontend transforms.

**Recommendation:** Standardize to `port_type`, `count`, `spec_notes` across all layers.

---

### 2. ListingComponent `rule_id` Field

**Issue:** `rule_id` appears in Pydantic schema but not in SQLAlchemy model.

```python
# In schemas/listing.py
class ListingComponentBase(DealBrainModel):
    ...
    rule_id: int | None = None  # ✗ Not in DB model
```

**Impact:** Field exists in API but cannot be persisted.

**Recommendation:** Either add to DB model or remove from schema.

---

### 3. Performance Metrics Dual Systems

**Issue:** Both legacy and new performance metrics coexist.

**Legacy Metrics:**
- `dollar_per_cpu_mark`
- `dollar_per_single_mark`

**New Metrics:**
- `dollar_per_cpu_mark_single` / `dollar_per_cpu_mark_single_adjusted`
- `dollar_per_cpu_mark_multi` / `dollar_per_cpu_mark_multi_adjusted`

**Impact:** Potential confusion about which metrics to use.

**Recommendation:** Deprecate legacy metrics once new system is fully validated.

---

### 4. Custom Fields Storage Pattern

**Pattern:** Most entities use `attributes_json` for custom field storage.

**Entities with Custom Fields:**
- Listing: `attributes_json` → API key: `attributes`
- CPU: `attributes_json` → API key: `attributes`
- GPU: `attributes_json` → API key: `attributes`
- RamSpec: `attributes_json` → API key: `attributes`
- StorageProfile: `attributes_json` → API key: `attributes`
- PortsProfile: `attributes_json` → API key: `attributes`

**Consistency:** ✓ Good - Pattern is consistent across entities.

---

### 5. Relationship vs. Direct Field Data

**Issue:** Some relationships are exposed as nested objects in API responses.

**Examples:**
- `Listing.cpu` (relationship) → API: `cpu: CpuRecord | null`
- `Listing.ram_spec` (relationship) → API: `ram_spec: RamSpecRecord | null`
- `Listing.ports_profile` (relationship) → API: `ports_profile: PortsProfileRecord | null`

**Pattern:** SQLAlchemy relationships with `lazy="joined"` or `lazy="selectin"` are serialized to nested objects.

**Consistency:** ✓ Good - Standard pattern throughout the app.

---

### 6. Enum Value Consistency

**Issue:** Enum values are lowercase in database, sometimes mixed case in frontend.

**Example - RamGeneration:**
- DB/Backend: `"ddr4"`, `"ddr5"`, `"lpddr5x"`
- Frontend displays: May be uppercased for UI

**Pattern:** Backend uses lowercase enum values, frontend handles display formatting.

**Consistency:** ✓ Acceptable - Presentation layer responsibility.

---

### 7. Timestamp Patterns

**Pattern:** All entities with `TimestampMixin` have:
- `created_at: datetime` (auto, func.now())
- `updated_at: datetime` (auto, onupdate=func.now())

**API Serialization:** Timestamps are serialized to ISO 8601 strings.

**Consistency:** ✓ Excellent - Uniform across all entities.

---

### 8. ID Field Types

**Pattern Analysis:**

| Entity | ID Type | Note |
|--------|---------|------|
| Most entities | `int` (auto-increment) | Standard pattern |
| ImportSession | `UUID` | Uses UUID for distributed imports |

**Consistency:** ✓ Good - UUID only used where needed for distributed systems.

---

### 9. Nullable vs. Optional Patterns

**Backend Pattern:**
- Pydantic: `str | None` (modern Python union syntax)
- SQLAlchemy: `Mapped[str | None]` with `nullable=True`

**Frontend Pattern:**
- TypeScript: `string | null` (explicit null)
- Optional fields: `field?: string` (undefined or present)

**Consistency:** ✓ Good - Each layer uses idiomatic patterns.

---

### 10. JSON Field Naming

**Backend Pattern:** `*_json` suffix on SQLAlchemy models
- `attributes_json`
- `metadata_json`
- `conditions_json`
- `value_json`

**API Pattern:** JSON suffix removed in API keys
- `attributes_json` → `attributes`
- `metadata_json` → `metadata`
- `conditions_json` → `conditions`

**Consistency:** ✓ Good - Clean API contract, descriptive DB columns.

---

## Summary

### Strengths

1. **Consistent Timestamp Pattern:** All entities use `TimestampMixin` with `created_at` and `updated_at`.
2. **Custom Fields Architecture:** Unified `attributes_json` pattern across entities.
3. **Type Safety:** Strong typing in Python (Pydantic) and TypeScript.
4. **Relationship Handling:** Consistent nested object serialization for relationships.
5. **Enum Management:** Centralized enums in `dealbrain_core.enums`.

### Areas for Improvement

1. **Port Field Naming:** Standardize `type`/`port_type`, `count`/`quantity`, `spec_notes`/`version`/`notes`.
2. **ListingComponent.rule_id:** Add to DB model or remove from schema.
3. **Performance Metrics:** Clarify migration path from legacy to new metrics.
4. **Documentation:** This report provides the foundation for developer reference.

---

## Field Count Summary

| Entity | Total Fields | Computed Fields | Relationships | Custom Fields Support |
|--------|--------------|-----------------|---------------|----------------------|
| Listing | 65+ | 2 (ram_type, ram_speed_mhz) | 8 | ✓ |
| CPU | 15 | 0 | 1 | ✓ |
| GPU | 7 | 0 | 1 | ✓ |
| RamSpec | 9 | 0 | 1 | ✓ |
| StorageProfile | 10 | 0 | 2 | ✓ |
| ListingComponent | 8 | 0 | 1 | ✗ |
| PortsProfile | 5 | 0 | 2 | ✓ |
| Port | 6 | 0 | 1 | ✗ |
| ValuationRuleset | 11 | 0 | 2 | ✗ |
| ValuationRuleGroup | 10 | 0 | 2 | ✗ |
| ValuationRuleV2 | 11 | 0 | 4 | ✗ |
| Profile | 7 | 0 | 1 | ✗ |
| CustomFieldDefinition | 16 | 0 | 1 | ✗ |

---

**Last Updated:** 2025-10-11
**Maintainer:** Lead Architect
**Related Documentation:**
- [CLAUDE.md](/mnt/containers/deal-brain/CLAUDE.md)
- [Architecture Decision Records (ADRs)](/mnt/containers/deal-brain/docs/adr/)
