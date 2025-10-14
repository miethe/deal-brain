# Basic to Advanced Mode Transition - PRD

**Date:** 2025-10-14
**Status:** Draft
**Priority:** High

## Problem Statement

When switching from Basic to Advanced mode in the Valuation Rules page, the Baseline rules are not populated correctly. All fields show:
- 0 conditions
- 1 action with blank value and default weights
- Priority correctly set
- RuleGroups and Rules exist

**Expected Behavior:**
The Advanced mode should correctly reflect the current state of the Baseline rules from Basic mode, allowing users to edit beyond the simple Overrides available in Basic mode.

**Current Behavior:**
Baseline rules appear empty in Advanced mode, making them uneditable.

## Root Cause Analysis

### 1. Placeholder Actions Issue
Baseline rules are created by `BaselineLoaderService` with **placeholder actions**:
```python
{
    "action_type": "fixed_value" or "multiplier",
    "metric": None,
    "value_usd": 0.0,  # ← Placeholder
    "unit_type": None,
    "formula": None,
    "modifiers": {
        "baseline_placeholder": True,
        "baseline_unit": unit,
    },
}
```

These placeholders have:
- `value_usd: 0.0` (appears blank in UI)
- No conditions (empty array)
- Metadata stored separately in `rule_metadata`

### 2. Metadata vs. Executable Rules
Baseline field metadata is stored in:
- `ValuationRuleV2.metadata_json` with keys:
  - `field_type` (e.g., "fixed", "formula", "enum_multiplier")
  - `valuation_buckets` (for enum types with per-value multipliers)
  - `formula_text`
  - `proper_name`, `description`, `explanation`

This metadata is **not** converted into executable conditions and actions.

### 3. Missing Condition-to-Action Mapping

For baseline fields like "DDR Generation":
- **Basic Mode UI:** Shows overrides like "DDR3: 0.7x, DDR4: 1.0x, DDR5: 1.3x"
- **Expected Advanced Mode:** Should create multiple rules OR a single rule with condition-action pairing
- **Current Advanced Mode:** Shows single rule with no conditions and 0.0 value

The system lacks a **hydration process** to convert baseline metadata into editable Advanced mode structures.

## User Stories

### US-1: View Baseline Rules in Advanced Mode
**As a** power user
**I want to** view baseline rules with their conditions and actions in Advanced mode
**So that** I can understand how valuations are calculated

**Acceptance Criteria:**
- Baseline rules display conditions (e.g., "DDR Generation = DDR4")
- Actions show configured values (e.g., "Multiplier: 1.0x")
- Rules match what was configured in Basic mode

### US-2: Edit Baseline Rules in Advanced Mode
**As a** power user
**I want to** edit baseline rule conditions and actions in Advanced mode
**So that** I can make granular adjustments beyond Basic mode capabilities

**Acceptance Criteria:**
- Can add/edit/remove conditions for baseline rules
- Can modify action values and types
- Changes persist and affect listing valuations
- Can see immediate preview of changes

### US-3: Sync Basic Mode After Advanced Edits
**As a** user
**I want to** see my Advanced mode edits reflected in Basic mode (where applicable)
**So that** I maintain consistency across modes

**Acceptance Criteria:**
- Simple baseline rules edited in Advanced mode appear in Basic mode
- Complex rules show as "Managed in Advanced Mode"
- No data loss when switching between modes

## Design Options

### Option 1: Hydrate on Mode Switch (Recommended)

**Concept:** When switching from Basic to Advanced, convert baseline metadata into full rule structures.

**Process:**
1. User switches to Advanced mode
2. System detects placeholder baseline rules (via `baseline_placeholder: true`)
3. Hydration service reads `valuation_buckets` from metadata
4. Creates conditions and actions:
   - For `enum_multiplier`: One rule per enum value with condition + multiplier action
   - For `formula`: Single rule with formula action
   - For `fixed`: Single rule with fixed value action
5. Marks rules as `hydrated: true` to prevent re-hydration
6. Displays in Advanced mode UI

**Pros:**
- Clean separation: metadata → executable rules
- Preserves original baseline metadata
- Allows full Advanced mode editing
- One-way sync (Basic → Advanced)

**Cons:**
- Rules proliferate (one per enum value)
- Increases database records
- More complex UI rendering

### Option 2: Virtual Rule Expansion

**Concept:** Keep placeholder rules in DB, expand virtually in UI only.

**Process:**
1. Advanced mode UI detects placeholder rules
2. Client-side expansion of metadata into virtual conditions/actions
3. Display virtual rules in UI
4. On save, convert virtual rules to real rules

**Pros:**
- No DB changes on mode switch
- Fewer database records
- Faster mode switching

**Cons:**
- Complex client-side logic
- Virtual vs. real rule confusion
- Harder to maintain consistency

### Option 3: Dual Rule Sets

**Concept:** Maintain separate rule structures for Basic and Advanced modes.

**Process:**
1. Basic mode uses baseline placeholders + overrides
2. Advanced mode uses fully expanded rules
3. Mode switch triggers conversion between formats
4. Maintain sync via "source of truth" flag

**Pros:**
- Each mode optimized for its use case
- Clear separation of concerns

**Cons:**
- Data duplication
- Complex sync logic
- Potential for drift between modes

## Recommended Solution: Option 1 with Enhancements

### Architecture

#### 1. Baseline Hydration Service
**Location:** `apps/api/dealbrain_api/services/baseline_hydration.py`

**Responsibilities:**
- Detect placeholder baseline rules
- Read metadata (`field_type`, `valuation_buckets`, `formula_text`)
- Generate conditions and actions based on field type
- Mark rules as hydrated
- Preserve original metadata for documentation

**API:**
```python
class BaselineHydrationService:
    async def hydrate_baseline_rules(
        self,
        session: AsyncSession,
        ruleset_id: int,
        actor: str = "system"
    ) -> HydrationResult:
        """Convert placeholder baseline rules to full executable rules."""

    async def hydrate_single_rule(
        self,
        session: AsyncSession,
        rule_id: int,
        actor: str = "system"
    ) -> list[ValuationRuleV2]:
        """Hydrate a single placeholder rule, may return multiple expanded rules."""
```

#### 2. Hydration Strategies

**Strategy A: Enum Multiplier Fields**
- Example: DDR Generation, Condition, Release Year
- Metadata: `valuation_buckets: {"ddr3": 0.7, "ddr4": 1.0, "ddr5": 1.3}`
- Output: **One rule per enum value**

```python
# For DDR3
Rule(
    name="DDR Generation: DDR3",
    conditions=[{
        "field": "ram_spec.ddr_generation",
        "operator": "equals",
        "value": "ddr3"
    }],
    actions=[{
        "action_type": "multiplier",
        "value_usd": 70.0,  # 0.7 * 100
        "modifiers": {"original_multiplier": 0.7}
    }]
)

# For DDR4, DDR5... (similar structure)
```

**Strategy B: Formula Fields**
- Example: Total RAM Capacity
- Metadata: `formula_text: "ram_capacity_gb * base_price_per_gb"`
- Output: **Single rule with formula action**

```python
Rule(
    name="Total RAM Capacity",
    conditions=[],  # Always applies
    actions=[{
        "action_type": "formula",
        "formula": "ram_capacity_gb * base_price_per_gb",
        "value_usd": None
    }]
)
```

**Strategy C: Fixed Value Fields**
- Example: Base depreciation
- Metadata: `field_type: "fixed"`
- Output: **Single rule with fixed action**

```python
Rule(
    name="Base Depreciation",
    conditions=[],
    actions=[{
        "action_type": "fixed_value",
        "value_usd": -50.0
    }]
)
```

#### 3. Foreign Key Rules Handling

**Issue:** RAM Spec and GPU rules are mapped via foreign keys, shown in RuleGroups but cannot be edited directly.

**Solution:**
- **Option A:** Hide foreign key rules in Advanced mode (cleaner UX)
- **Option B:** Show as read-only with explanation
- **Recommendation:** Option A - hide via `is_foreign_key_rule: true` metadata flag

### Database Changes

#### Migration: Add Hydration Metadata

```python
# Migration: 0019_add_rule_hydration_metadata

# Add fields to ValuationRuleV2.metadata_json:
# - hydrated: bool (false for placeholders, true after hydration)
# - hydration_source_rule_id: int (for tracking expanded rules)
# - is_foreign_key_rule: bool (for hiding in Advanced UI)
# - original_multiplier: float (for enum multipliers)
```

No schema changes needed - use existing `metadata_json` column.

### Frontend Changes

#### 1. Advanced Mode Rule Rendering
**Location:** `apps/web/app/valuation-rules/_components/advanced-mode.tsx`

**Changes:**
- Filter out rules with `is_foreign_key_rule: true`
- Display hydrated rules with conditions and actions
- Show "Hydrate Baseline Rules" button if placeholders detected

#### 2. Hydration Trigger UI
**Location:** `apps/web/app/valuation-rules/page.tsx`

**Changes:**
- Add detection for placeholder baseline rules
- Show banner: "Baseline rules need hydration for Advanced editing"
- Button: "Prepare Baseline Rules for Editing"
- Progress indicator during hydration

#### 3. Basic Mode Compatibility
**Location:** `apps/web/app/valuation-rules/_components/basic-mode-tabs.tsx`

**Changes:**
- Detect if rules are hydrated
- If hydrated, show read-only view with "Managed in Advanced Mode" label
- Prevent overrides on hydrated rules
- Allow reverting hydration (optional)

### API Endpoints

#### POST /api/v1/valuation/rulesets/{ruleset_id}/hydrate-baseline
**Description:** Hydrate all placeholder baseline rules in a ruleset

**Request:**
```json
{
  "actor": "user@example.com"
}
```

**Response:**
```json
{
  "status": "success",
  "ruleset_id": 42,
  "hydrated_rule_count": 12,
  "created_rule_count": 18,  // Some rules split into multiple
  "hydration_summary": [
    {
      "original_rule_id": 101,
      "field_name": "DDR Generation",
      "field_type": "enum_multiplier",
      "expanded_rules": [102, 103, 104]
    },
    ...
  ]
}
```

#### POST /api/v1/valuation/rules/{rule_id}/hydrate
**Description:** Hydrate a single placeholder rule

**Response:** Similar structure, single rule focus

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Basic Mode → Advanced Mode Transition                       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ User clicks "Advanced" │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │ Detect placeholder rules   │
              │ (baseline_placeholder=true)│
              └────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │ Show hydration prompt banner   │
              │ "Prepare for Advanced Editing" │
              └────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │ User clicks "Hydrate Rules"    │
              └────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────┐
        │ POST /rulesets/{id}/hydrate-baseline     │
        └──────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────────┐
        │ BaselineHydrationService.hydrate()       │
        │                                           │
        │ For each placeholder rule:                │
        │  1. Read metadata (valuation_buckets)    │
        │  2. Generate conditions + actions         │
        │  3. Create new expanded rules             │
        │  4. Mark original as hydrated             │
        │  5. Link via hydration_source_rule_id    │
        └──────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │ Return hydration summary   │
              └────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │ Refresh Advanced mode UI   │
              │ Display expanded rules     │
              └────────────────────────────┘
```

### Example: DDR Generation Hydration

**Before (Placeholder):**
```json
{
  "id": 101,
  "name": "DDR Generation",
  "group_id": 10,
  "conditions": [],
  "actions": [{
    "action_type": "multiplier",
    "value_usd": 0.0,
    "modifiers": {"baseline_placeholder": true}
  }],
  "metadata_json": {
    "field_type": "enum_multiplier",
    "valuation_buckets": {
      "ddr3": 0.7,
      "ddr4": 1.0,
      "ddr5": 1.3
    },
    "proper_name": "DDR Generation",
    "baseline_placeholder": true
  }
}
```

**After Hydration:**
```json
// Original rule marked as hydrated
{
  "id": 101,
  "name": "DDR Generation (Hydrated)",
  "group_id": 10,
  "is_active": false,  // Deactivated
  "metadata_json": {
    "hydrated": true,
    "hydrated_at": "2025-10-14T10:00:00Z"
  }
}

// Expanded Rule 1
{
  "id": 102,
  "name": "DDR Generation: DDR3",
  "group_id": 10,
  "conditions": [{
    "field": "ram_spec.ddr_generation",
    "operator": "equals",
    "value": "ddr3"
  }],
  "actions": [{
    "action_type": "multiplier",
    "value_usd": 70.0,
    "modifiers": {"original_multiplier": 0.7}
  }],
  "metadata_json": {
    "hydration_source_rule_id": 101,
    "enum_value": "ddr3"
  }
}

// Expanded Rule 2 (DDR4)
{
  "id": 103,
  "name": "DDR Generation: DDR4",
  // ... similar structure with value_usd: 100.0
}

// Expanded Rule 3 (DDR5)
{
  "id": 104,
  "name": "DDR Generation: DDR5",
  // ... similar structure with value_usd: 130.0
}
```

## Implementation Phases

### Phase 1: Backend Hydration Service (2-3 days)
1. Create `BaselineHydrationService`
2. Implement hydration strategies (enum, formula, fixed)
3. Add hydration metadata handling
4. Write unit tests (90%+ coverage)

### Phase 2: API Endpoints (1 day)
1. Create `/hydrate-baseline` endpoint
2. Add validation and error handling
3. Integration tests

### Phase 3: Frontend Detection & UI (2 days)
1. Add placeholder detection in Advanced mode
2. Create hydration prompt banner
3. Implement hydration trigger button
4. Show progress and results

### Phase 4: Advanced Mode Rendering (1 day)
1. Filter foreign key rules
2. Display hydrated rules with full details
3. Handle edge cases (no conditions, complex formulas)

### Phase 5: Testing & Documentation (1 day)
1. E2E tests for mode switching
2. User documentation
3. Migration guide for existing rulesets

### Phase 6: Optional - Dehydration (1 day)
1. Add "Revert to Placeholder" functionality
2. Useful for resetting to baseline state

## Success Metrics

- ✅ Baseline rules display conditions and actions in Advanced mode
- ✅ All baseline field types hydrate correctly (enum, formula, fixed)
- ✅ Users can edit hydrated rules in Advanced mode
- ✅ No valuation calculation changes before/after hydration
- ✅ Foreign key rules properly hidden in Advanced UI
- ✅ 95%+ test coverage for hydration service

## Risk Mitigation

### Risk 1: Rule Proliferation
**Concern:** Hydrating enum fields creates many rules (e.g., 3 rules for DDR Gen, 3 for Condition = 9 combinations)

**Mitigation:**
- Keep original placeholder rule deactivated as reference
- Group expanded rules visually in UI
- Implement collapse/expand for rule groups

### Risk 2: Performance Impact
**Concern:** Hydration creates many DB records

**Mitigation:**
- Batch rule creation in single transaction
- Use async background job for large rulesets
- Cache hydrated rule structures

### Risk 3: User Confusion
**Concern:** Users may not understand hydrated vs. placeholder rules

**Mitigation:**
- Clear UI messaging and banners
- Tooltips explaining hydration
- "Undo Hydration" option for safety
- Documentation with screenshots

## Open Questions

1. **Q:** Should hydration be automatic on mode switch or require user confirmation?
   **A:** Require confirmation via banner + button (user control)

2. **Q:** How to handle rules manually edited in Advanced mode then viewed in Basic mode?
   **A:** Show as "Managed in Advanced Mode" (read-only in Basic)

3. **Q:** Should foreign key rules be completely hidden or shown as read-only?
   **A:** Hidden by default, with toggle to "Show System Rules" (advanced option)

4. **Q:** What happens if user adds new enum values after hydration?
   **A:** Add "Re-hydrate" button to sync new values

## Next Steps

1. Review and approve this PRD
2. Create ADR for hydration strategy selection
3. Create implementation plan with detailed tasks
4. Assign to backend-architect for hydration service
5. Assign to ui-engineer for frontend components
