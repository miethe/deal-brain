# Valuation Rules Phase 1 - Key Insights

**Date**: 2025-10-15
**Phase**: Critical Bug Fixes

## Bug Root Causes

### BUG-001: Wrong Modal Opens
- **File**: `apps/web/app/valuation-rules/page.tsx:701`
- **Issue**: Button handler calls `setIsRulesetBuilderOpen(true)` instead of `setIsGroupFormOpen(true)`
- **Fix**: 1-line change

### BUG-002: RuleGroup Not Appearing After Creation
- **File**: `apps/web/components/valuation/rule-group-form-modal.tsx:112-114`
- **Issue**: Modal closes before query refetch completes (race condition)
- **Fix**: Await refetch or implement optimistic updates

### BUG-003: Formula Evaluation Failing
**Multiple issues**:
1. Missing `clamp()` function in formula engine allowed functions
2. Baseline hydration checks wrong metadata key for formula (`formula_text` vs `Formula`)
3. Silent error handling in evaluator (no logging)
4. Context building inconsistency (flat vs nested field access)

**Files**:
- `packages/core/dealbrain_core/rules/formula.py` - Add clamp()
- `apps/api/dealbrain_api/services/baseline_hydration.py` - Fix key extraction
- `packages/core/dealbrain_core/rules/evaluator.py` - Add logging

### BUG-004: Baseline Hydration Issues
- Same root cause as BUG-003 (formula extraction)
- Formula actions becoming Fixed $0 actions due to missing formula_text

### BUG-005: Foreign Key Rules Visible
- **File**: `apps/web/app/valuation-rules/page.tsx:464-468`
- **Issue**: Filtering exists but some rules lack `is_foreign_key_rule` metadata
- **Fix**: Ensure all FK rules tagged properly

## Architecture Notes

- No `useRuleGroups` hook exists; operations done via direct API calls
- React Query cache invalidation pattern: manual invalidation after mutations
- Formula engine uses AST-based safe evaluation
- Baseline hydration expands placeholder rules into multiple editable rules

## Key Files
- Frontend page: `apps/web/app/valuation-rules/page.tsx` (784 lines)
- Modal: `apps/web/components/valuation/rule-group-form-modal.tsx` (256 lines)
- Formula engine: `packages/core/dealbrain_core/rules/formula.py` (274 lines)
- Hydration service: `apps/api/dealbrain_api/services/baseline_hydration.py` (314 lines)
