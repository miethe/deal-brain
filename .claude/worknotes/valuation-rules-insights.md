# Valuation Rules Consolidated - Key Insights

**Last Updated**: 2025-10-16
**Phase**: Critical Bug Fixes - Baseline Hydration Issues Resolved

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

### BUG-005: Foreign Key Rules Visible ✅ RESOLVED
- **File**: `apps/web/app/valuation-rules/page.tsx:464-468`
- **Issue**: Filtering exists but NO rules had `is_foreign_key_rule` metadata
- **Root Cause**: Baseline hydration never set the metadata flag
- **Fix**: Added `_is_foreign_key_rule()` helper and FK_ENTITY_KEYS constant to tag rules during hydration
- **Files Modified**: `apps/api/dealbrain_api/services/baseline_hydration.py`
- **Status**: Fixed in all 3 hydration strategies (_hydrate_enum_multiplier, _hydrate_formula, _hydrate_fixed)
- **Backfill**: Created `scripts/backfill_fk_metadata.py` for existing rules

### BUG-006: Scalar Field Rules Creating Null Fixed Values ✅ RESOLVED
- **Issue**: Baseline rules with `field_type: scalar` (CPU, GPU, Storage, etc.) were being hydrated into editable rules with $0.00 fixed values
- **Root Cause**: Scalar fields represent foreign key relationships, not valuation rules - they should not be hydrated at all
- **Impact**: Users saw dozens of meaningless "$0.00 Fixed Value" rules cluttering the UI
- **Fix**: Added early return in `hydrate_single_rule()` to skip scalar field types entirely
- **Files Modified**: `apps/api/dealbrain_api/services/baseline_hydration.py:157-162`
- **Status**: Scalar fields now return empty list `[]` instead of creating placeholder rules

## Architecture Notes

- No `useRuleGroups` hook exists; operations done via direct API calls
- React Query cache invalidation pattern: manual invalidation after mutations
- Formula engine uses AST-based safe evaluation
- Baseline hydration expands placeholder rules into multiple editable rules

## Key Files
- Frontend page: `apps/web/app/valuation-rules/page.tsx` (784 lines)
- Modal: `apps/web/components/valuation/rule-group-form-modal.tsx` (256 lines)
- Formula engine: `packages/core/dealbrain_core/rules/formula.py` (274 lines)
- Hydration service: `apps/api/dealbrain_api/services/baseline_hydration.py` (401 lines)
- Backfill script: `scripts/backfill_fk_metadata.py` (NEW)

## Recent Fixes (2025-10-16)

### Baseline Hydration Improvements

**Problem Statement**: After switching from Basic to Advanced mode, users saw:
1. Dozens of meaningless rules with "Fixed Value: $0.00"
2. Foreign key rules visible despite "Show system rules" toggle being off

**Root Cause Analysis**:
- Scalar field types (CPU, GPU, Storage) were being hydrated into editable rules
- These fields represent FK relationships and should never be user-editable
- No rules had `is_foreign_key_rule` metadata, making the toggle ineffective

**Solution Implemented**:
1. **Skip Scalar Fields**: Modified `hydrate_single_rule()` to return empty list for `field_type: scalar`
2. **Tag FK Rules**: Added `_is_foreign_key_rule()` helper method using `FK_ENTITY_KEYS` constant
3. **Update All Strategies**: Modified all 3 hydration strategies to set `is_foreign_key_rule` in metadata
4. **Backfill Existing Rules**: Created migration script to update 40 existing hydrated rules

**Test Coverage**:
- Added 3 new tests (test_scalar_field_type_skipped, test_foreign_key_rule_tagging, test_foreign_key_tagging_all_strategies)
- All 20 baseline hydration tests passing

**Impact**:
- Users no longer see scalar field "$0.00" rules after hydration
- "Show system rules" toggle now correctly filters FK-related rules
- Cleaner, more intuitive Advanced Mode experience

### Baseline Hydration Critical Fixes - Phase 2 (2025-10-16)

**Problem Statement**: Hydration failing with errors:
1. Formula validation errors for pseudo-code (`≈`, `if...then`, etc.)
2. "No default value found" warnings flooding logs
3. Many rules not creating at all

**Root Cause Analysis**:
- Baseline rules contain human-readable pseudo-code, not executable Python
- Examples: `"usd ≈ (gpu_mark/1000)*8.0"`, `"if tdp_w>120 then apply penalty"`
- System was trying to parse these as Python AST, which fails
- Missing default values in metadata caused fallback issues

**Solution Implemented**:
1. **Graceful Formula Handling** (`baseline_hydration.py:334-350`):
   - Log as warning (not error) since pseudo-code is expected
   - Create placeholder fixed rule ($0.00) for user configuration
   - Preserve pseudo-code in `original_formula_description` metadata
   - Set `requires_user_configuration: true` flag
2. **Enhanced Default Value Extraction** (`baseline_hydration.py:394-408`):
   - Added `base_value` to search keys
   - Changed logging to info level (expected behavior)
   - Clear messaging that 0.0 is intentional placeholder
3. **Metadata Override Support** (`baseline_hydration.py:375, 421-430`):
   - `_hydrate_fixed()` accepts optional `override_metadata` parameter
   - Enables context preservation when falling back from formula validation

**Test Coverage**:
- Added comprehensive test for pseudo-code formula handling
- All 21 baseline hydration tests passing

**Impact**:
- No more hydration failures or error logs
- Pseudo-code formulas create editable placeholder rules
- Original intent preserved in metadata for user reference
- Clear indicators of which rules need manual configuration

**Data Import Requirements** (for future baseline rule updates):
- Formula rules must use valid Python syntax (no `≈`, `if...then`, pseudo-code)
- Use Python ternary: `value if condition else other_value`
- Available functions: `clamp(value, min, max)`, standard math operators
- Fixed rules should include `default_value` (or `Default`, `value`, `Value`, `base_value`) in metadata
