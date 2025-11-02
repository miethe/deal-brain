# Bug Fixes Tracking

## 2025-11-01: FastAPI DELETE Endpoint 204 Response Body Issue

**Issue**: API failed to start with `AssertionError: Status code 204 must not have a response body`

**Location**: `apps/api/dealbrain_api/api/listings.py:351`

**Root Cause**: DELETE endpoint decorated with `status_code=status.HTTP_204_NO_CONTENT` without explicitly setting `response_model=None`. FastAPI's newer versions are stricter about HTTP 204 semantics - this status code must not have a response body.

**Fix**: Added `response_model=None` parameter to the `@router.delete()` decorator.

**Code Change**:
```python
# Before
@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)

# After
@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
```

**Testing**: Verified fix by rebuilding Docker container and confirming API starts successfully with no errors.

**Commit**: 0e1cf35

## 2025-11-02: Celery AsyncIO Event Loop Conflict

**Issue**: Celery task `admin.recalculate_cpu_mark_metrics` failing with `RuntimeError: Task got Future attached to a different loop`

**Location**: `apps/api/dealbrain_api/tasks/admin.py` and `apps/api/dealbrain_api/tasks/baseline.py`

**Root Cause**: Tasks used `asyncio.run()` which creates implicit event loops. In Celery forked workers with global SQLAlchemy async engine state, the cached engine remains attached to old event loops, causing conflicts when new event loops are created.

**Fix**: Replaced `asyncio.run()` with explicit event loop management pattern:
1. Create fresh event loop with `asyncio.new_event_loop()`
2. Call `dispose_engine()` to reset cached SQLAlchemy engine
3. Execute async function with `loop.run_until_complete()`
4. Proper cleanup in finally block (shutdown async generators, close loop, clear context)

**Files Modified**:
- `apps/api/dealbrain_api/tasks/admin.py` - Fixed 4 tasks (recalculate_metrics, recalculate_cpu_mark_metrics, import_passmark, import_entities)
- `apps/api/dealbrain_api/tasks/baseline.py` - Fixed 1 task (load_ruleset)

**Pattern Used**: Followed working pattern from `apps/api/dealbrain_api/tasks/valuation.py:145-169`

**Testing**: [To be verified after container restart]

**Commit**: [To be added after commit]
