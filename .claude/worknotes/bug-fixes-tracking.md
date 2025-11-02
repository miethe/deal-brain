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

**Commit**: [To be added after commit]
