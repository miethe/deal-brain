# DELETE Endpoint 204 Response Fix - Context

**Date**: 2025-11-01

## Issue
API failed to start with `AssertionError: Status code 204 must not have a response body` in `listings.py:351`.

## Root Cause
FastAPI's stricter validation in newer versions requires explicit `response_model=None` for endpoints returning HTTP 204 (No Content) status codes.

## Fix
Added `response_model=None` parameter to the DELETE endpoint decorator:

```python
@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
```

## Verification
- Rebuilt Docker container without cache
- API started successfully
- Confirmed no errors in logs

## Commit
`0e1cf35` - fix(api): add response_model=None to DELETE endpoint for HTTP 204 compliance
