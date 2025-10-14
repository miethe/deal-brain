# Baseline Field Type Fix

**Date:** 2025-10-14
**Status:** ✅ Resolved

## Issue Summary

When attempting to load the valuation rules pane in the UI after the baseline valuation enhancements, the frontend failed to load any data with a Pydantic validation error:

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for BaselineFieldMetadata
field_type
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
```

## Root Cause Analysis

### Timeline of Events

1. **October 12, 2025**: Basic valuation enhancements completed (Workstreams 1-5)
2. **October 13, 2025**: Commit `04f1163` added proper `field_type` derivation logic
3. **October 14, 2025**: User reported issue - baseline metadata endpoint failing

### The Problem

The baseline rules imported on October 12-13 were created BEFORE the `field_type` derivation fix was implemented. The code initially had a bug where it was using the wrong field as `field_type`:

**Original buggy code** (before commit 04f1163):
```python
field = BaselineFieldMetadata(
    field_name=rule_meta.get("field_id", rule.name),
    field_type=rule_meta.get("unit", "USD"),  # ❌ Wrong! Using 'unit' as field_type
    ...
)
```

**Fixed code** (commit 04f1163):
```python
# Get or derive field_type
field_type = rule_meta.get("field_type")
if not field_type:
    # Fallback: derive from metadata for legacy rules
    field_type = BaselineLoaderService._derive_field_type_from_metadata(rule_meta)

field = BaselineFieldMetadata(
    field_name=rule_meta.get("field_id", rule.name),
    field_type=field_type,  # ✅ Correct! Properly derived
    ...
)
```

### Database State

All 44 baseline rules in the database had `field_type: None` in their `metadata_json` because:
1. They were imported using the buggy code
2. The fix added fallback logic, but existing data wasn't updated
3. The fallback logic should have worked, but there was a version mismatch

## Resolution

### 1. Created Migration Script

Created [scripts/fix_baseline_field_types.py](../../scripts/fix_baseline_field_types.py) to update existing database records:

```python
def derive_field_type(rule_meta: dict[str, Any]) -> str:
    """Derive the field type from rule metadata."""
    # Check if it's a formula field
    formula_text = rule_meta.get("formula_text")
    if formula_text and isinstance(formula_text, str) and formula_text.strip():
        return "formula"

    # Check if it's a multiplier field
    unit = rule_meta.get("unit")
    if isinstance(unit, str) and unit.lower() == "multiplier":
        return "multiplier"

    # Default to scalar
    return "scalar"
```

### 2. Executed the Fix

```bash
poetry run python scripts/fix_baseline_field_types.py
```

**Results:**
- Updated 44 rules across 2 baseline rulesets
- Field types assigned:
  - **formula**: 23 rules (have Formula field)
  - **multiplier**: 4 rules (unit == "multiplier")
  - **scalar**: 17 rules (default type)

### 3. Verification

After running the fix script:

```bash
# Test via Python
poetry run python -c "
from dealbrain_api.services.baseline_loader import BaselineLoaderService
# ... test get_baseline_metadata()
"
# ✅ Success! Got metadata for baseline: 1.0.20251013

# Test via HTTP API
curl http://localhost:8020/api/v1/baseline/meta
# ✅ Returns complete JSON with all field_type values populated
```

## Technical Details

### Field Type Classification

The `field_type` property indicates how a field contributes to valuation:

1. **formula** (`"formula"`): Fields that use formula expressions
   - Example: `cpu_id` with `Formula = "value = clamp(...)"`
   - Stored in: `rule_meta["formula_text"]`

2. **multiplier** (`"multiplier"`): Fields that multiply the subtotal
   - Example: `condition` with `unit = "multiplier"`
   - Stored in: `rule_meta["unit"]`

3. **scalar** (`"scalar"`): Fields with direct USD values or buckets
   - Example: `os_license` with valuation buckets
   - Default type for all other cases

### Database Schema

The `field_type` is stored in the `metadata_json` JSONB column:

```json
{
  "system_baseline": true,
  "entity_key": "Listing",
  "field_id": "cpu_id",
  "field_type": "formula",  // ← Added by fix
  "proper_name": "CPU",
  "unit": "USD",
  "formula_text": "value = clamp(...)",
  ...
}
```

## Prevention Measures

### Future Baseline Imports

The current code (post-fix) automatically derives `field_type` during import:

```python
# In _build_rule_metadata()
field_type = BaselineLoaderService._derive_field_type(field)

return {
    "system_baseline": True,
    "entity_key": entity_key,
    "field_id": field.get("id"),
    "field_type": field_type,  // ← Automatically derived
    ...
}
```

### Fallback Logic

For legacy rules or edge cases, the `get_baseline_metadata()` method has fallback logic:

```python
field_type = rule_meta.get("field_type")
if not field_type:
    # Fallback for legacy rules
    field_type = BaselineLoaderService._derive_field_type_from_metadata(rule_meta)
```

### Data Validation

The Pydantic schema ensures `field_type` is always a string:

```python
class BaselineFieldMetadata(BaseModel):
    field_name: str = Field(..., description="Field identifier")
    field_type: str = Field(..., description="Field data type")  # Required, non-null
    ...
```

## Files Modified

### Created
- [scripts/fix_baseline_field_types.py](../../scripts/fix_baseline_field_types.py) - Database migration script

### Previously Modified (commit 04f1163)
- [apps/api/dealbrain_api/services/baseline_loader.py](../../apps/api/dealbrain_api/services/baseline_loader.py)
  - Added `_derive_field_type()` method
  - Added `_derive_field_type_from_metadata()` fallback
  - Updated `_build_rule_metadata()` to set `field_type`
  - Updated `get_baseline_metadata()` to use fallback logic

## Impact Assessment

### Before Fix
- ❌ Baseline metadata API endpoint failed with validation error
- ❌ Frontend valuation pane unable to load
- ❌ Basic mode UI non-functional

### After Fix
- ✅ Baseline metadata API returns valid JSON
- ✅ All 44 rules have correct `field_type` values
- ✅ Frontend valuation pane loads correctly
- ✅ Basic mode UI operational

## Lessons Learned

1. **Data Migration Strategy**: When adding required fields to existing schemas, always:
   - Add default/fallback logic first
   - Migrate existing data
   - Then rely on strict validation

2. **Version Control**: Container code can be stale if not rebuilt:
   - Always verify code version in running containers
   - Use `poetry run` for local testing when possible
   - Consider database migrations for schema changes

3. **Testing Coverage**: Need tests for:
   - Loading baseline metadata with legacy data
   - Field type derivation for all scenarios
   - API endpoint error handling

## Related Documentation

- [Basic Valuation Complete Summary](./basic-valuation-complete-summary.md)
- [User Guide: Basic Valuation Mode](../../docs/user-guide/basic-valuation-mode.md)
- [Developer Guide: Baseline JSON Format](../../docs/developer/baseline-json-format.md)
- Git commit: `04f1163` - fix: Add field_type derivation for baseline metadata

## Status

✅ **Issue Resolved** - Baseline metadata loading successfully with all `field_type` values properly set.
