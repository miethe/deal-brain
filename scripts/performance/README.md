# Catalog API Performance Testing

Performance validation scripts for catalog CRUD operations.

## Quick Start

```bash
# Start the API
make up  # or make api

# Run performance tests
poetry run python scripts/performance/catalog_performance_test.py

# Run with verbose output
poetry run python scripts/performance/catalog_performance_test.py --verbose
```

## Performance Targets

| Operation | Target (P95) |
|-----------|--------------|
| Update (PUT/PATCH) | < 500ms |
| Delete with check | < 1s |
| List queries | < 2s |
| Detail view | < 1.5s |

## Usage

### Run All Tests

```bash
poetry run python scripts/performance/catalog_performance_test.py
```

### Test Specific Entity Type

```bash
# CPU endpoints only
poetry run python scripts/performance/catalog_performance_test.py --entity-type cpu

# GPU endpoints only
poetry run python scripts/performance/catalog_performance_test.py --entity-type gpu

# Profile endpoints only
poetry run python scripts/performance/catalog_performance_test.py --entity-type profile
```

### Customize Test Parameters

```bash
# More runs for better statistical significance
poetry run python scripts/performance/catalog_performance_test.py --runs 50

# Test against different environment
poetry run python scripts/performance/catalog_performance_test.py --base-url http://staging-api.example.com

# Save results to specific file
poetry run python scripts/performance/catalog_performance_test.py --output results/$(date +%Y%m%d)-perf.json
```

## Test Scenarios

### CPU Operations
- **PATCH single field**: Update CPU notes field
- **PUT full update**: Complete CPU entity replacement
- **DELETE (no listings)**: Delete CPU with zero usage
- **DELETE CHECK (100 listings)**: Attempt delete with 100 listing references
- **DELETE CHECK (1000 listings)**: Attempt delete with 1000 listing references
- **LIST all**: Fetch all CPUs
- **DETAIL with listings**: Get CPU + associated listings

### GPU Operations
- **PATCH single field**: Update GPU notes
- **PUT full update**: Complete GPU replacement
- **LIST all**: Fetch all GPUs

### Profile Operations
- **PATCH weights**: Update scoring profile weights
- **LIST all**: Fetch all profiles

### RAM Spec Operations
- **LIST with filter**: Fetch RAM specs with query filters

### Storage Profile Operations
- **LIST with filter**: Fetch storage profiles with query filters

## Output

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

...

================================================================================
SUMMARY
================================================================================

Target: P95 < 500ms (3/3 passed)
--------------------------------------------------------------------------------
✅ CPU_PATCH_SINGLE_FIELD                       P95:    78.5ms (target: 500ms)
✅ CPU_PUT_FULL_UPDATE                          P95:   125.3ms (target: 500ms)
✅ GPU_PATCH_SINGLE_FIELD                       P95:    82.1ms (target: 500ms)

Target: P95 < 1000ms (2/2 passed)
--------------------------------------------------------------------------------
✅ CPU_DELETE_NO_LISTINGS                       P95:   250.5ms (target: 1000ms)
✅ CPU_DELETE_WITH_LISTINGS_100                 P95:   485.2ms (target: 1000ms)

================================================================================
Overall: 5/5 tests passed
✅ All performance targets met!
================================================================================
```

### JSON Output

Results are automatically saved to `performance-results.json` (or custom file via `--output`):

```json
{
  "timestamp": "2025-11-14T10:30:00.000000",
  "base_url": "http://localhost:8000",
  "runs_per_test": 20,
  "results": [
    {
      "operation": "PATCH",
      "entity_type": "CPU",
      "scenario": "CPU_PATCH_SINGLE_FIELD",
      "p50_ms": 45.2,
      "p95_ms": 78.5,
      "p99_ms": 95.3,
      "min_ms": 38.1,
      "max_ms": 102.7,
      "mean_ms": 52.3,
      "stddev_ms": 15.2,
      "target_ms": 500.0,
      "passed": true,
      "runs": 20,
      "failed_runs": 0
    }
  ],
  "summary": {
    "total_tests": 5,
    "passed": 5,
    "failed": 0
  }
}
```

## Interpreting Results

### Performance Metrics

- **P50 (Median)**: 50% of requests completed in this time or less
- **P95**: 95% of requests completed in this time or less (our target metric)
- **P99**: 99% of requests completed in this time or less
- **Min/Max**: Fastest and slowest request times
- **Mean**: Average response time
- **StdDev**: Response time variability

### Pass/Fail Criteria

Tests pass when **P95 < Target**:
- ✅ **PASS**: P95 meets or exceeds target
- ❌ **FAIL**: P95 exceeds target threshold

### What to Do When Tests Fail

1. **Check Environment**: Ensure clean test environment (no other load)
2. **Database State**: Verify database has reasonable data volume
3. **Profile Code**: Use OpenTelemetry spans to identify bottlenecks
4. **Review Queries**: Check for N+1 queries, missing indexes
5. **Cache Analysis**: Verify caching is working as expected
6. **Connection Pooling**: Ensure database connections are properly pooled

## Optimization Tips

### Database Optimization
- Add indexes for frequently queried fields
- Use `select_related()` / `selectinload()` to avoid N+1 queries
- Consider query result caching for expensive operations

### API Optimization
- Implement response caching for read-heavy endpoints
- Use pagination for large result sets
- Add field selection to reduce payload size
- Consider async background processing for expensive operations

### Infrastructure
- Scale database vertically (more CPU/RAM)
- Add read replicas for read-heavy workloads
- Implement CDN for static content
- Use connection pooling (pgBouncer for PostgreSQL)

## Continuous Integration

### Add to CI Pipeline

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  pull_request:
    paths:
      - 'apps/api/**'
      - 'packages/core/**'

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Run performance tests
        run: poetry run python scripts/performance/catalog_performance_test.py
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: performance-results.json
```

## Documentation

Results and analysis documented in:
- `/home/user/deal-brain/docs/testing/performance-validation-results.md`

## Requirements

- Python 3.11+
- httpx (async HTTP client)
- Running API server (localhost:8000 or custom URL)

## Troubleshooting

### Cannot connect to API

```
❌ Cannot connect to API: [Errno 111] Connection refused
```

**Solution**: Start the API server:
```bash
make up    # Docker Compose stack
# OR
make api   # Local API server
```

### No entities found

```
⚠️  Skipping CPU_PATCH_SINGLE_FIELD: No CPU entities found
```

**Solution**: Seed the database:
```bash
make seed
# OR
poetry run dealbrain-cli import path/to/workbook.xlsx
```

### All runs failed

```
❌ All runs failed for CPU_PATCH_SINGLE_FIELD
```

**Solution**: Check API logs for errors:
```bash
docker-compose logs api
# OR
make logs
```

## Contributing

When adding new test scenarios:

1. Add scenario to `CatalogPerformanceTester.scenarios` list
2. Implement test method (e.g., `test_cpu_patch()`)
3. Update documentation with new scenario
4. Set appropriate performance target
5. Run tests to validate

## Related Documentation

- [Entity Detail Views PRD](/home/user/deal-brain/docs/project_plans/entity-detail-views-v2-prd.md)
- [Performance Validation Results](/home/user/deal-brain/docs/testing/performance-validation-results.md)
- [OpenTelemetry Integration](/home/user/deal-brain/docs/architecture/observability.md)
