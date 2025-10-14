# ADR 0003: Baseline Rule Hydration Strategy

**Date:** 2025-10-14
**Status:** Proposed
**Deciders:** Lead Architect, Backend Architect, UI Engineer
**Related:** PRD - Basic to Advanced Mode Transition

## Context

The Deal Brain valuation system uses a dual-mode UI for rule management:
- **Basic Mode:** Simplified UI with baseline fields and override values
- **Advanced Mode:** Full rule hierarchy with conditions, actions, and logic

Currently, baseline rules are stored as **placeholders** with metadata:
- Empty conditions array
- Actions with `value_usd: 0.0`
- Metadata contains field configuration (`valuation_buckets`, `formula_text`)

**Problem:** When users switch from Basic to Advanced mode, placeholder rules appear empty and uneditable.

**Need:** A mechanism to convert baseline metadata into executable rule structures for Advanced mode editing.

## Decision

We will implement **on-demand hydration** of baseline placeholder rules using a dedicated `BaselineHydrationService`.

### Key Decisions

#### 1. Hydration Trigger: User-Initiated
**Decision:** Require explicit user action to hydrate rules (via banner + button in Advanced mode)

**Rationale:**
- Gives users control over when rules are expanded
- Prevents unexpected rule proliferation
- Allows users to review before committing
- Supports audit trail (who hydrated, when)

**Alternatives Considered:**
- ❌ **Automatic on mode switch:** Could surprise users with many new rules
- ❌ **Virtual expansion (client-side only):** Complex state management, no persistence

#### 2. Hydration Storage: Expanded Real Rules
**Decision:** Create new `ValuationRuleV2` records for each expanded rule, deactivate original placeholder

**Rationale:**
- Rules become fully editable in Advanced mode
- Standard rule evaluation applies (no special cases)
- Clear audit trail via `created_by`, `created_at`
- Supports rollback (reactivate placeholder, delete expanded)

**Alternatives Considered:**
- ❌ **Keep placeholders, virtual UI expansion:** Lose ability to edit in DB
- ❌ **Overwrite placeholder in-place:** Lose original metadata

#### 3. Enum Field Strategy: One Rule Per Value
**Decision:** For enum multiplier fields (e.g., DDR Generation), create one rule per enum value

**Example:**
```
DDR Generation (placeholder) →
  ├─ DDR Generation: DDR3 (condition: ddr_generation = ddr3, action: 0.7x)
  ├─ DDR Generation: DDR4 (condition: ddr_generation = ddr4, action: 1.0x)
  └─ DDR Generation: DDR5 (condition: ddr_generation = ddr5, action: 1.3x)
```

**Rationale:**
- Each rule independently editable
- Conditions and actions explicitly matched
- Standard rule evaluation (no special logic)
- Users can add/remove enum values easily

**Trade-offs:**
- ✅ **Pro:** Full Advanced mode flexibility
- ❌ **Con:** More DB records (acceptable - typically 3-5 per field)

**Alternatives Considered:**
- ❌ **Single rule with multi-value condition:** Complex action mapping
- ❌ **Keep enum logic in action modifiers:** Not editable in UI

#### 4. Formula Field Strategy: Single Rule with Formula Action
**Decision:** For formula fields, create one rule with `action_type: formula`

**Example:**
```
Total RAM Capacity (placeholder) →
  └─ Total RAM Capacity (action: formula = "ram_capacity_gb * base_price_per_gb")
```

**Rationale:**
- Formulas already support complex logic
- No need for multiple rules
- Editable in Advanced mode formula builder

#### 5. Foreign Key Rules: Hidden in Advanced Mode
**Decision:** Hide rules with `is_foreign_key_rule: true` metadata in Advanced UI

**Rationale:**
- These rules reference other entities (RAM Spec, GPU)
- Not directly editable (tied to entity catalog)
- Showing them causes confusion
- Can be revealed via "Show System Rules" toggle (optional)

**Alternatives Considered:**
- ❌ **Show as read-only:** Clutters UI with non-actionable rules
- ❌ **Delete foreign key rules:** Lose important valuation logic

#### 6. Metadata Preservation: Link via hydration_source_rule_id
**Decision:** Store original rule ID in expanded rules' metadata

**Schema:**
```python
# Original placeholder (after hydration)
{
  "id": 101,
  "is_active": false,
  "metadata_json": {
    "hydrated": true,
    "hydrated_at": "2025-10-14T10:00:00Z",
    "hydrated_by": "user@example.com"
  }
}

# Expanded rule
{
  "id": 102,
  "metadata_json": {
    "hydration_source_rule_id": 101,
    "enum_value": "ddr3"
  }
}
```

**Rationale:**
- Enables rollback/rehydration
- Audit trail for rule expansion
- Can reconstruct original metadata if needed

## Architectural Implications

### Database Impact
- **Storage:** +50-100 rules per baseline ruleset (depends on enum field count)
- **Performance:** Negligible (rules loaded once, cached)
- **Migrations:** None required (use existing schema + metadata_json)

### Service Layer
- **New Service:** `BaselineHydrationService` (300-400 LOC)
- **Dependencies:** `RulesService` (for rule creation)
- **Integration:** Called via API endpoint

### API Layer
- **New Endpoint:** `POST /api/v1/valuation/rulesets/{id}/hydrate-baseline`
- **Payload:** `{ actor: string }`
- **Response:** Hydration summary with rule counts

### Frontend Impact
- **Detection Logic:** Scan rules for `baseline_placeholder: true`
- **UI Components:** Hydration banner, progress indicator
- **Rule Rendering:** Filter foreign key rules, display expanded rules

### Evaluation Logic
- **No Changes Required:** Hydrated rules are standard `ValuationRuleV2` records
- **Backward Compatibility:** Placeholder rules with 0.0 values produce 0.0 adjustments (fixed by multiplier bug fix)

## Data Migration Strategy

### Existing Rulesets
**Approach:** No automatic migration - hydration on-demand

1. Users with existing baseline rulesets see placeholder rules
2. Switching to Advanced mode shows hydration prompt
3. User clicks "Hydrate Rules" → service expands rules
4. Future loads show expanded rules

**Rationale:**
- Avoids bulk DB updates
- Users hydrate only if needed
- Gradual rollout

### New Rulesets
**Approach:** Create placeholders as usual, hydrate as needed

- Baseline loader continues creating placeholders
- Hydration available immediately after creation
- Supports iterative development (add features before hydration)

## Consequences

### Positive
- ✅ Baseline rules fully editable in Advanced mode
- ✅ No special evaluation logic needed
- ✅ Clear separation: Basic (placeholders) vs Advanced (expanded)
- ✅ User control over rule expansion
- ✅ Rollback capability via original placeholder

### Negative
- ❌ Rule count increases (mitigated by grouping in UI)
- ❌ Additional service complexity (mitigated by clear separation)
- ❌ User education needed (mitigated by in-app prompts)

### Neutral
- Rules are one-way hydrated (Basic → Advanced)
- Reverting requires manual dehydration (future feature)
- Hydration is ruleset-scoped (not global)

## Alternatives Considered

### Alternative 1: In-Place Placeholder Hydration
**Approach:** Overwrite placeholder rules with full conditions/actions

**Rejected Because:**
- Loses original baseline metadata
- No audit trail of expansion
- Harder to rollback
- Breaks idempotency of baseline loader

### Alternative 2: Virtual Expansion (Client-Side Only)
**Approach:** Expand placeholders in UI, don't persist

**Rejected Because:**
- Complex state management
- Rules not editable (no DB persistence)
- Requires special evaluation logic
- Hydration state lost on refresh

### Alternative 3: Dual Rule Sets
**Approach:** Maintain separate rules for Basic and Advanced modes

**Rejected Because:**
- Data duplication
- Complex sync logic between modes
- Higher risk of drift
- More storage required

## Implementation Checklist

- [ ] Create `BaselineHydrationService` with enum/formula strategies
- [ ] Add hydration endpoint to API
- [ ] Implement frontend detection and hydration UI
- [ ] Filter foreign key rules in Advanced mode
- [ ] Write unit tests (90%+ coverage)
- [ ] Write integration tests for hydration flow
- [ ] E2E tests for mode switching
- [ ] User documentation with examples
- [ ] Migration guide for existing rulesets

## Review Notes

**Date:** 2025-10-14
**Reviewers:** TBD

**Approved:** [ ]
**Rejected:** [ ]
**Needs Revision:** [ ]

**Comments:**
[Space for reviewer feedback]

## References

- PRD: Basic to Advanced Mode Transition
- Original Implementation: BaselineLoaderService
- Related Bug: Valuation calculation 300% adjustment issue (fixed separately)
- Architecture Doc: Valuation Rules System
