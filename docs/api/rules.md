# Valuation Rules API

The Valuation Rules API provides a comprehensive system for managing pricing adjustments and valuation logic. It enables creation of rule hierarchies (Rulesets > Rule Groups > Rules) with flexible condition-based evaluations and customizable actions for component-based pricing adjustments.

## Overview

The valuation system follows a three-tier hierarchy:

1. **Rulesets** - Collections of rule groups with metadata, priority, and global conditions
2. **Rule Groups** - Organized categories of rules (e.g., "CPU Adjustments", "RAM Penalties")
3. **Rules** - Individual condition-action pairs that evaluate listing attributes and apply adjustments

Rules support:
- **Conditions** - Multi-condition evaluation with logical operators (AND, OR)
- **Actions** - Fixed values, per-unit calculations, formulas, and dynamic modifiers
- **Preview & Validation** - Test rules before applying to listings
- **Audit Logging** - Track all changes for compliance and debugging
- **Package Export/Import** - Share rule configurations across installations

## Quick Start

### Create a Ruleset

```bash
curl -X POST "http://localhost:8000/api/v1/rulesets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Standard Valuation v1",
    "description": "Standard PC component valuation rules",
    "version": "1.0.0",
    "is_active": true,
    "priority": 10
  }'
```

### Create a Rule Group

```bash
curl -X POST "http://localhost:8000/api/v1/rule-groups" \
  -H "Content-Type: application/json" \
  -d '{
    "ruleset_id": 1,
    "name": "CPU Adjustments",
    "category": "processor",
    "description": "Rules for CPU-based price adjustments",
    "display_order": 1,
    "weight": 1.0,
    "is_active": true
  }'
```

### Create a Rule

```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 1,
    "name": "High-End CPU Bonus",
    "description": "Add $50 for CPUs with CPU Mark > 50000",
    "priority": 100,
    "evaluation_order": 100,
    "is_active": true,
    "conditions": [
      {
        "field_name": "cpu.cpu_mark_multi",
        "field_type": "number",
        "operator": "greater_than",
        "value": 50000
      }
    ],
    "actions": [
      {
        "action_type": "fixed_adjustment",
        "metric": null,
        "value_usd": 50.0,
        "unit_type": null,
        "formula": null,
        "modifiers": {}
      }
    ]
  }'
```

## API Endpoints

### Rulesets

#### Create Ruleset

**POST /api/v1/rulesets**

Create a new valuation ruleset as a container for rule groups.

**Request Schema:**
```typescript
interface RulesetCreateRequest {
  name: string;                    // Unique ruleset name (1-128 chars)
  description?: string;            // Optional description
  version?: string;                // Version string (default: "1.0.0")
  is_active?: boolean;             // Whether ruleset is active (default: true)
  priority?: number;               // Execution priority, lower runs first (default: 10)
  metadata?: object;               // Custom metadata (e.g., tags, source)
  conditions?: object;             // Ruleset-level conditions (serialized tree)
}
```

**Response Schema:**
```typescript
interface RulesetResponse {
  id: number;
  name: string;
  description?: string;
  version: string;
  is_active: boolean;
  created_by?: string;
  created_at: string;              // ISO 8601 timestamp
  updated_at: string;              // ISO 8601 timestamp
  metadata: object;
  priority: number;
  conditions: object;
  rule_groups: RuleGroupResponse[];
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/rulesets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium PC Valuation",
    "description": "Valuation rules for premium systems",
    "version": "2.1.0",
    "is_active": true,
    "priority": 5,
    "metadata": {
      "tags": ["premium", "high-end"],
      "source": "internal"
    }
  }'
```

**Example Response (201):**
```json
{
  "id": 5,
  "name": "Premium PC Valuation",
  "description": "Valuation rules for premium systems",
  "version": "2.1.0",
  "is_active": true,
  "created_by": null,
  "created_at": "2024-11-05T10:30:00.000Z",
  "updated_at": "2024-11-05T10:30:00.000Z",
  "metadata": {
    "tags": ["premium", "high-end"],
    "source": "internal"
  },
  "priority": 5,
  "conditions": {},
  "rule_groups": []
}
```

#### List Rulesets

**GET /api/v1/rulesets**

List all rulesets with optional filtering.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_only` | boolean | false | Filter to active rulesets only |
| `skip` | integer | 0 | Number of results to skip |
| `limit` | integer | 100 | Max results (1-500) |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/rulesets?active_only=true&limit=20"
```

**Example Response (200):**
```json
[
  {
    "id": 1,
    "name": "Standard Valuation v1",
    "description": "Standard PC component valuation rules",
    "version": "1.0.0",
    "is_active": true,
    "created_by": null,
    "created_at": "2024-11-01T09:00:00.000Z",
    "updated_at": "2024-11-05T10:30:00.000Z",
    "metadata": {},
    "priority": 10,
    "conditions": {},
    "rule_groups": []
  }
]
```

#### Get Ruleset

**GET /api/v1/rulesets/{ruleset_id}**

Get a ruleset with all nested rule groups and rules.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ruleset_id` | integer | Ruleset ID |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/rulesets/1"
```

**Example Response (200):**
```json
{
  "id": 1,
  "name": "Standard Valuation v1",
  "description": "Standard PC component valuation rules",
  "version": "1.0.0",
  "is_active": true,
  "created_by": null,
  "created_at": "2024-11-01T09:00:00.000Z",
  "updated_at": "2024-11-05T10:30:00.000Z",
  "metadata": {},
  "priority": 10,
  "conditions": {},
  "rule_groups": [
    {
      "id": 1,
      "ruleset_id": 1,
      "name": "CPU Adjustments",
      "category": "processor",
      "description": "Rules for CPU-based adjustments",
      "display_order": 1,
      "weight": 1.0,
      "is_active": true,
      "created_at": "2024-11-01T09:00:00.000Z",
      "updated_at": "2024-11-05T10:30:00.000Z",
      "metadata": {},
      "basic_managed": false,
      "entity_key": null,
      "rules": [
        {
          "id": 10,
          "group_id": 1,
          "name": "CPU Mark Deduction",
          "description": "Deduct $25 for CPUs below 30,000 mark",
          "priority": 100,
          "is_active": true,
          "evaluation_order": 100,
          "version": 1,
          "created_by": null,
          "created_at": "2024-11-01T09:00:00.000Z",
          "updated_at": "2024-11-05T10:30:00.000Z",
          "conditions": [
            {
              "field_name": "cpu.cpu_mark_multi",
              "field_type": "number",
              "operator": "less_than",
              "value": 30000,
              "logical_operator": null,
              "group_order": 0
            }
          ],
          "actions": [
            {
              "action_type": "fixed_adjustment",
              "metric": null,
              "value_usd": 25.0,
              "unit_type": null,
              "formula": null,
              "modifiers": {}
            }
          ],
          "metadata": {}
        }
      ]
    }
  ]
}
```

#### Update Ruleset

**PUT /api/v1/rulesets/{ruleset_id}**

Update a ruleset's properties.

**Request Schema:**
```typescript
interface RulesetUpdateRequest {
  name?: string;
  description?: string;
  version?: string;
  is_active?: boolean;
  priority?: number;
  metadata?: object;
  conditions?: object;
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/api/v1/rulesets/1" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.1.0",
    "is_active": true
  }'
```

**Example Response (200):** Same as Get Ruleset response

#### Delete Ruleset

**DELETE /api/v1/rulesets/{ruleset_id}**

Delete a ruleset (cascades to all groups and rules).

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/rulesets/1"
```

**Example Response (200):**
```json
{
  "message": "Ruleset deleted successfully"
}
```

**Error Responses:**
- `404 Not Found` - Ruleset doesn't exist

### Rule Groups

#### Create Rule Group

**POST /api/v1/rule-groups**

Create a rule group within a ruleset for organizing related rules.

**Request Schema:**
```typescript
interface RuleGroupCreateRequest {
  ruleset_id: number;              // Parent ruleset ID
  name: string;                    // Group name (1-128 chars)
  category: string;                // Category (1-64 chars, e.g., "processor", "memory")
  description?: string;            // Optional description
  display_order?: number;          // Display order (default: 100)
  weight?: number;                 // Weight multiplier 0.0-1.0 (default: 1.0)
  is_active?: boolean;             // Whether group is active (default: true)
  metadata?: object;               // Custom metadata
  basic_managed?: boolean;         // Whether managed by Basic UI mode
  entity_key?: string;             // Entity type if basic-managed (Listing, CPU, GPU, etc.)
}
```

**Validation Rules:**
- If `basic_managed` is true, `entity_key` is required

**Response Schema:**
```typescript
interface RuleGroupResponse {
  id: number;
  ruleset_id: number;
  name: string;
  category: string;
  description?: string;
  display_order: number;
  weight: number;
  is_active: boolean;
  created_at: string;              // ISO 8601 timestamp
  updated_at: string;              // ISO 8601 timestamp
  metadata: object;
  basic_managed?: boolean;
  entity_key?: string;
  rules: RuleResponse[];           // Nested rules
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/rule-groups" \
  -H "Content-Type: application/json" \
  -d '{
    "ruleset_id": 1,
    "name": "RAM Specifications",
    "category": "memory",
    "description": "Valuation adjustments based on RAM capacity and generation",
    "display_order": 2,
    "weight": 1.0,
    "is_active": true,
    "basic_managed": false
  }'
```

**Example Response (201):**
```json
{
  "id": 2,
  "ruleset_id": 1,
  "name": "RAM Specifications",
  "category": "memory",
  "description": "Valuation adjustments based on RAM capacity and generation",
  "display_order": 2,
  "weight": 1.0,
  "is_active": true,
  "created_at": "2024-11-05T10:30:00.000Z",
  "updated_at": "2024-11-05T10:30:00.000Z",
  "metadata": {},
  "basic_managed": false,
  "entity_key": null,
  "rules": []
}
```

#### List Rule Groups

**GET /api/v1/rule-groups**

List rule groups with optional filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ruleset_id` | integer | Filter by ruleset ID |
| `category` | string | Filter by category |
| `skip` | integer | Results to skip (default: 0) |
| `limit` | integer | Max results 1-500 (default: 100) |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/rule-groups?ruleset_id=1&category=processor"
```

#### Get Rule Group

**GET /api/v1/rule-groups/{group_id}**

Get a rule group with all nested rules.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/rule-groups/1"
```

#### Update Rule Group

**PUT /api/v1/rule-groups/{group_id}**

Update a rule group.

**Request Schema:**
```typescript
interface RuleGroupUpdateRequest {
  name?: string;
  category?: string;
  description?: string;
  display_order?: number;
  weight?: number;
  is_active?: boolean;
  metadata?: object;
  basic_managed?: boolean;
  entity_key?: string;
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/api/v1/rule-groups/1" \
  -H "Content-Type: application/json" \
  -d '{
    "weight": 1.5,
    "display_order": 5
  }'
```

### Individual Rules

#### Create Rule

**POST /api/v1/valuation-rules**

Create a new valuation rule with conditions and actions.

**Request Schema:**
```typescript
interface RuleCreateRequest {
  group_id: number;                // Parent group ID
  name: string;                    // Rule name (1-128 chars)
  description?: string;            // Optional description
  priority?: number;               // Priority value (default: 100)
  evaluation_order?: number;       // Execution order (default: 100)
  is_active?: boolean;             // Whether rule is active (default: true)
  conditions?: ConditionSchema[];  // List of conditions (AND by default)
  actions?: ActionSchema[];        // List of actions to apply
  metadata?: object;               // Custom metadata
}

interface ConditionSchema {
  field_name: string;              // Field to evaluate (supports dot notation)
  field_type: string;              // Data type (string, number, boolean, enum)
  operator: string;                // Comparison operator (see operators table)
  value: any;                      // Value to compare
  logical_operator?: string;       // AND/OR for condition grouping
  group_order?: number;            // Order within group (default: 0)
}

interface ActionSchema {
  action_type: string;             // Type: fixed_adjustment, per_unit, formula, etc.
  metric?: string;                 // Metric field (for per_unit actions)
  value_usd?: number;              // Fixed USD value
  unit_type?: string;              // Unit for calculations (per_gb, per_unit, etc.)
  formula?: string;                // Custom formula expression
  modifiers?: object;              // Applied modifiers (min_usd, max_usd, clamp, etc.)
}
```

**Condition Operators:**
| Operator | Type | Description |
|----------|------|-------------|
| `equals` | any | Exact match |
| `not_equals` | any | Not equal |
| `greater_than` | number | Greater than |
| `greater_than_or_equal` | number | Greater than or equal |
| `less_than` | number | Less than |
| `less_than_or_equal` | number | Less than or equal |
| `contains` | string | String contains |
| `not_contains` | string | String does not contain |
| `starts_with` | string | String starts with |
| `ends_with` | string | String ends with |
| `in` | array | Value in list |
| `not_in` | array | Value not in list |
| `is_empty` | any | Field is null/empty |
| `is_not_empty` | any | Field is not null/empty |

**Action Types:**
| Type | Description | Required Fields |
|------|-------------|-----------------|
| `fixed_adjustment` | Fixed USD amount | `value_usd` |
| `per_unit` | Per-unit calculation | `metric`, `value_usd` |
| `formula` | Custom formula expression | `formula` |
| `percentage` | Percentage adjustment | `value_usd` (as percentage) |

**Example Request (Fixed Adjustment):**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 1,
    "name": "High CPU Mark Bonus",
    "description": "Add $75 for CPUs with Mark > 50,000",
    "priority": 100,
    "evaluation_order": 10,
    "is_active": true,
    "conditions": [
      {
        "field_name": "cpu.cpu_mark_multi",
        "field_type": "number",
        "operator": "greater_than",
        "value": 50000
      }
    ],
    "actions": [
      {
        "action_type": "fixed_adjustment",
        "value_usd": 75.0,
        "modifiers": {}
      }
    ]
  }'
```

**Example Request (Per-Unit Calculation):**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 2,
    "name": "RAM Valuation",
    "description": "Value RAM at $5 per GB",
    "priority": 100,
    "is_active": true,
    "conditions": [],
    "actions": [
      {
        "action_type": "per_unit",
        "metric": "ram_gb",
        "value_usd": 5.0,
        "unit_type": "per_gb",
        "modifiers": {
          "min_usd": 10.0
        }
      }
    ]
  }'
```

**Example Request (Formula-Based):**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 1,
    "name": "CPU Mark Dynamic Pricing",
    "description": "Price based on CPU Mark with tiered rates",
    "priority": 100,
    "is_active": true,
    "conditions": [
      {
        "field_name": "cpu",
        "field_type": "reference",
        "operator": "is_not_empty",
        "value": null
      }
    ],
    "actions": [
      {
        "action_type": "formula",
        "formula": "cpu_mark_multi / 1000 * 3.5 if cpu_mark_multi > 40000 else cpu_mark_multi / 1000 * 2.5",
        "modifiers": {
          "min_usd": 50.0,
          "max_usd": 500.0
        }
      }
    ]
  }'
```

**Example Response (201):**
```json
{
  "id": 10,
  "group_id": 1,
  "name": "High CPU Mark Bonus",
  "description": "Add $75 for CPUs with Mark > 50,000",
  "priority": 100,
  "is_active": true,
  "evaluation_order": 10,
  "version": 1,
  "created_by": null,
  "created_at": "2024-11-05T10:30:00.000Z",
  "updated_at": "2024-11-05T10:30:00.000Z",
  "conditions": [
    {
      "field_name": "cpu.cpu_mark_multi",
      "field_type": "number",
      "operator": "greater_than",
      "value": 50000,
      "logical_operator": null,
      "group_order": 0
    }
  ],
  "actions": [
    {
      "action_type": "fixed_adjustment",
      "metric": null,
      "value_usd": 75.0,
      "unit_type": null,
      "formula": null,
      "modifiers": {}
    }
  ],
  "metadata": {}
}
```

#### List Rules

**GET /api/v1/valuation-rules**

List rules with filtering and pagination.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `group_id` | integer | Filter by group ID |
| `active_only` | boolean | Show only active rules (default: false) |
| `skip` | integer | Results to skip (default: 0) |
| `limit` | integer | Max results 1-500 (default: 100) |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/valuation-rules?group_id=1&active_only=true&limit=50"
```

#### Get Rule

**GET /api/v1/valuation-rules/{rule_id}**

Get a single rule with all conditions and actions.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/valuation-rules/10"
```

#### Update Rule

**PUT /api/v1/valuation-rules/{rule_id}**

Update a rule's conditions, actions, or properties.

**Request Schema:**
```typescript
interface RuleUpdateRequest {
  name?: string;
  description?: string;
  priority?: number;
  evaluation_order?: number;
  is_active?: boolean;
  conditions?: ConditionSchema[];
  actions?: ActionSchema[];
  metadata?: object;
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/api/v1/valuation-rules/10" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false,
    "description": "Deprecated in favor of rule 12"
  }'
```

#### Delete Rule

**DELETE /api/v1/valuation-rules/{rule_id}**

Delete a rule.

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/valuation-rules/10"
```

**Example Response (200):**
```json
{
  "message": "Rule deleted successfully"
}
```

## Preview & Validation

### Preview Rule

**POST /api/v1/valuation-rules/preview**

Test a rule before saving to see impact on sample listings.

**Request Schema:**
```typescript
interface RulePreviewRequest {
  conditions: ConditionSchema[];
  actions: ActionSchema[];
  sample_size?: number;            // Sample listings to evaluate (1-50, default: 10)
  category_filter?: object;        // Optional filter (e.g., {"category": "processor"})
}
```

**Response Schema:**
```typescript
interface RulePreviewResponse {
  statistics: {
    total_sample_listings: number;
    matched_count: number;
    avg_adjustment: number;
    min_adjustment: number;
    max_adjustment: number;
  };
  sample_matched_listings: SampleListingResult[];
  sample_non_matched_listings: SampleListingResult[];
}

interface SampleListingResult {
  id: number;
  title: string;
  original_price: number;
  adjustment?: number;             // Only if matched
  adjusted_price?: number;
  price_change_pct?: number;
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "sample_size": 20,
    "conditions": [
      {
        "field_name": "ram_gb",
        "field_type": "number",
        "operator": "greater_than_or_equal",
        "value": 32
      }
    ],
    "actions": [
      {
        "action_type": "fixed_adjustment",
        "value_usd": 100.0,
        "modifiers": {}
      }
    ]
  }'
```

**Example Response (200):**
```json
{
  "statistics": {
    "total_sample_listings": 20,
    "matched_count": 7,
    "avg_adjustment": 100.0,
    "min_adjustment": 100.0,
    "max_adjustment": 100.0
  },
  "sample_matched_listings": [
    {
      "id": 45,
      "title": "Dell OptiPlex 7090 - 32GB RAM",
      "original_price": 450.00,
      "adjustment": 100.0,
      "adjusted_price": 550.00,
      "price_change_pct": 22.22
    }
  ],
  "sample_non_matched_listings": [
    {
      "id": 23,
      "title": "HP ProDesk 600 - 16GB RAM",
      "original_price": 375.00,
      "adjustment": null,
      "adjusted_price": null,
      "price_change_pct": null
    }
  ]
}
```

### Validate Formula

**POST /api/v1/valuation-rules/validate-formula**

Validate formula syntax, check available fields, and provide preview calculation.

**Request Schema:**
```typescript
interface FormulaValidationRequest {
  formula: string;                 // Formula expression to validate
  entity_type?: string;            // Entity context: Listing, CPU, GPU, etc. (default: "Listing")
  sample_context?: object;         // Optional sample data for preview
}
```

**Response Schema:**
```typescript
interface FormulaValidationResponse {
  valid: boolean;
  errors: FormulaValidationError[];
  preview?: number;                // Calculated preview with sample data
  used_fields: string[];          // Fields referenced in formula
  available_fields: string[];     // All available fields for entity
}

interface FormulaValidationError {
  message: string;
  severity: "error" | "warning" | "info";
  position?: number;              // Character position of error
  suggestion?: string;            // Suggested fix
}
```

**Example Formulas:**

```typescript
// Simple per-GB pricing
"ram_gb * 5.0"

// Tiered pricing based on CPU Mark
"cpu_mark_multi / 1000 * 3.5 if cpu_mark_multi > 40000 else cpu_mark_multi / 1000 * 2.5"

// Minimum value enforcement
"max(ram_gb * 5.0, 50)"

// Condition-based adjustment
"ram_gb * 3.0 if ram_type == 'ddr5' else ram_gb * 2.5"

// Complex expression with multiple fields
"(cpu_mark_multi / 1000 * 2.0) + (ram_gb * 5.0) + (primary_storage_gb / 500)"
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules/validate-formula" \
  -H "Content-Type: application/json" \
  -d '{
    "formula": "ram_gb * 5.0 if ram_type == \"ddr5\" else ram_gb * 3.0",
    "entity_type": "Listing",
    "sample_context": {
      "ram_gb": 32,
      "ram_type": "ddr5"
    }
  }'
```

**Example Response (200):**
```json
{
  "valid": true,
  "errors": [],
  "preview": 160.0,
  "used_fields": ["ram_gb", "ram_type"],
  "available_fields": [
    "price_usd",
    "condition",
    "status",
    "ram_gb",
    "ram_type",
    "primary_storage_gb",
    "cpu_mark_multi",
    "cpu_mark_single",
    "gpu_mark",
    "manufacturer",
    "series",
    "model_number",
    "form_factor"
  ]
}
```

## Evaluation & Application

### Evaluate Listing

**POST /api/v1/valuation-rules/evaluate/{listing_id}**

Evaluate a single listing against a ruleset to see which rules match and what adjustments are applied.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ruleset_id` | integer | Ruleset to evaluate (uses active ruleset if not provided) |

**Response Schema:**
```typescript
interface RuleEvaluationResponse {
  listing_id: number;
  original_price: number;
  total_adjustment: number;
  adjusted_price: number;
  ruleset_id: number;
  ruleset_name: string;
  matched_rules_count: number;
  matched_rules: Array<{
    rule_id: number;
    rule_name: string;
    group_name: string;
    adjustment: number;
    action_type: string;
  }>;
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules/evaluate/123?ruleset_id=1"
```

**Example Response (200):**
```json
{
  "listing_id": 123,
  "original_price": 450.00,
  "total_adjustment": 125.00,
  "adjusted_price": 575.00,
  "ruleset_id": 1,
  "ruleset_name": "Standard Valuation v1",
  "matched_rules_count": 2,
  "matched_rules": [
    {
      "rule_id": 10,
      "rule_name": "High CPU Mark Bonus",
      "group_name": "CPU Adjustments",
      "adjustment": 75.0,
      "action_type": "fixed_adjustment"
    },
    {
      "rule_id": 15,
      "rule_name": "High RAM Bonus",
      "group_name": "RAM Adjustments",
      "adjustment": 50.0,
      "action_type": "fixed_adjustment"
    }
  ]
}
```

### Apply Ruleset

**POST /api/v1/valuation-rules/apply**

Apply a ruleset to listings (specific or all active listings).

**Request Schema:**
```typescript
interface ApplyRulesetRequest {
  ruleset_id?: number;             // Ruleset to apply (uses active if not provided)
  listing_ids?: number[];          // Specific listings (if empty, applies to all active)
}
```

**Response:**
```typescript
interface ApplyRulesetResponse {
  results: Array<{
    listing_id: number;
    original_price: number;
    adjusted_price: number;
    total_adjustment: number;
    error?: string;                // If rule application failed
  }>;
}
```

**Example Request (Apply to Specific Listings):**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "ruleset_id": 1,
    "listing_ids": [123, 124, 125]
  }'
```

**Example Request (Apply to All Active Listings):**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "ruleset_id": 1
  }'
```

## Package Management

### Export Ruleset Package

**POST /api/v1/rulesets/{ruleset_id}/package**

Export a ruleset as a `.dbrs` (Deal Brain Ruleset) package file for sharing and distribution.

**Request Schema:**
```typescript
interface PackageMetadataRequest {
  name: string;                    // Package name
  version: string;                 // Semantic version (e.g., "1.0.0")
  author?: string;                 // Package author
  description?: string;            // Package description
  min_app_version?: string;        // Minimum app version required
  required_custom_fields?: string[];  // Custom field dependencies
  tags?: string[];                 // Tags (e.g., ["premium", "budget"])
  include_examples?: boolean;      // Include example listings (default: false)
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/rulesets/1/package" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Standard Valuation Rules",
    "version": "1.0.0",
    "author": "Deal Brain Team",
    "description": "Standard valuation rules for PC component pricing",
    "tags": ["standard", "recommended"],
    "include_examples": false
  }'
```

**Response:** `.dbrs` package file (JSON format, can be downloaded)

### Preview Package Export

**POST /api/v1/rulesets/{ruleset_id}/package/preview**

Preview what will be included in a package export without creating the file.

**Request Schema:** Same as Export Ruleset Package

**Response Schema:**
```typescript
interface PackageExportResponse {
  package_name: string;
  package_version: string;
  rulesets_count: number;
  rule_groups_count: number;
  rules_count: number;
  custom_fields_count: number;
  dependencies: object;
  estimated_size_kb: number;
  readme: string;
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/rulesets/1/package/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Standard Valuation Rules",
    "version": "1.0.0"
  }'
```

**Example Response (200):**
```json
{
  "package_name": "Standard Valuation Rules",
  "package_version": "1.0.0",
  "rulesets_count": 1,
  "rule_groups_count": 5,
  "rules_count": 23,
  "custom_fields_count": 0,
  "dependencies": {
    "min_app_version": "0.1.0"
  },
  "estimated_size_kb": 125.3,
  "readme": "# Standard Valuation Rules\n\nThis package contains standard valuation rules..."
}
```

### Install Ruleset Package

**POST /api/v1/rulesets/install**

Install a `.dbrs` package file.

**Request:** Multipart form-data with file upload

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `actor` | string | "system" | User installing the package |
| `merge_strategy` | string | "replace" | Conflict resolution: "replace", "skip", "merge" |

**Response Schema:**
```typescript
interface PackageInstallResponse {
  success: boolean;
  message: string;
  rulesets_created: number;
  rulesets_updated: number;
  rule_groups_created: number;
  rules_created: number;
  warnings: string[];
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/rulesets/install" \
  -F "file=@standard_rules_v1.0.0.dbrs" \
  -H "merge_strategy=replace"
```

## Audit & History

### Get Audit Log

**GET /api/v1/valuation-rules/audit-log**

Retrieve audit log entries tracking changes to rules.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `rule_id` | integer | Filter by rule ID |
| `limit` | integer | Max results 1-500 (default: 100) |

**Response Schema:**
```typescript
interface AuditLogResponse {
  id: number;
  rule_id?: number;
  action: string;                  // "created", "updated", "deleted"
  actor?: string;                  // User who made change
  changes?: object;                // JSON diff of changes
  impact_summary?: object;         // Summary of impact
  created_at: string;              // ISO 8601 timestamp
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/valuation-rules/audit-log?rule_id=10&limit=50"
```

**Example Response (200):**
```json
[
  {
    "id": 1,
    "rule_id": 10,
    "action": "created",
    "actor": null,
    "changes": {
      "name": "High CPU Mark Bonus",
      "value_usd": 75.0
    },
    "impact_summary": {
      "estimated_listings_affected": 23,
      "estimated_avg_adjustment": 75.0
    },
    "created_at": "2024-11-05T10:30:00.000Z"
  },
  {
    "id": 2,
    "rule_id": 10,
    "action": "updated",
    "actor": null,
    "changes": {
      "is_active": false
    },
    "impact_summary": {
      "estimated_listings_affected": 23
    },
    "created_at": "2024-11-05T10:35:00.000Z"
  }
]
```

## Error Handling

### HTTP Status Codes

| Code | Meaning | When Returned |
|------|---------|---------------|
| 200 | OK | Success (GET, PUT, DELETE) |
| 201 | Created | Resource successfully created (POST) |
| 400 | Bad Request | Validation error, invalid input, logic constraint violated |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource, constraint violation |
| 422 | Unprocessable Entity | Schema validation error |
| 500 | Server Error | Internal error |

### Error Response Format

All errors follow a consistent format:

```json
{
  "detail": "Validation error: metric is required when action_type is 'per_unit'"
}
```

### Common Error Scenarios

**Rule Group Not Found**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 999,
    "name": "Test Rule"
  }'

# Response (404):
{
  "detail": "Rule group not found"
}
```

**Validation Error - Missing Required Field**
```bash
curl -X POST "http://localhost:8000/api/v1/valuation-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 1,
    "actions": [
      {
        "action_type": "per_unit",
        "value_usd": 5.0
        // metric is missing!
      }
    ]
  }'

# Response (400):
{
  "detail": "metric is required when action_type is 'per_unit'"
}
```

**Duplicate Ruleset Name**
```bash
curl -X POST "http://localhost:8000/api/v1/rulesets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Standard Valuation v1"  // Already exists
  }'

# Response (409):
{
  "detail": "A ruleset with this name already exists"
}
```

## TypeScript Client Example

```typescript
import fetch from 'node-fetch';

const API_URL = 'http://localhost:8000/api/v1';

interface CreateRulesetPayload {
  name: string;
  description?: string;
  version?: string;
  is_active?: boolean;
  priority?: number;
}

async function createRuleset(payload: CreateRulesetPayload) {
  const response = await fetch(`${API_URL}/rulesets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to create ruleset: ${error.detail}`);
  }

  return response.json();
}

async function previewRule(conditions, actions, sampleSize = 10) {
  const response = await fetch(`${API_URL}/valuation-rules/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      conditions,
      actions,
      sample_size: sampleSize,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to preview rule: ${error.detail}`);
  }

  return response.json();
}

async function evaluateListing(listingId, rulesetId) {
  const url = new URL(`${API_URL}/valuation-rules/evaluate/${listingId}`);
  if (rulesetId) {
    url.searchParams.append('ruleset_id', String(rulesetId));
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to evaluate listing: ${error.detail}`);
  }

  return response.json();
}

// Usage
(async () => {
  try {
    // Create a ruleset
    const ruleset = await createRuleset({
      name: 'My Valuation Rules',
      description: 'Custom valuation logic',
      version: '1.0.0',
    });
    console.log('Created ruleset:', ruleset.id);

    // Preview a rule
    const preview = await previewRule(
      [
        {
          field_name: 'ram_gb',
          field_type: 'number',
          operator: 'greater_than_or_equal',
          value: 32,
        },
      ],
      [
        {
          action_type: 'fixed_adjustment',
          value_usd: 100.0,
          modifiers: {},
        },
      ],
      20
    );
    console.log('Preview results:', preview.statistics);

    // Evaluate a listing
    const evaluation = await evaluateListing(123, ruleset.id);
    console.log('Evaluation:', evaluation);
  } catch (error) {
    console.error('Error:', error);
  }
})();
```

## Best Practices

### Rule Design

1. **Use Clear Names** - Give rules descriptive names that explain the adjustment
2. **Document Intent** - Use descriptions to explain why the rule exists
3. **Test Before Applying** - Always use `/preview` endpoint to verify impact
4. **Validate Formulas** - Use `/validate-formula` for complex expressions
5. **Organize with Groups** - Use rule groups to organize by component type

### Condition Handling

1. **Explicit Empty Checks** - Use `is_empty` / `is_not_empty` for reference fields
2. **Order Matters** - Use `group_order` for complex AND/OR logic
3. **Test with Sample Data** - Verify conditions match intended listings
4. **Use Dot Notation** - Access nested fields like `cpu.cpu_mark_multi`

### Action Configuration

1. **Start Simple** - Begin with fixed adjustments, graduate to formulas
2. **Set Bounds** - Use `min_usd` and `max_usd` modifiers to prevent extremes
3. **Document Formulas** - Add formula explanation in modifiers or description
4. **Version Updates** - Increment ruleset version when making changes

### Performance

1. **Limit Conditions** - Rules with many conditions are slower to evaluate
2. **Use Indexes** - Conditions on indexed fields (price_usd, cpu_mark_multi) perform better
3. **Batch Operations** - Apply to multiple listings in one `/apply` call
4. **Monitor Changes** - Check audit log to understand impact of rule changes

## Further Reading

- **Component Catalog**: `/docs/api/catalog.md` - CPU, GPU, RAM, Storage APIs
- **Listings API**: `/docs/api/listings.md` - Creating and managing listings
- **Import Workflow**: `/docs/guides/import-workflow.md` - Importing PC data
- **Formula Reference**: `/docs/guides/formula-reference.md` - Complete formula documentation
