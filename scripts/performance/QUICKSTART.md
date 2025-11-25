# Performance Testing Quick Start

Get up and running with catalog API performance testing in 5 minutes.

## Prerequisites

```bash
# 1. Ensure API is running
make up    # Full Docker Compose stack
# OR
make api   # Local API server only

# 2. Verify API is accessible
curl http://localhost:8000/health
```

## Run Tests (Simple)

```bash
# Run all performance tests (20 iterations each)
./scripts/performance/run_performance_tests.sh

# Run with verbose output to see progress
./scripts/performance/run_performance_tests.sh --verbose
```

## Run Tests (Detailed)

```bash
# Test specific entity type
poetry run python scripts/performance/catalog_performance_test.py --entity-type cpu

# More runs for better accuracy
poetry run python scripts/performance/catalog_performance_test.py --runs 50

# Test against different environment
poetry run python scripts/performance/catalog_performance_test.py --base-url http://staging:8000
```

## Analyze Results

```bash
# Analyze test results
poetry run python scripts/performance/analyze_results.py performance-results.json

# View summary
cat performance-results.json | jq '.summary'

# View failed tests only
cat performance-results.json | jq '.results[] | select(.passed == false)'

# View P95 latencies
cat performance-results.json | jq '.results[] | {scenario, p95_ms, target_ms, passed}'
```

## Expected Output

### Console Output

```
================================================================================
CATALOG API PERFORMANCE VALIDATION
================================================================================
Base URL: http://localhost:8000
Runs per test: 20
Timestamp: 2025-11-14T10:30:00

================================================================================
Testing: CPU_PATCH_SINGLE_FIELD
Description: Update CPU with single field change
Target P95: < 500ms
================================================================================

Results:
  P50: 45.2ms
  P95: 78.5ms (target: < 500ms)
  P99: 95.3ms
  Min: 38.1ms
  Max: 102.7ms
  Mean: 52.3ms
  StdDev: 15.2ms
  Failed runs: 0/20

✅ PASS

================================================================================
SUMMARY
================================================================================

Target: P95 < 500ms (3/3 passed)
--------------------------------------------------------------------------------
✅ CPU_PATCH_SINGLE_FIELD                       P95:    78.5ms (target: 500ms)
✅ CPU_PUT_FULL_UPDATE                          P95:   125.3ms (target: 500ms)
✅ GPU_PATCH_SINGLE_FIELD                       P95:    82.1ms (target: 500ms)

================================================================================
Overall: 10/10 tests passed
✅ All performance targets met!
================================================================================

✅ Results saved to: performance-results.json
```

### Analysis Output

```
================================================================================
PERFORMANCE ANALYSIS
================================================================================

Summary:
  Total Tests: 10
  Passed: 10
  Failed: 0

================================================================================
✅ PASSED TESTS
================================================================================
  CPU_PATCH_SINGLE_FIELD                         P95:    78.5ms (margin: 84.3%)
  CPU_PUT_FULL_UPDATE                            P95:   125.3ms (margin: 74.9%)
  CPU_DELETE_NO_LISTINGS                         P95:   235.5ms (margin: 76.5%)
  GPU_PATCH_SINGLE_FIELD                         P95:    82.1ms (margin: 83.6%)
  ...

================================================================================
RECOMMENDED ACTIONS
================================================================================

✅ No critical issues or warnings detected!
   All performance targets are met with healthy margins.

================================================================================
```

## What Gets Tested

### Update Operations (Target: P95 < 500ms)
- CPU PATCH: Single field update
- CPU PUT: Full entity replacement
- GPU PATCH: Single field update
- GPU PUT: Full entity replacement
- Profile PATCH: Update weights

### Delete Operations (Target: P95 < 1s)
- CPU DELETE: Entity with 0 listings
- CPU DELETE CHECK: Entity with 100 listings
- CPU DELETE CHECK: Entity with 1000 listings

### List Operations (Target: P95 < 2s)
- CPU LIST: All CPUs
- GPU LIST: All GPUs
- Profile LIST: All profiles
- RamSpec LIST: With filters
- StorageProfile LIST: With filters

### Detail Operations (Target: P95 < 1.5s)
- CPU DETAIL: Get CPU + associated listings

## Troubleshooting

### API Not Running

```
❌ Cannot connect to API: [Errno 111] Connection refused

Solution:
  make up    # Start Docker Compose stack
  make api   # Or run API locally
```

### No Entities Found

```
⚠️  Skipping CPU_PATCH_SINGLE_FIELD: No CPU entities found

Solution:
  make seed  # Seed database with sample data
```

### Tests Running Slowly

Slow tests may indicate:
- Database needs indexing
- Connection pooling issues
- N+1 query problems
- Missing cache layer

Run with `--verbose` to see individual request timings.

## Next Steps

1. **Document Results**: Update `/home/user/deal-brain/docs/testing/performance-validation-results.md`
2. **Address Issues**: If tests fail, investigate with OpenTelemetry spans
3. **Optimize**: Follow recommendations from analyze_results.py
4. **Monitor**: Set up continuous performance monitoring

## Files Created

- `catalog_performance_test.py` - Main test script
- `run_performance_tests.sh` - Quick runner script
- `analyze_results.py` - Results analyzer
- `sample-results.json` - Example results
- `README.md` - Detailed documentation
- `QUICKSTART.md` - This file

## Documentation

- **Performance Results**: `/home/user/deal-brain/docs/testing/performance-validation-results.md`
- **PRD Reference**: `/home/user/deal-brain/docs/project_plans/entity-detail-views-v2-prd.md` (Phase 8, Task TEST-004)

## Questions?

See `scripts/performance/README.md` for comprehensive documentation.
