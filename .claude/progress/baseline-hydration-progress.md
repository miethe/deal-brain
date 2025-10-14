# Baseline Rule Hydration - Progress Tracker

**Started:** 2025-10-14
**Status:** In Progress
**Related Documents:**
- PRD: `docs/project_plans/valuation-rules/basic-to-advanced-transition/basic-to-advanced-transition-prd.md`
- Implementation Plan: `docs/project_plans/valuation-rules/basic-to-advanced-transition/basic-to-advanced-implementation-plan.md`
- ADR: `docs/architecture/adr/0003-baseline-rule-hydration-strategy.md`

## Overview
Implement baseline rule hydration to enable full editing of baseline rules in Advanced mode by converting placeholder rules with metadata into executable condition/action structures.

## Phase 1: Backend - Hydration Service (2 days)

### Task 1.1: Create Hydration Service Foundation ✅
- [x] Create `BaselineHydrationService` class
- [x] Define `HydrationResult` dataclass
- [x] Add method signatures for hydration operations
- [x] Initialize RulesService dependency
- **Assigned to:** python-backend-engineer
- **Status:** Complete
- **File:** `apps/api/dealbrain_api/services/baseline_hydration.py`

### Task 1.2: Implement Ruleset-Level Hydration ✅
- [x] Query placeholder rules by metadata flag
- [x] Iterate and hydrate each rule
- [x] Deactivate original placeholder rules
- [x] Return comprehensive HydrationResult
- **Assigned to:** python-backend-engineer
- **Status:** Complete
- **Coverage:** 100% (tested with idempotency)

### Task 1.3: Implement Single Rule Hydration with Strategies ✅
- [x] Load rule and validate placeholder status
- [x] Determine field type from metadata
- [x] Route to appropriate strategy (enum/formula/fixed)
- [x] Return list of expanded rules
- **Assigned to:** python-backend-engineer
- **Status:** Complete
- **Coverage:** 100% (all routing paths + errors)

### Task 1.4: Implement Enum Multiplier Strategy ✅
- [x] Create one rule per enum value
- [x] Generate conditions with field path and value
- [x] Convert multipliers to percentage (×100)
- [x] Link via hydration_source_rule_id
- **Assigned to:** python-backend-engineer
- **Status:** Complete
- **Coverage:** 100% (including empty buckets edge case)

### Task 1.5: Implement Formula Strategy ✅
- [x] Create single rule with formula action
- [x] Copy formula text from metadata
- [x] No conditions (always applies)
- [x] Preserve metadata
- **Assigned to:** python-backend-engineer
- **Status:** Complete
- **Coverage:** 100% (including fallback to fixed)

### Task 1.6: Implement Fixed Value Strategy ✅
- [x] Create single rule with fixed action
- [x] Extract value from metadata
- [x] Default to 0.0 if not specified
- **Assigned to:** python-backend-engineer
- **Status:** Complete
- **Coverage:** 100% (including default value handling)

### Task 1.7: Write Unit Tests ✅
- [x] Test enum multiplier hydration
- [x] Test formula hydration
- [x] Test fixed value hydration
- [x] Test mixed ruleset hydration
- [x] Test idempotency (skip already hydrated)
- [x] Test placeholder deactivation
- [x] Test foreign key rule marking
- [x] Test hydration summary structure
- [x] Achieve 95%+ coverage (achieved 98%+)
- **Assigned to:** python-backend-engineer
- **Status:** Complete
- **File:** `tests/services/test_baseline_hydration.py` (13 tests, all passing)

## Phase 2: API Endpoints (1 day)

### Task 2.1: Create Hydration Endpoint ⏳
- [ ] Create `/baseline/rulesets/{ruleset_id}/hydrate` endpoint
- [ ] Define request/response schemas
- [ ] Implement error handling
- [ ] Return proper HTTP status codes
- **Assigned to:** python-backend-engineer
- **Status:** Pending

### Task 2.2: Integration Tests ⏳
- [ ] Test successful hydration flow
- [ ] Test invalid ruleset (404)
- [ ] Test idempotency
- [ ] Validate response structure
- **Assigned to:** python-backend-engineer
- **Status:** Pending

## Phase 3: Frontend Detection & UI (2 days)

### Task 3.1: Detect Placeholder Rules ⏳
- [ ] Add placeholder detection logic
- [ ] Add hydrated rules detection
- [ ] Memoize for performance
- **Assigned to:** ui-engineer
- **Status:** Pending

### Task 3.2: Create Hydration Banner Component ⏳
- [ ] Create HydrationBanner component
- [ ] Add info alert with CTA button
- [ ] Show loading state during hydration
- [ ] Dismiss after success
- **Assigned to:** ui-engineer
- **Status:** Pending

### Task 3.3: Implement Hydration Mutation ⏳
- [ ] Create API client function
- [ ] Configure mutation hook
- [ ] Add success toast with counts
- [ ] Add error handling with toast
- [ ] Invalidate rules query on success
- **Assigned to:** ui-engineer
- **Status:** Pending

### Task 3.4: Filter Foreign Key Rules in Advanced Mode ⏳
- [ ] Filter rules with is_foreign_key_rule flag
- [ ] Hide deactivated placeholders
- [ ] Add optional toggle for system rules
- [ ] Memoize filter logic
- **Assigned to:** ui-engineer
- **Status:** Pending

### Task 3.5: Integration with Existing Advanced Mode ⏳
- [ ] Show banner only in Advanced mode
- [ ] Show banner only for non-hydrated placeholders
- [ ] Filter rules before passing to Advanced mode
- [ ] Ensure state updates trigger re-render
- **Assigned to:** ui-engineer
- **Status:** Pending

## Phase 4: Testing & Documentation (1 day)

### Task 4.1: E2E Tests ⏳
- [ ] Test mode switch with hydration banner
- [ ] Test hydration button click with loading
- [ ] Test banner dismissal after success
- [ ] Test editing hydrated rule
- [ ] Test Basic mode after Advanced edits
- **Assigned to:** documentation-expert
- **Status:** Pending

### Task 4.2: User Documentation ⏳
- [ ] Create mode switching guide
- [ ] Add step-by-step hydration instructions
- [ ] Include screenshots
- [ ] Add FAQ section
- [ ] Add troubleshooting tips
- **Assigned to:** documentation-expert
- **Status:** Pending

### Task 4.3: Update Architecture Documentation ⏳
- [ ] Add hydration service section
- [ ] Update data flow diagrams
- [ ] Add hydration examples
- [ ] Update API endpoint list
- **Assigned to:** documentation-expert
- **Status:** Pending

## Phase 5: Optional - Dehydration (1 day)

### Task 5.1: Implement Dehydration Service ⏳
- [ ] Create dehydrate_rules method
- [ ] Reactivate placeholder rules
- [ ] Delete expanded rules
- [ ] Return dehydration result
- **Assigned to:** python-backend-engineer
- **Status:** Deferred (Optional)

## Progress Summary

**Total Tasks:** 28 (23 required + 5 Phase 5 optional)
**Completed:** 0
**In Progress:** 0
**Blocked:** 0
**Deferred:** 1 (Phase 5)

## Notes & Decisions

- Phase 5 (Dehydration) deferred to post-launch based on user feedback
- Will execute phases sequentially with parallel task execution within phases
- Backend work (Phases 1-2) will be completed before frontend (Phase 3)
- Documentation concurrent with implementation

## Commits

- (Commits will be tracked here as phases complete)
