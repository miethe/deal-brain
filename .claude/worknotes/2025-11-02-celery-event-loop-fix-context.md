# Celery AsyncIO Event Loop Fix - Context

**Date**: 2025-11-02

## Issue
Celery tasks failing with `RuntimeError: Task got Future attached to a different loop` when executing async database operations.

## Root Cause
Tasks used `asyncio.run()` which creates implicit event loops. In Celery forked worker processes, the global SQLAlchemy async engine remains attached to old event loops, causing conflicts when new tasks create new event loops.

## Fix
Replaced `asyncio.run()` with explicit event loop management pattern:
1. Create fresh event loop: `asyncio.new_event_loop()`
2. Dispose cached engine: `loop.run_until_complete(dispose_engine())`
3. Execute async function: `loop.run_until_complete(async_func())`
4. Cleanup in finally block: shutdown generators, close loop, reset state

## Files Modified
- `apps/api/dealbrain_api/tasks/admin.py` - Fixed 4 tasks
- `apps/api/dealbrain_api/tasks/baseline.py` - Fixed 1 task

## Pattern Reference
Followed working pattern from `apps/api/dealbrain_api/tasks/valuation.py:145-169`

## Verification
- Worker restarted successfully
- Tasks registered without errors
- No event loop errors in logs

## Commit
`8f93897` - fix(worker): resolve asyncio event loop conflicts in Celery tasks
