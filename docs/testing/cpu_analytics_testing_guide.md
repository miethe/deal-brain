---
title: "CPU Analytics Testing Guide"
description: "Manual testing guide for CPU analytics service implementation"
audience: [developers, ai-agents]
tags: [testing, cpu-analytics, backend, service-layer]
created: 2025-11-05
updated: 2025-11-05
category: "test-documentation"
status: published
related:
  - /docs/project_plans/cpu-page-reskin-prd.md
---

# CPU Analytics Testing Guide

This guide provides manual testing procedures for the CPU Analytics service (Group 2 implementation).

## Overview

The CPU Analytics service (`CPUAnalyticsService`) provides methods to:
1. Calculate price targets from listing adjusted prices
2. Calculate performance value metrics ($/PassMark)
3. Update CPU analytics fields in the database
4. Recalculate metrics for all CPUs in batch

## Prerequisites

1. Running PostgreSQL database with:
   - CPU table populated with benchmark data
   - Listings table with active listings and adjusted_price_usd values
2. Python environment with deal-brain packages installed
3. Database connection configured in `.env`

## Test Scenarios

### Test 1: Calculate Price Targets

**Objective**: Verify price target calculation from listing prices

**Steps**:
```python
import asyncio
from apps.api.dealbrain_api.db import session_scope
from apps.api.dealbrain_api.services.cpu_analytics import CPUAnalyticsService

async def test():
    async with session_scope() as session:
        # Pick a CPU ID with active listings
        cpu_id = 1  # Replace with actual CPU ID

        result = await CPUAnalyticsService.calculate_price_targets(session, cpu_id)

        print(f"Sample Size: {result.sample_size}")
        print(f"Confidence: {result.confidence}")
        print(f"Good (avg): ${result.good:.2f}" if result.good else "Good: None")
        print(f"Great (avg-σ): ${result.great:.2f}" if result.great else "Great: None")
        print(f"Fair (avg+σ): ${result.fair:.2f}" if result.fair else "Fair: None")
        print(f"Std Dev: ${result.stddev:.2f}" if result.stddev else "Std Dev: None")

asyncio.run(test())
```

**Expected Results**:
- Sample size matches count of active listings with prices
- Confidence level:
  - `insufficient`: sample_size < 2
  - `low`: sample_size 2-4
  - `medium`: sample_size 5-9
  - `high`: sample_size >= 10
- good = average price
- great = max(average - stddev, 0)
- fair = average + stddev
- All prices are non-negative floats

**Edge Cases**:
- CPU with 0 listings → sample_size=0, confidence='insufficient', all prices None
- CPU with 1 listing → sample_size=1, confidence='insufficient', all prices None
- CPU with negative/null prices → filtered out, only valid prices counted

---

### Test 2: Calculate Performance Value

**Objective**: Verify $/PassMark calculation and percentile ranking

**Steps**:
```python
import asyncio
from apps.api.dealbrain_api.db import session_scope
from apps.api.dealbrain_api.services.cpu_analytics import CPUAnalyticsService

async def test():
    async with session_scope() as session:
        # Pick a CPU ID with benchmark scores and listings
        cpu_id = 1  # Replace with actual CPU ID

        result = await CPUAnalyticsService.calculate_performance_value(session, cpu_id)

        print(f"$/Single Mark: ${result.dollar_per_mark_single:.4f}" if result.dollar_per_mark_single else "$/Single Mark: None")
        print(f"$/Multi Mark: ${result.dollar_per_mark_multi:.4f}" if result.dollar_per_mark_multi else "$/Multi Mark: None")
        print(f"Percentile: {result.percentile:.1f}%" if result.percentile is not None else "Percentile: None")
        print(f"Rating: {result.rating}" if result.rating else "Rating: None")

asyncio.run(test())
```

**Expected Results**:
- dollar_per_mark_single = avg_price / cpu_mark_single
- dollar_per_mark_multi = avg_price / cpu_mark_multi
- Percentile range: 0-100 (0 = best value, 100 = worst value)
- Rating quartiles:
  - `excellent`: 0-25th percentile
  - `good`: 25-50th percentile
  - `fair`: 50-75th percentile
  - `poor`: 75-100th percentile

**Edge Cases**:
- CPU without benchmark scores → all fields None
- CPU without listings → all fields None
- CPU with listings but no prices → all fields None
- CPU with zero benchmark scores → division by zero handled, returns None

---

### Test 3: Update CPU Analytics

**Objective**: Verify analytics are persisted to database

**Steps**:
```python
import asyncio
from apps.api.dealbrain_api.db import session_scope
from apps.api.dealbrain_api.models.core import Cpu
from apps.api.dealbrain_api.services.cpu_analytics import CPUAnalyticsService

async def test():
    async with session_scope() as session:
        cpu_id = 1  # Replace with actual CPU ID

        # Update analytics
        await CPUAnalyticsService.update_cpu_analytics(session, cpu_id)
        await session.commit()

        # Verify fields populated
        cpu = await session.get(Cpu, cpu_id)

        print("\nPrice Target Fields:")
        print(f"  good: ${cpu.price_target_good:.2f}" if cpu.price_target_good else "  good: None")
        print(f"  great: ${cpu.price_target_great:.2f}" if cpu.price_target_great else "  great: None")
        print(f"  fair: ${cpu.price_target_fair:.2f}" if cpu.price_target_fair else "  fair: None")
        print(f"  sample_size: {cpu.price_target_sample_size}")
        print(f"  confidence: {cpu.price_target_confidence}")
        print(f"  stddev: ${cpu.price_target_stddev:.2f}" if cpu.price_target_stddev else "  stddev: None")
        print(f"  updated_at: {cpu.price_target_updated_at}")

        print("\nPerformance Value Fields:")
        print(f"  $/single: ${cpu.dollar_per_mark_single:.4f}" if cpu.dollar_per_mark_single else "  $/single: None")
        print(f"  $/multi: ${cpu.dollar_per_mark_multi:.4f}" if cpu.dollar_per_mark_multi else "  $/multi: None")
        print(f"  percentile: {cpu.performance_value_percentile:.1f}%" if cpu.performance_value_percentile else "  percentile: None")
        print(f"  rating: {cpu.performance_value_rating}")
        print(f"  updated_at: {cpu.performance_metrics_updated_at}")

asyncio.run(test())
```

**Expected Results**:
- All 12 analytics fields populated (or None if insufficient data)
- price_target_updated_at timestamp is recent
- performance_metrics_updated_at timestamp is recent
- Database commit successful
- Values match those from calculate methods

---

### Test 4: Recalculate All CPU Metrics

**Objective**: Verify batch recalculation works correctly

**Steps**:
```python
import asyncio
from apps.api.dealbrain_api.db import session_scope
from apps.api.dealbrain_api.services.cpu_analytics import CPUAnalyticsService

async def test():
    async with session_scope() as session:
        # Run batch recalculation
        summary = await CPUAnalyticsService.recalculate_all_cpu_metrics(session)

        print(f"\nRecalculation Summary:")
        print(f"  Total CPUs: {summary['total']}")
        print(f"  Successful: {summary['success']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Success Rate: {(summary['success']/summary['total']*100):.1f}%")

asyncio.run(test())
```

**Expected Results**:
- All CPUs in database processed
- Success count + error count = total count
- Errors are logged but don't stop processing
- Database transaction committed at end
- High success rate (>95% typically)

**Performance Notes**:
- Expected speed: ~1-5 CPUs/second depending on listing count
- For 1000 CPUs: ~3-10 minutes total
- Progress logged every 10 CPUs

---

## Verification Queries

After running tests, verify results with SQL:

```sql
-- Check CPUs with populated analytics
SELECT
    id,
    name,
    price_target_good,
    price_target_confidence,
    dollar_per_mark_multi,
    performance_value_rating
FROM cpu
WHERE price_target_updated_at IS NOT NULL
LIMIT 10;

-- Check confidence distribution
SELECT
    price_target_confidence,
    COUNT(*) as count
FROM cpu
WHERE price_target_updated_at IS NOT NULL
GROUP BY price_target_confidence
ORDER BY count DESC;

-- Check performance rating distribution
SELECT
    performance_value_rating,
    COUNT(*) as count
FROM cpu
WHERE performance_metrics_updated_at IS NOT NULL
GROUP BY performance_value_rating
ORDER BY count DESC;

-- Find CPUs with best value (lowest $/mark)
SELECT
    id,
    name,
    dollar_per_mark_multi,
    performance_value_percentile,
    performance_value_rating
FROM cpu
WHERE dollar_per_mark_multi IS NOT NULL
ORDER BY dollar_per_mark_multi ASC
LIMIT 10;
```

## Common Issues

### Issue: ModuleNotFoundError for dealbrain_core

**Cause**: Python packages not installed in editable mode

**Solution**:
```bash
poetry install
# or
pip install -e .
```

### Issue: No CPUs found with active listings

**Cause**: Database empty or listings not marked as active

**Solution**:
```bash
# Import sample data
poetry run python scripts/seed_sample_listings.py
# or
poetry run dealbrain-cli import path/to/workbook.xlsx
```

### Issue: All price targets return insufficient confidence

**Cause**: Listings missing adjusted_price_usd values

**Solution**:
```bash
# Recalculate listing valuations
poetry run python scripts/recalculate_all_metrics.py
```

### Issue: Performance value calculations return None

**Cause**: CPUs missing benchmark scores

**Solution**:
```bash
# Import PassMark benchmark data
poetry run python scripts/import_passmark_data.py data/passmark_cpus.csv
```

## Success Criteria

Implementation is successful if:

- ✅ All 5 schemas defined with proper types and descriptions
- ✅ calculate_price_targets() returns correct statistics
- ✅ calculate_performance_value() calculates percentiles correctly
- ✅ update_cpu_analytics() persists all fields
- ✅ recalculate_all_cpu_metrics() processes all CPUs
- ✅ Edge cases handled (no data, missing benchmarks, etc.)
- ✅ Comprehensive logging added
- ✅ Manual testing passes for sample CPUs

## Next Steps

After validation:
1. Integration with API endpoints (Group 3)
2. Frontend display of analytics (Group 4)
3. Background job scheduling for periodic recalculation
4. Performance optimization for large datasets
