# Performance Load Test Report - Collections Sharing

**Generated:** Not yet run

## Summary

Run the load test script to generate this report:

```bash
poetry run python scripts/load_test.py
```

This report will include:

- Collections endpoint load test results
- Public share page performance (cached and uncached)
- Share creation under load
- Database connection pool monitoring

## How to Run

1. Ensure API server is running on `http://localhost:8000`
2. Seed test data: `poetry run python scripts/seed_test_data.py`
3. Run load tests: `poetry run python scripts/load_test.py`
4. Review this generated report

## Performance Targets

| Test | Target p95 | Concurrent Users/Requests |
|------|-----------|---------------------------|
| Collections (100+ items) | < 200ms | 100 concurrent users |
| Public share (uncached) | < 1s | 500 concurrent requests |
| Public share (cached) | < 50ms | 500 concurrent requests |
| Share creation | < 500ms | 50 concurrent users |
| Connection pool | < 300ms | 200 concurrent queries |

## Expected Results

All tests should meet or exceed performance targets:

- ✓ Collections endpoint p95 < 200ms
- ✓ Public share uncached p95 < 1s
- ✓ Public share cached p95 < 50ms
- ✓ Share creation p95 < 500ms
- ✓ No connection pool exhaustion
