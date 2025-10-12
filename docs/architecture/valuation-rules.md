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

## Data Flow Diagrams

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
