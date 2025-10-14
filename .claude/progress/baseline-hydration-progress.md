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

### Task 2.1: Create Hydration Endpoint ✅
- [x] Create `/baseline/rulesets/{ruleset_id}/hydrate` endpoint
- [x] Define request/response schemas
- [x] Implement error handling
- [x] Return proper HTTP status codes
- **Assigned to:** python-backend-engineer
- **Status:** Complete
- **Files:**
  - `packages/core/dealbrain_core/schemas/baseline.py` (schemas)
  - `apps/api/dealbrain_api/api/baseline.py` (endpoint)
- **URL:** `POST /api/v1/baseline/rulesets/{ruleset_id}/hydrate`

### Task 2.2: Integration Tests ✅
- [x] Test successful hydration flow
- [x] Test invalid ruleset (404)
- [x] Test idempotency
- [x] Validate response structure
- [x] Additional tests (default actor, empty ruleset, full workflow)
- **Assigned to:** python-backend-engineer
- **Status:** Complete
- **File:** `tests/test_baseline_hydration_api.py` (7 tests, all passing)

## Phase 3: Frontend Detection & UI (2 days)

### Task 3.1: Detect Placeholder Rules ✅
- [x] Add placeholder detection logic
- [x] Add hydrated rules detection
- [x] Memoize for performance
- **Assigned to:** ui-engineer
- **Status:** Complete
- **Location:** `apps/web/app/valuation-rules/page.tsx` (hasPlaceholderRules, hasHydratedRules hooks)

### Task 3.2: Create Hydration Banner Component ✅
- [x] Create HydrationBanner component
- [x] Add info alert with CTA button
- [x] Show loading state during hydration
- [x] Dismiss after success
- [x] Accessibility features (ARIA labels)
- **Assigned to:** ui-engineer
- **Status:** Complete
- **File:** `apps/web/app/valuation-rules/_components/hydration-banner.tsx` (NEW)

### Task 3.3: Implement Hydration Mutation ✅
- [x] Create API client function
- [x] Configure mutation hook
- [x] Add success toast with counts
- [x] Add error handling with toast
- [x] Invalidate rules query on success
- **Assigned to:** ui-engineer
- **Status:** Complete
- **Files:**
  - `apps/web/lib/api/baseline.ts` (hydrateBaselineRules function)
  - `apps/web/types/baseline.ts` (TypeScript types)
  - `apps/web/app/valuation-rules/page.tsx` (mutation hook)

### Task 3.4: Filter Foreign Key Rules in Advanced Mode ✅
- [x] Filter rules with is_foreign_key_rule flag
- [x] Hide deactivated placeholders
- [x] Memoize filter logic
- [x] Filter at both rule and group level
- **Assigned to:** ui-engineer
- **Status:** Complete
- **Location:** `apps/web/app/valuation-rules/page.tsx` (filteredRuleGroups hook)

### Task 3.5: Integration with Existing Advanced Mode ✅
- [x] Show banner only in Advanced mode
- [x] Show banner only for non-hydrated placeholders
- [x] Filter rules before passing to Advanced mode
- [x] Ensure state updates trigger re-render
- **Assigned to:** ui-engineer
- **Status:** Complete
- **Integration:** All components working together seamlessly

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
