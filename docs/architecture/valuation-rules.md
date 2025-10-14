# Valuation Rules System Architecture

## Overview

The Valuation Rules system is a dynamic, hierarchical pricing adjustment engine that allows users to configure flexible pricing strategies based on listing attributes. The system evaluates listings against user-defined rules and calculates adjusted prices with full traceability and explainability.

**Key Capabilities:**
- Hierarchical rule organization (Ruleset → Rule Groups → Rules)
- Condition-based rule matching with AND/OR logic
- Multiple action types (fixed value, per-unit, formula-based)
- Rule priority and evaluation order control
- Real-time preview of rule impact on listings
- Ruleset-level conditions for automatic selection
- Basic and Advanced UI modes
- Full audit trail and versioning

## System Architecture

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────────────┐      ┌──────────────────────────┐ │
│  │  /valuation-rules    │      │  Listing Components      │ │
│  │  - Basic Mode Tab    │      │  - ValuationCell         │ │
│  │  - Advanced Mode Tab │      │  - Breakdown Modal       │ │
│  │  - Rule Builder UI   │      │  - Threshold Display     │ │
│  └──────────────────────┘      └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
                    REST API (FastAPI)
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                       Backend Services                       │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │  RulesService      │  │ RuleEvaluationSvc  │            │
│  │  - CRUD operations │  │ - Rule evaluation  │            │
│  │  - Validation      │  │ - Context building │            │
│  └────────────────────┘  └────────────────────┘            │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ RulePreviewService │  │ PackagingService   │            │
│  │ - Preview listings │  │ - Import/Export    │            │
│  └────────────────────┘  └────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                    Core Domain Logic                         │
│  (packages/core/dealbrain_core/rules/)                      │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ RuleEvaluator  │  │ ConditionGroup │  │ ActionEngine │ │
│  │ - Orchestrate  │  │ - AND/OR logic │  │ - Fixed val  │ │
│  │ - Match rules  │  │ - Operators    │  │ - Per-unit   │ │
│  │ - Apply actions│  │ - Nested groups│  │ - Formula    │ │
│  └────────────────┘  └────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                          │
│  PostgreSQL with SQLAlchemy Models                           │
│  - ValuationRuleset                                          │
│  - ValuationRuleGroup                                        │
│  - ValuationRuleV2                                           │
│  - ValuationRuleCondition (nested)                           │
│  - ValuationRuleAction                                       │
│  - ValuationRuleVersion (audit)                              │
│  - ValuationRuleAudit (history)                              │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Hierarchy Model

The database uses a 4-level hierarchy:

```
ValuationRuleset (1:N)
  ├─ priority: int (evaluation order)
  ├─ is_active: bool (enabled/disabled)
  ├─ conditions_json: dict (optional ruleset-level conditions)
  └─ ValuationRuleGroup[] (1:N)
      ├─ category: str (cpu, ram, storage, etc.)
      ├─ display_order: int (UI ordering)
      ├─ weight: float (future scoring weight)
      └─ ValuationRuleV2[] (1:N)
          ├─ evaluation_order: int (execution sequence)
          ├─ priority: int (deprecated, use evaluation_order)
          ├─ is_active: bool (rule on/off)
          ├─ ValuationRuleCondition[] (1:N)
          │   ├─ field_name: str (e.g., "condition", "cpu.cores")
          │   ├─ operator: str (equals, gt, lt, in, contains, etc.)
          │   ├─ value_json: any (comparison value)
          │   ├─ logical_operator: str (AND/OR)
          │   └─ parent_condition_id: int (for nested groups)
          └─ ValuationRuleAction[] (1:N)
              ├─ action_type: str (fixed_value, per_unit, formula)
              ├─ metric: str (per_gb, primary_storage_gb, etc.)
              ├─ value_usd: float (adjustment amount)
              └─ modifiers_json: dict (additional parameters)
```

**Key Design Decisions:**

1. **Nested Conditions**: `ValuationRuleCondition` supports hierarchical condition groups via `parent_condition_id`, enabling complex AND/OR logic trees.

2. **Ruleset Conditions**: `ValuationRuleset.conditions_json` allows automatic ruleset selection based on listing context (e.g., "Apply this ruleset only to listings with Intel CPUs").

3. **Soft Deletes**: Rules maintain referential integrity. Versioning captures historical states.

4. **Action Flexibility**: `modifiers_json` provides extensibility for future action types without schema changes.

## Core Domain Logic

### Rule Evaluation Flow

Located in `packages/core/dealbrain_core/rules/`:

```
1. RuleEvaluator.evaluate_ruleset(rules, context)
   ├─ Sort rules by evaluation_order
   └─ For each rule:
       ├─ Check is_active flag
       ├─ Build Condition objects from conditions list
       ├─ Evaluate conditions against context
       │   └─ ConditionGroup handles AND/OR logic
       ├─ If matched:
       │   └─ ActionEngine.execute_actions()
       │       ├─ fixed_value: return value_usd
       │       ├─ per_unit: value_usd * context[metric]
       │       └─ formula: FormulaEngine.evaluate()
       └─ Return RuleEvaluationResult
```

**Context Building** (`build_context_from_listing`):
- Flattens listing, CPU, GPU, RAM, storage data into single dict
- Supports nested field access (e.g., `cpu.cores`, `ram_spec.speed_mhz`)
- Includes custom fields from `attributes_json`
- Used for both condition evaluation and action calculation

### Condition System

**Supported Operators:**
- `equals`, `not_equals`: Exact match
- `gt`, `gte`, `lt`, `lte`: Numeric/date comparisons
- `in`, `not_in`: List membership
- `contains`, `not_contains`: String/array containment
- `is_null`, `is_not_null`: Null checks
- `regex_match`: Pattern matching

**Logical Operators:**
- `AND`: All conditions must be true
- `OR`: At least one condition must be true

**Nested Groups:**
```json
{
  "logical_operator": "AND",
  "conditions": [
    {"field_name": "condition", "operator": "equals", "value": "used"},
    {
      "logical_operator": "OR",
      "conditions": [
        {"field_name": "cpu.cores", "operator": "gte", "value": 8},
        {"field_name": "ram_gb", "operator": "gte", "value": 32}
      ]
    }
  ]
}
```
This matches listings that are "used" AND have either 8+ cores OR 32+ GB RAM.

### Action System

**Action Types:**

1. **fixed_value**: Applies a constant adjustment
   ```json
   {
     "action_type": "fixed_value",
     "value_usd": -50.0
   }
   ```

2. **per_unit**: Multiplies by a metric from context
   ```json
   {
     "action_type": "per_unit",
     "metric": "ram_gb",
     "value_usd": -2.5
   }
   ```
   If `context["ram_gb"] = 16`, adjustment = -2.5 × 16 = -40

3. **formula**: Custom expressions using FormulaEngine
   ```json
   {
     "action_type": "formula",
     "formula": "price_usd * 0.15 - (ram_gb * 2)"
   }
   ```

**Modifiers** (future extensibility):
- Can contain flags like `cap_at_zero`, `round_to_nearest`, etc.

## Backend Services

### RulesService

**Responsibilities:**
- CRUD operations for rulesets, groups, and rules
- Validation of rule structures
- Cascade operations (delete group → delete rules)
- Transaction management

**Key Methods:**
- `create_ruleset()`, `update_ruleset()`, `delete_ruleset()`
- `create_rule_group()`, `update_rule_group()`
- `create_rule()`, `update_rule()`, `duplicate_rule()`
- `get_ruleset()` - fetches full hierarchy with eager loading

### RuleEvaluationService

**Responsibilities:**
- Evaluate listings against rulesets
- Apply valuation results to listings
- Batch processing for multiple listings
- Ruleset matching based on context

**Key Methods:**
- `evaluate_listing(listing_id, ruleset_id?)` - evaluates and returns results
- `apply_ruleset_to_listing()` - evaluates and persists to `adjusted_price_usd`
- `apply_ruleset_to_all_listings()` - batch processing with commit batching
- `_match_ruleset_for_context()` - auto-selects ruleset based on conditions

**Ruleset Selection Logic:**
1. If listing has `ruleset_id` set and that ruleset is active, use it
2. Else, find highest-priority active ruleset whose `conditions_json` matches context
3. Else, use default active ruleset (lowest priority value)

### RulePreviewService

**Responsibilities:**
- Preview rule impact on sample listings
- Statistical analysis of rule matches
- Sample matched/non-matched listings

**Response Structure:**
```json
{
  "statistics": {
    "total_listings_checked": 150,
    "matched_count": 42,
    "match_percentage": 28.0,
    "avg_adjustment": -35.50,
    "min_adjustment": -150.0,
    "max_adjustment": 0.0
  },
  "sample_matched_listings": [...],
  "sample_non_matched_listings": [...]
}
```

### RulesetPackagingService

**Responsibilities:**
- Export rulesets as JSON packages
- Import ruleset packages with conflict resolution
- Metadata management (author, version, tags)

**Package Format:**
```json
{
  "metadata": {
    "name": "Standard Valuation v2",
    "version": "2.1.0",
    "author": "Admin",
    "exported_at": "2025-10-12T10:30:00Z"
  },
  "ruleset": {
    "name": "...",
    "rule_groups": [...]
  }
}
```

## Frontend Architecture

### Page Structure: /valuation-rules

**Component Hierarchy:**
```
ValuationRulesPage
├─ Mode Toggle (Basic/Advanced)
├─ Ruleset Selector (dropdown)
├─ Ruleset Stats Card
├─ RulesetSettingsCard (priority, conditions)
└─ [Mode-specific content]
    ├─ BasicValuationForm (Basic mode)
    │   ├─ Baseline adjustments (base, RAM, storage)
    │   └─ Condition adjustments (new, refurb, used, for_parts)
    └─ Advanced mode
        ├─ Search bar
        ├─ Add Group button
        └─ RulesetCard[] (one per group)
            ├─ Group header (name, category, stats)
            ├─ Add Rule button
            └─ Rule rows (expandable)
                ├─ Rule header (name, status, priority)
                ├─ Actions (Edit, Toggle, Duplicate, Delete)
                └─ Expanded details (conditions, actions)
```

**State Management:**
- React Query for server state (queries, mutations)
- Local state for UI interactions (expanded rows, modals)
- localStorage for mode preference persistence

### Basic Mode

**Purpose:** Simplified interface for common adjustments without rule concepts.

**Managed Rules:**
- Creates/updates rules in a special "Basic · Adjustments" group
- Rules are tagged with `metadata.basic_managed: true`
- Maps UI fields to rule definitions:
  - Base adjustment → fixed_value action with no conditions
  - RAM per GB → per_unit action with metric="per_gb"
  - Storage per 100GB → per_unit action with metric="primary_storage_gb" (scaled)
  - Condition adjustments → fixed_value actions with condition equality checks

**Sync Logic:**
- Derives config from existing rules on load
- On save, creates/updates/deactivates managed rules
- Users can switch to Advanced to see generated rules

### Advanced Mode

**Features:**
- Full rule hierarchy visualization
- Inline rule creation/editing via modals
- Drag-to-reorder (future enhancement)
- Real-time search/filtering
- Rule duplication
- Rule enable/disable toggles

**Modals:**
- `RuleBuilderModal`: Create/edit rules with condition and action builders
- `RuleGroupFormModal`: Create/edit rule groups
- `RulesetBuilderModal`: Create new rulesets
- `RulePreviewPanel`: Preview rule impact on listings (future)

**Components:**
- `RulesetCard`: Collapsible card for each group with rule list
- `ConditionGroup`: Recursive condition builder with AND/OR logic
- `EntityFieldSelector`: Field picker with type awareness
- `ActionBuilder`: Action configuration with type-specific inputs
- `ValueInput`: Type-safe value input (string, number, enum, etc.)

## Listing Integration

### Valuation Display

**Components:**
- `ValuationCell`: Color-coded adjusted price with delta badge
- `ValuationBreakdownModal`: Detailed breakdown of applied rules and adjustments

**Breakdown Structure:**
```json
{
  "listing_id": 123,
  "base_price_usd": 500.0,
  "adjusted_price_usd": 425.0,
  "total_adjustment": -75.0,
  "matched_rules_count": 3,
  "ruleset_name": "Standard Valuation",
  "adjustments": [
    {
      "rule_id": 45,
      "rule_name": "RAM Deduction",
      "adjustment_amount": -32.0,
      "actions": [
        {
          "action_type": "per_unit",
          "metric": "per_gb",
          "value": -32.0
        }
      ]
    },
    ...
  ]
}
```

**Color Coding:**
- Thresholds stored in `ApplicationSettings` with key `valuation_thresholds`
- Green: Good deal (adjusted < list by threshold %)
- Yellow: Great deal (adjusted < list by higher threshold %)
- Red: Premium (adjusted > list)
- Blue: Fair (within threshold range)

**Automatic Recalculation:**
- Triggered on listing save (price change, component change)
- Can be manually triggered via "Apply Ruleset" action
- Background jobs can batch-process all listings

## Baseline Rule Hydration

### Overview

**Purpose:** Convert placeholder baseline rules into fully expanded rule structures for Advanced Mode editing.

Baseline rules created in Basic Mode are stored as **placeholders** with minimal structure:
- Empty conditions arrays
- Actions with `value_usd: 0.0`
- Configuration stored in `metadata_json` (valuation buckets, formulas, etc.)

To enable full editing in Advanced Mode, these placeholders must be **hydrated** — expanded into complete rules with explicit conditions and actions.

### BaselineHydrationService

**Location:** `apps/api/dealbrain_api/services/baseline_hydration.py`

**Responsibilities:**
- Detect placeholder baseline rules via metadata flags
- Expand placeholders into executable rule structures
- Maintain metadata linking between original and expanded rules
- Ensure idempotent hydration (prevent duplicate expansions)
- Preserve valuation calculations (hydration is value-neutral)

**Key Methods:**

```python
class BaselineHydrationService:
    async def hydrate_baseline_rules(
        self,
        session: AsyncSession,
        ruleset_id: int,
        actor: str = "system"
    ) -> HydrationResult:
        """
        Hydrate all placeholder baseline rules in a ruleset.

        Returns:
            HydrationResult with status, counts, and summary
        """

    async def hydrate_single_rule(
        self,
        session: AsyncSession,
        rule_id: int,
        actor: str = "system"
    ) -> list[ValuationRuleV2]:
        """
        Hydrate a single placeholder rule.

        May return multiple rules (enum expansion).
        """
```

**HydrationResult Structure:**

```python
@dataclass
class HydrationResult:
    status: str  # "success" or "error"
    ruleset_id: int
    hydrated_rule_count: int  # Number of placeholders processed
    created_rule_count: int   # Total new rules created
    hydration_summary: list[dict[str, Any]]  # Per-rule expansion details
```

### Hydration Strategies

The service uses different strategies based on field type:

#### Strategy 1: Enum Multiplier Fields

**Field Types:** DDR Generation, Condition, Release Year, etc.

**Input (Placeholder):**
```json
{
  "id": 101,
  "name": "DDR Generation",
  "conditions": [],
  "actions": [{
    "action_type": "multiplier",
    "value_usd": 0.0
  }],
  "metadata_json": {
    "baseline_placeholder": true,
    "field_type": "enum_multiplier",
    "valuation_buckets": {
      "ddr3": 0.7,
      "ddr4": 1.0,
      "ddr5": 1.3
    },
    "field_id": "ram_spec.ddr_generation"
  }
}
```

**Output (Expanded):**
Creates **one rule per enum value**:

```json
[
  {
    "id": 102,
    "name": "DDR Generation: DDR3",
    "conditions": [{
      "field": "ram_spec.ddr_generation",
      "operator": "equals",
      "value": "ddr3"
    }],
    "actions": [{
      "action_type": "multiplier",
      "value_usd": 70.0,  // 0.7 * 100
      "modifiers": {"original_multiplier": 0.7}
    }],
    "metadata_json": {
      "hydration_source_rule_id": 101,
      "enum_value": "ddr3",
      "field_type": "enum_multiplier"
    }
  },
  // Similar rules for ddr4, ddr5...
]
```

**Key Points:**
- Multipliers converted to percentages (×100 for storage)
- Each rule independently editable
- Original multiplier preserved in action modifiers
- Field path copied from metadata to condition

#### Strategy 2: Formula Fields

**Field Types:** RAM Capacity calculation, composite formulas

**Input (Placeholder):**
```json
{
  "id": 201,
  "name": "Total RAM Capacity",
  "conditions": [],
  "actions": [{"action_type": "multiplier", "value_usd": 0.0}],
  "metadata_json": {
    "baseline_placeholder": true,
    "field_type": "formula",
    "formula_text": "ram_capacity_gb * base_price_per_gb"
  }
}
```

**Output (Expanded):**
Creates **single rule with formula action**:

```json
{
  "id": 202,
  "name": "Total RAM Capacity",
  "conditions": [],  // Always applies
  "actions": [{
    "action_type": "formula",
    "formula": "ram_capacity_gb * base_price_per_gb",
    "value_usd": null
  }],
  "metadata_json": {
    "hydration_source_rule_id": 201,
    "field_type": "formula"
  }
}
```

**Key Points:**
- Formula text copied verbatim
- No conditions (always applies to all listings)
- Formula editable in Advanced Mode formula builder

#### Strategy 3: Fixed Value Fields

**Field Types:** Base depreciation, flat adjustments

**Input (Placeholder):**
```json
{
  "id": 301,
  "name": "Base Depreciation",
  "conditions": [],
  "actions": [{"action_type": "fixed_value", "value_usd": 0.0}],
  "metadata_json": {
    "baseline_placeholder": true,
    "field_type": "fixed",
    "default_value": -50.0
  }
}
```

**Output (Expanded):**
Creates **single rule with fixed value**:

```json
{
  "id": 302,
  "name": "Base Depreciation",
  "conditions": [],
  "actions": [{
    "action_type": "fixed_value",
    "value_usd": -50.0,
    "modifiers": {}
  }],
  "metadata_json": {
    "hydration_source_rule_id": 301,
    "field_type": "fixed"
  }
}
```

**Key Points:**
- Value extracted from metadata `default_value`
- No conditions (always applies)
- Directly editable value in Advanced Mode

### Metadata Structure and Tracking

**Placeholder Rule Metadata (Before Hydration):**

```json
{
  "baseline_placeholder": true,
  "field_type": "enum_multiplier" | "formula" | "fixed",
  "field_id": "ram_spec.ddr_generation",
  "valuation_buckets": {...},  // For enum types
  "formula_text": "...",       // For formula types
  "default_value": -50.0,      // For fixed types
  "proper_name": "DDR Generation",
  "description": "...",
  "explanation": "..."
}
```

**Placeholder Rule Metadata (After Hydration):**

```json
{
  "baseline_placeholder": true,
  "hydrated": true,
  "hydrated_at": "2025-10-14T10:00:00Z",
  "hydrated_by": "user@example.com",
  // Original metadata preserved for audit
  "field_type": "enum_multiplier",
  "valuation_buckets": {...}
}
```

**Expanded Rule Metadata:**

```json
{
  "hydration_source_rule_id": 101,
  "enum_value": "ddr3",  // For enum expansions
  "field_type": "enum_multiplier"
}
```

**Key Metadata Fields:**
- `baseline_placeholder`: Identifies original baseline rules
- `hydrated`: Marks placeholder as already processed (prevents re-hydration)
- `hydrated_at` / `hydrated_by`: Audit trail
- `hydration_source_rule_id`: Links expanded rules back to source
- `is_foreign_key_rule`: Marks system-managed rules (hidden in Advanced UI)

### Hydration Process Flow

**Trigger:** User clicks "Prepare Baseline Rules for Editing" in Advanced Mode

```
1. Frontend Detection
   └─ Check rules for baseline_placeholder: true && hydrated: false
   └─ Show hydration banner if placeholders detected

2. User Action
   └─ Click "Prepare Baseline Rules for Editing" button
   └─ POST /api/v1/baseline/rulesets/{ruleset_id}/hydrate
       └─ Request: { actor: "user@example.com" }

3. Backend Processing (BaselineHydrationService)
   ├─ Query all placeholder rules in ruleset
   ├─ For each placeholder:
   │   ├─ Skip if already hydrated
   │   ├─ Determine field_type from metadata
   │   ├─ Route to appropriate strategy:
   │   │   ├─ Enum → _hydrate_enum_multiplier()
   │   │   ├─ Formula → _hydrate_formula()
   │   │   └─ Fixed → _hydrate_fixed()
   │   ├─ Create expanded rules via RulesService
   │   ├─ Mark original as hydrated (is_active=false)
   │   └─ Update metadata with hydration timestamps
   └─ Commit transaction

4. Response to Frontend
   └─ Return HydrationResult:
       {
         "status": "success",
         "ruleset_id": 1,
         "hydrated_rule_count": 12,
         "created_rule_count": 18,
         "hydration_summary": [...]
       }

5. Frontend Updates
   ├─ Display success toast with counts
   ├─ Hide hydration banner
   ├─ Invalidate rules query (React Query)
   └─ Re-render Advanced Mode with expanded rules
```

### Idempotency and Safety

**Idempotent Hydration:**
- Service checks `hydrated: true` flag before processing
- Prevents duplicate rule creation on multiple hydration attempts
- Returns appropriate message if already hydrated

**Transaction Safety:**
- All hydration operations wrapped in database transaction
- Rollback on error (no partial hydration)
- Original placeholders never deleted (only deactivated)

**Valuation Preservation:**
- Hydration is designed to be value-neutral
- Adjusted prices remain identical before and after
- Multiplier conversions preserve original values (0.7 → 70.0%)
- Conditions and actions match original logic exactly

**Audit Trail:**
- `hydrated_at` and `hydrated_by` recorded
- Original placeholder metadata preserved
- `ValuationRuleVersion` snapshot created
- `ValuationRuleAudit` entry logged

### Foreign Key Rule Handling

**Problem:** RAM Spec and GPU rules reference foreign entities and cannot be directly edited.

**Solution:**
- Mark foreign key rules with `is_foreign_key_rule: true` in metadata
- Filter these rules out of Advanced Mode UI by default
- Exclude from hydration process
- Optional "Show System Rules" toggle for visibility (view-only)

**Example:**
```json
{
  "id": 401,
  "name": "RAM Spec: 16GB DDR4",
  "metadata_json": {
    "is_foreign_key_rule": true,
    "ram_spec_id": 15
  }
}
```

### Performance Considerations

**Rule Proliferation:**
- Enum fields can create multiple rules (3-5 typically)
- Example: DDR Generation (3 rules) + Condition (4 rules) + Release Year (5 rules) = 12 rules from 3 placeholders
- Mitigated by:
  - Visual grouping in UI
  - Collapse/expand functionality
  - Search and filtering

**Database Impact:**
- Additional rule records created
- Original placeholders retained (marked inactive)
- Typical ruleset: +50-100 rules after hydration
- Performance impact negligible (rules loaded once, cached)

**Hydration Speed:**
- Small ruleset (10 rules): <1 second
- Medium ruleset (50 rules): <3 seconds
- Large ruleset (100+ rules): <5 seconds
- Batch rule creation optimized within single transaction

### Error Handling

**Common Errors:**
- Invalid metadata structure → Skip rule with warning
- Missing valuation_buckets → Log error, skip rule
- Database constraint violation → Rollback transaction
- Network timeout → Return error, allow retry

**Error Response:**
```json
{
  "status": "error",
  "error_message": "Failed to hydrate rule 101: Invalid metadata",
  "ruleset_id": 1,
  "hydrated_rule_count": 0,
  "created_rule_count": 0
}
```

**Frontend Error Handling:**
- Display error toast with user-friendly message
- Keep hydration banner visible (allow retry)
- Log detailed error for debugging

### Future Enhancements

**Phase 5: Dehydration** (Planned)
- Reverse hydration process
- Reactivate placeholder rules
- Delete expanded rules
- Restore Basic Mode editability

**Re-hydration:**
- Update expanded rules when enum values change
- Smart diff to preserve manual edits
- Merge new values with existing rules

**Selective Hydration:**
- Hydrate specific rules instead of entire ruleset
- Useful for large rulesets with mixed editing needs

## Data Flow Diagrams

### Baseline Rule Hydration Flow

```
┌─────────────────────────────────────────────────────────────┐
│ User switches to Advanced Mode                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ Frontend detects       │
              │ placeholder rules      │
              │ (baseline_placeholder  │
              │  && !hydrated)         │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │ Show hydration banner:         │
              │ "Baseline Rules Need           │
              │  Preparation"                  │
              │ [Prepare Rules Button]         │
              └────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │ User clicks "Prepare Rules"    │
              └────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────────┐
        │ POST /api/v1/baseline/rulesets/{id}/hydrate  │
        │ { actor: "user@example.com" }                │
        └──────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────────┐
        │ BaselineHydrationService.hydrate_baseline_   │
        │ rules(session, ruleset_id, actor)            │
        │                                               │
        │ For each placeholder rule:                   │
        │  1. Load rule and metadata                   │
        │  2. Check hydrated flag (skip if true)       │
        │  3. Determine field_type                     │
        │  4. Route to strategy:                       │
        │     - Enum → create N rules                  │
        │     - Formula → create 1 rule                │
        │     - Fixed → create 1 rule                  │
        │  5. Link via hydration_source_rule_id        │
        │  6. Deactivate original placeholder          │
        │  7. Mark as hydrated with timestamps         │
        └──────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │ Commit transaction         │
              │ Return HydrationResult     │
              └────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │ Frontend receives response     │
              │ - Show success toast           │
              │ - Hide banner                  │
              │ - Invalidate rules cache       │
              │ - Re-render with expanded rules│
              └────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │ Advanced Mode displays     │
              │ expanded rules with        │
              │ conditions and actions     │
              └────────────────────────────┘
```

### DDR Generation Hydration Example

**Before:**
```
ValuationRuleV2 (id=101)
├─ name: "DDR Generation"
├─ conditions: [] (empty)
├─ actions: [{ type: "multiplier", value_usd: 0.0 }]
└─ metadata: {
     baseline_placeholder: true,
     field_type: "enum_multiplier",
     valuation_buckets: { ddr3: 0.7, ddr4: 1.0, ddr5: 1.3 }
   }
```

**After Hydration:**
```
Original (id=101) - DEACTIVATED
├─ is_active: false
└─ metadata: { hydrated: true, hydrated_at: "...", ... }

Expanded Rule 1 (id=102)
├─ name: "DDR Generation: DDR3"
├─ conditions: [{ field: "ram_spec.ddr_generation", op: "equals", value: "ddr3" }]
├─ actions: [{ type: "multiplier", value_usd: 70.0 }]
└─ metadata: { hydration_source_rule_id: 101, enum_value: "ddr3" }

Expanded Rule 2 (id=103)
├─ name: "DDR Generation: DDR4"
├─ conditions: [{ field: "ram_spec.ddr_generation", op: "equals", value: "ddr4" }]
├─ actions: [{ type: "multiplier", value_usd: 100.0 }]
└─ metadata: { hydration_source_rule_id: 101, enum_value: "ddr4" }

Expanded Rule 3 (id=104)
├─ name: "DDR Generation: DDR5"
├─ conditions: [{ field: "ram_spec.ddr_generation", op: "equals", value: "ddr5" }]
├─ actions: [{ type: "multiplier", value_usd: 130.0 }]
└─ metadata: { hydration_source_rule_id: 101, enum_value: "ddr5" }
```

### Rule Creation Flow

```
User → Frontend
  └─ Fill rule form (name, conditions, actions)
  └─ POST /api/v1/valuation-rules
      └─ RulesService.create_rule()
          ├─ Validate: group exists, name unique, conditions valid
          ├─ Create ValuationRuleV2 record
          ├─ Create ValuationRuleCondition records
          ├─ Create ValuationRuleAction records
          ├─ Create ValuationRuleVersion snapshot
          ├─ Create ValuationRuleAudit entry
          └─ Commit transaction
      └─ Return RuleResponse
  └─ Update UI (React Query invalidation)
```

### Listing Valuation Flow

```
Listing Save → Backend
  └─ RuleEvaluationService.apply_ruleset_to_listing()
      ├─ Fetch listing with related data (CPU, GPU, RAM, storage)
      ├─ build_context_from_listing()
      ├─ Select ruleset:
      │   ├─ Use listing.ruleset_id if set and active
      │   ├─ Else match ruleset conditions against context
      │   └─ Else use default active ruleset
      ├─ Fetch all active rules from ruleset groups
      ├─ RuleEvaluator.evaluate_ruleset()
      │   └─ For each rule:
      │       ├─ Evaluate conditions → bool
      │       ├─ If matched, execute actions → adjustment
      │       └─ Aggregate results
      ├─ Calculate total_adjustment
      ├─ Update listing.adjusted_price_usd = price_usd + total_adjustment
      ├─ Update listing.valuation_breakdown = results JSON
      └─ Commit
  └─ Frontend displays updated valuation
```

### Rule Preview Flow

```
User → Frontend
  └─ Edit rule conditions/actions in modal
  └─ Click "Preview Impact"
      └─ POST /api/v1/valuation-rules/preview
          └─ RulePreviewService.preview_rule()
              ├─ Fetch sample listings (configurable size)
              ├─ For each listing:
              │   ├─ Build context
              │   ├─ Evaluate conditions
              │   └─ If matched, calculate adjustment
              ├─ Aggregate statistics:
              │   ├─ Match count, percentage
              │   ├─ Min/max/avg adjustment
              │   └─ Sample matched/non-matched listings
              └─ Return RulePreviewResponse
      └─ Display preview panel with statistics
```

## Key Concepts

### Rule Priority vs Evaluation Order

- **Priority**: Higher-level concept (10, 20, 30...) for grouping. Used for tie-breaking.
- **Evaluation Order**: Explicit sequence within a group (1, 2, 3...). Determines execution order.

All rules are evaluated in order unless `stop_on_first_match` is set (currently unused).

### Ruleset Conditions vs Rule Conditions

- **Ruleset Conditions** (`conditions_json` on Ruleset): Determines which ruleset applies to a listing. Used for automatic ruleset selection.
- **Rule Conditions**: Determines if a specific rule within a ruleset matches a listing.

**Example:**
- Ruleset A has condition: `cpu.manufacturer == "Intel"`
- Ruleset B has condition: `cpu.manufacturer == "AMD"`
- Intel listings automatically use Ruleset A, AMD listings use Ruleset B

### Adjustment Semantics

- **Negative values**: Deductions (e.g., -$50 reduces adjusted price)
- **Positive values**: Premiums (e.g., +$25 increases adjusted price)

This is a **subtractive model** for valuation (deductions from base price).

### Version History

- `ValuationRuleVersion`: Snapshots full rule state on each update
- `ValuationRuleAudit`: Logs all changes (create, update, delete, enable/disable) with actor and timestamp
- Enables rollback and compliance tracking

## API Endpoints

### Rulesets
- `POST /api/v1/rulesets` - Create ruleset
- `GET /api/v1/rulesets` - List rulesets (with `active_only` filter)
- `GET /api/v1/rulesets/{id}` - Get ruleset with full hierarchy
- `PUT /api/v1/rulesets/{id}` - Update ruleset
- `DELETE /api/v1/rulesets/{id}` - Delete ruleset (cascades)

### Rule Groups
- `POST /api/v1/rule-groups` - Create group
- `GET /api/v1/rule-groups` - List groups (filterable by ruleset)
- `PUT /api/v1/rule-groups/{id}` - Update group
- `DELETE /api/v1/rule-groups/{id}` - Delete group (cascades)

### Rules
- `POST /api/v1/valuation-rules` - Create rule
- `GET /api/v1/valuation-rules` - List rules (filterable by group)
- `GET /api/v1/valuation-rules/{id}` - Get single rule
- `PUT /api/v1/valuation-rules/{id}` - Update rule (creates version)
- `DELETE /api/v1/valuation-rules/{id}` - Delete rule
- `POST /api/v1/valuation-rules/{id}/duplicate` - Duplicate rule

### Evaluation
- `POST /api/v1/valuation-rules/preview` - Preview rule impact
- `POST /api/v1/valuation-rules/evaluate/{listing_id}` - Evaluate listing
- `POST /api/v1/valuation-rules/apply` - Apply ruleset to listing(s)

### Audit
- `GET /api/v1/valuation-rules/audit-log` - Fetch audit history

### Packaging
- `POST /api/v1/rulesets/{id}/export` - Export as JSON package
- `POST /api/v1/rulesets/import` - Import package (file upload)

### Baseline Hydration
- `POST /api/v1/baseline/rulesets/{ruleset_id}/hydrate` - Hydrate placeholder baseline rules

**Request Schema:**
```json
{
  "actor": "user@example.com"  // Optional, defaults to "system"
}
```

**Response Schema:**
```json
{
  "status": "success" | "error",
  "ruleset_id": 1,
  "hydrated_rule_count": 12,      // Number of placeholders hydrated
  "created_rule_count": 18,       // Total expanded rules created
  "hydration_summary": [
    {
      "original_rule_id": 101,
      "field_name": "DDR Generation",
      "field_type": "enum_multiplier",
      "expanded_rule_ids": [102, 103, 104]
    }
  ]
}
```

**Error Codes:**
- `200`: Success
- `404`: Ruleset not found
- `500`: Hydration failed (transaction rolled back)

## Future Enhancements

### Planned Features

1. **Rule Templates**: Predefined rule patterns for common scenarios
2. **Bulk Actions**: Apply actions to multiple rules at once
3. **Rule Dependencies**: Rules that depend on other rules
4. **Conditional Actions**: Actions with additional conditions
5. **Rule Scheduling**: Time-based rule activation
6. **A/B Testing**: Compare ruleset performance
7. **ML-Assisted Tuning**: Suggest optimal adjustment values

### Performance Optimizations

1. **Redis Caching**: Cache ruleset structures and evaluation results
2. **Lazy Loading**: Paginate rules in large groups
3. **Background Processing**: Async recalculation for bulk operations
4. **Materialized Views**: Pre-compute rule match statistics
5. **Query Optimization**: Add strategic indexes for condition fields

### UI Enhancements

1. **Drag-and-Drop Reordering**: Visual evaluation order management
2. **Rule Impact Visualization**: Charts showing adjustment distributions
3. **Condition Builder Autocomplete**: Suggest field names and values
4. **Rule Testing Playground**: Interactive rule testing with sample data
5. **Ruleset Comparison**: Side-by-side diff of rulesets
6. **Inline Rule Editing**: Edit rules without modal dialogs

## Configuration

### Application Settings

Valuation thresholds are stored in the `application_settings` table:

```json
{
  "key": "valuation_thresholds",
  "value_json": {
    "good_deal_threshold": 10.0,
    "great_deal_threshold": 20.0,
    "premium_threshold": 5.0
  }
}
```

Accessed via:
- Backend: `ApplicationSettingsService.get_valuation_thresholds()`
- Frontend: `useValuationThresholds()` hook

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis cache connection (optional)
- `VALUATION_BATCH_SIZE`: Default batch size for bulk operations (default: 100)

## Testing Strategy

### Unit Tests
- Condition evaluation logic
- Action calculation accuracy
- Formula parsing and evaluation
- Context building from listings

### Integration Tests
- Full rule evaluation flow
- Database transactions and cascades
- API endpoint contracts
- Ruleset import/export

### E2E Tests
- Rule creation via UI
- Valuation recalculation
- Breakdown modal display
- Basic mode syncing

## Troubleshooting

### Common Issues

**Rules not matching listings:**
- Verify condition field names match context structure
- Check logical operators (AND vs OR)
- Enable debug logging in RuleEvaluator

**Adjusted price not updating:**
- Confirm ruleset is active
- Check if listing has disabled ruleset in attributes_json
- Verify rule group is active
- Ensure rules have is_active=true

**Basic mode out of sync:**
- Basic mode relies on managed rules with `basic_managed` metadata
- Manual edits in Advanced mode may desync
- Re-save in Basic mode to regenerate managed rules

**Performance degradation:**
- Monitor rule count per listing (avoid thousands of rules)
- Use `evaluation_order` to optimize hot paths
- Consider caching frequently-used rulesets

## Conclusion

The Valuation Rules system provides a powerful, flexible, and user-friendly way to manage pricing adjustments in Deal Brain. Its hierarchical architecture, extensible action system, and dual-mode UI balance simplicity for common use cases with advanced capabilities for power users. The system's audit trail and versioning ensure traceability, while the preview functionality enables confident rule tuning.
