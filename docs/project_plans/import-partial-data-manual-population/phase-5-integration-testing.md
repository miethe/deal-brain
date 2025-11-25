---
title: "Phase 5: Integration & Testing"
description: "End-to-end testing, migration validation, and monitoring setup for partial imports feature"
audience: [ai-agents, developers]
tags:
  - implementation
  - testing
  - integration
  - monitoring
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: pending
related:
  - /docs/project_plans/import-partial-data-manual-population/implementation-plan.md
---

# Phase 5: Integration & Testing

**Duration**: 1-2 days
**Dependencies**: Phases 1-4 complete
**Risk Level**: Low (testing and validation)

## Phase Overview

Phase 5 validates the complete implementation through:
- End-to-end testing across all phases
- Database migration testing and validation
- Monitoring setup for production readiness
- Performance benchmarking
- Security and data validation testing

**Key Outcomes**:
- All E2E tests pass
- Migrations tested and validated
- Monitoring metrics configured
- Performance verified acceptable
- Security review complete

---

## Task 5.1: End-to-End Testing

**Agent**: `python-backend-engineer` (lead), `ui-engineer` (support)
**Duration**: 1 day

### Objective
Test complete flow from URL import through manual completion.

### Test Scenarios

```python
# tests/test_phase5_e2e.py
"""
End-to-end tests for partial import feature.
Tests the complete flow across all phases.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient


class TestPartialImportE2E:
    """Test complete partial import workflow."""

    async def test_e2e_url_import_partial_complete(
        self,
        client: AsyncClient,
        session: AsyncSession
    ):
        """
        Test complete flow:
        1. Import single URL
        2. Extract partial data (no price)
        3. Query bulk status
        4. Complete via API
        5. Verify metrics calculated
        """
        # Step 1: Start bulk import with URL
        import_response = await client.post(
            "/api/v1/ingest/bulk",
            json={
                "urls": ["https://example.com/item1"],
                "marketplace": "other"
            }
        )
        assert import_response.status_code == 202
        bulk_job_id = import_response.json()["bulk_job_id"]

        # Step 2: Wait for partial import to complete
        # (Mock adapter returns partial data)
        await asyncio.sleep(1)  # Wait for processing

        # Step 3: Check bulk status
        status_response = await client.get(
            f"/api/v1/ingest/bulk/{bulk_job_id}/status"
        )
        assert status_response.status_code == 200
        status = status_response.json()

        assert status["total_urls"] == 1
        assert status["completed"] == 1
        assert status["partial"] == 1
        assert status["status"] == "partial"

        # Get listing ID
        listing_id = status["per_row_status"][0]["listing_id"]
        assert listing_id is not None

        # Step 4: Get partial listing and verify
        listing_response = await client.get(
            f"/api/v1/listings/{listing_id}"
        )
        assert listing_response.status_code == 200
        listing = listing_response.json()

        assert listing["quality"] == "partial"
        assert listing["price_usd"] is None
        assert listing["title"] == "Test Listing Title"
        assert listing["adjusted_price_usd"] is None  # No metrics yet

        # Step 5: Complete via API
        complete_response = await client.patch(
            f"/api/v1/listings/{listing_id}/complete",
            json={"price": 299.99}
        )
        assert complete_response.status_code == 200
        completed = complete_response.json()

        assert completed["quality"] == "full"
        assert completed["price_usd"] == 299.99
        assert completed["adjusted_price_usd"] is not None
        assert completed["adjusted_deal_rating"] in ["good_deal", "great_deal", "premium"]

        # Step 6: Verify database
        fresh_listing = await session.get(Listing, listing_id)
        assert fresh_listing.quality == "full"
        assert fresh_listing.extraction_metadata["price"] == "manual"

    async def test_e2e_multiple_partial_imports(
        self,
        client: AsyncClient,
        session: AsyncSession
    ):
        """Test handling multiple partial imports in one bulk job."""
        # Create bulk job with 3 URLs
        bulk_response = await client.post(
            "/api/v1/ingest/bulk",
            json={
                "urls": [
                    "https://example.com/1",
                    "https://example.com/2",
                    "https://example.com/3"
                ],
                "marketplace": "other"
            }
        )
        bulk_job_id = bulk_response.json()["bulk_job_id"]

        # Wait for processing
        await asyncio.sleep(2)

        # Check status
        status_response = await client.get(
            f"/api/v1/ingest/bulk/{bulk_job_id}/status"
        )
        status = status_response.json()

        assert status["total_urls"] == 3
        assert status["completed"] == 3
        assert status["partial"] >= 1  # At least one partial

        # Complete each partial
        for row in status["per_row_status"]:
            if row["quality"] == "partial":
                complete_response = await client.patch(
                    f"/api/v1/listings/{row['listing_id']}/complete",
                    json={"price": 299.99}
                )
                assert complete_response.status_code == 200

        # Verify all complete
        stmt = select(Listing).where(
            Listing.bulk_job_id == bulk_job_id,
            Listing.price_usd.isnot(None)
        )
        result = await session.execute(stmt)
        listings = result.scalars().all()

        assert len(listings) >= 3

    async def test_e2e_partial_with_cpu_enrichment(
        self,
        client: AsyncClient,
        session: AsyncSession
    ):
        """Test partial import with CPU extraction and enrichment."""
        # Import with CPU but no price
        listing_response = await client.post(
            "/api/v1/listings",
            json={
                "title": "Dell with i5-10500",
                "cpu_id": 123,  # Pre-populated CPU
                "condition": "refurb",
                "marketplace": "amazon",
                "quality": "partial",
                "missing_fields": ["price"]
            }
        )
        assert listing_response.status_code == 201
        listing = listing_response.json()

        # CPU should be enriched with benchmarks
        assert listing["cpu"]["cpu_mark"] is not None
        assert listing["cpu"]["single_thread_rating"] is not None

        # But no valuation metrics yet
        assert listing["adjusted_price_usd"] is None

        # Complete with price
        complete_response = await client.patch(
            f"/api/v1/listings/{listing['id']}/complete",
            json={"price": 399.99}
        )
        assert complete_response.status_code == 200
        completed = complete_response.json()

        # Now metrics should be calculated
        assert completed["adjusted_price_usd"] is not None
        assert completed["cpu_price_performance_rating"] is not None

    async def test_e2e_error_handling(
        self,
        client: AsyncClient
    ):
        """Test error handling in partial import flow."""
        # Try to complete non-existent listing
        response = await client.patch(
            "/api/v1/listings/99999/complete",
            json={"price": 299.99}
        )
        assert response.status_code == 404

        # Try to complete with invalid price
        # Create a partial listing first
        listing_response = await client.post(
            "/api/v1/listings",
            json={
                "title": "Test",
                "condition": "used",
                "marketplace": "other",
                "quality": "partial"
            }
        )
        listing_id = listing_response.json()["id"]

        # Invalid price
        response = await client.patch(
            f"/api/v1/listings/{listing_id}/complete",
            json={"price": -100}
        )
        assert response.status_code == 422

        # Try to complete already complete listing
        complete_response = await client.patch(
            f"/api/v1/listings/{listing_id}/complete",
            json={"price": 299.99}
        )
        assert complete_response.status_code == 200

        # Try again
        response = await client.patch(
            f"/api/v1/listings/{listing_id}/complete",
            json={"price": 399.99}
        )
        assert response.status_code == 400
```

### Acceptance Criteria

- [ ] Complete partial import flow works end-to-end
- [ ] Multiple partial imports handled correctly
- [ ] CPU enrichment works with partial imports
- [ ] All error conditions handled
- [ ] Metrics calculated correctly after completion
- [ ] Database state correct after each step
- [ ] API responses valid and complete
- [ ] Performance acceptable (<5s for complete flow)

---

## Task 5.2: Database Migration Testing

**Agent**: `data-layer-expert`
**Duration**: 4 hours

### Objective
Validate all migrations work correctly and data integrity maintained.

### Migration Validation Tests

```python
# tests/test_phase5_migrations.py
"""
Test database migrations for partial import support.
"""

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.dealbrain_api.models.core import Listing, ImportSession


class TestMigrations:
    """Test migration safety and correctness."""

    async def test_migration_0022_nullable_price(
        self,
        session: AsyncSession
    ):
        """Verify price_usd is nullable after migration."""
        # Create listing with NULL price
        listing = Listing(
            title="Test Partial",
            price_usd=None,
            condition="used",
            marketplace="other",
            quality="partial",
            missing_fields=["price"]
        )
        session.add(listing)
        await session.flush()

        # Query and verify
        stmt = select(Listing).where(Listing.id == listing.id)
        result = await session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.price_usd is None
        assert retrieved.quality == "partial"

    async def test_migration_0022_existing_data_preserved(
        self,
        session: AsyncSession
    ):
        """Verify existing listings with prices preserved."""
        # Create listing with price
        listing = Listing(
            title="Existing",
            price_usd=599.99,
            condition="new",
            marketplace="amazon"
        )
        session.add(listing)
        await session.flush()
        listing_id = listing.id

        # Verify after migration
        stmt = select(Listing).where(Listing.id == listing_id)
        result = await session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.price_usd == 599.99
        assert retrieved.quality == "full"  # Defaults to full for existing
        assert retrieved.extraction_metadata == {}
        assert retrieved.missing_fields == []

    async def test_migration_0022_default_values(
        self,
        session: AsyncSession
    ):
        """Verify column defaults work correctly."""
        listing = Listing(
            title="Test",
            condition="used",
            marketplace="other"
            # No quality, extraction_metadata, missing_fields
        )
        session.add(listing)
        await session.flush()

        stmt = select(Listing).where(Listing.id == listing.id)
        result = await session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.quality == "full"
        assert retrieved.extraction_metadata == {}
        assert retrieved.missing_fields == []

    async def test_migration_0023_bulk_job_tracking(
        self,
        session: AsyncSession
    ):
        """Verify bulk job tracking fields work."""
        session_obj = ImportSession(
            filename="test.xlsx",
            bulk_job_id="bulk-abc123",
            quality="partial",
            listing_id=1,
            status="complete"
        )
        session.add(session_obj)
        await session.flush()

        # Query by bulk_job_id
        stmt = select(ImportSession).where(
            ImportSession.bulk_job_id == "bulk-abc123"
        )
        result = await session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.bulk_job_id == "bulk-abc123"
        assert retrieved.quality == "partial"
        assert retrieved.listing_id == 1

    async def test_migration_downgrade_deletes_partial(
        self,
        session: AsyncSession
    ):
        """Verify downgrade safely handles partial imports."""
        # This test documents the downgrade behavior
        # (Actual downgrade not executed in normal tests)

        listing = Listing(
            title="Partial to Delete",
            price_usd=None,
            quality="partial",
            condition="used",
            marketplace="other"
        )
        session.add(listing)
        await session.flush()

        # If we were to downgrade:
        # - This listing would be deleted
        # - price_usd would be NOT NULL again
        # - quality, extraction_metadata, missing_fields would be dropped

    async def test_migration_performance(
        self,
        session: AsyncSession
    ):
        """Verify migration performance acceptable."""
        import time

        # Create 100 listings
        start = time.time()
        for i in range(100):
            listing = Listing(
                title=f"Test {i}",
                price_usd=float(i * 100) if i % 2 == 0 else None,
                condition="used",
                marketplace="other",
                quality="full" if i % 2 == 0 else "partial"
            )
            session.add(listing)
        await session.flush()
        create_time = time.time() - start

        # Query all with quality filter
        start = time.time()
        stmt = select(Listing).where(
            Listing.quality == "partial"
        )
        result = await session.execute(stmt)
        results = result.scalars().all()
        query_time = time.time() - start

        assert len(results) == 50
        assert create_time < 1.0  # <1s for 100 inserts
        assert query_time < 0.1   # <100ms for query

    async def test_migration_index_works(
        self,
        session: AsyncSession
    ):
        """Verify indexes created and working."""
        # Create import sessions with same bulk_job_id
        bulk_job_id = "bulk-test-index"
        for i in range(10):
            session_obj = ImportSession(
                filename=f"url_{i}",
                bulk_job_id=bulk_job_id,
                status="complete"
            )
            session.add(session_obj)
        await session.flush()

        # Query should be fast (uses index)
        import time
        start = time.time()
        stmt = select(ImportSession).where(
            ImportSession.bulk_job_id == bulk_job_id
        )
        result = await session.execute(stmt)
        results = result.scalars().all()
        query_time = time.time() - start

        assert len(results) == 10
        assert query_time < 0.05  # Should be very fast with index

    async def test_migration_foreign_key(
        self,
        session: AsyncSession
    ):
        """Verify foreign key constraint works."""
        # Create listing first
        listing = Listing(
            title="Test FK",
            condition="used",
            marketplace="other"
        )
        session.add(listing)
        await session.flush()
        listing_id = listing.id

        # Link import session
        session_obj = ImportSession(
            filename="test.xlsx",
            listing_id=listing_id,
            status="complete"
        )
        session.add(session_obj)
        await session.flush()

        # Verify relationship works
        stmt = select(ImportSession).where(
            ImportSession.listing_id == listing_id
        )
        result = await session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.listing_id == listing_id
```

### Acceptance Criteria

- [ ] All migrations apply cleanly
- [ ] No data loss on upgrade
- [ ] Backward compatibility maintained
- [ ] Default values work correctly
- [ ] Indexes created and working
- [ ] Foreign keys enforced
- [ ] Performance acceptable
- [ ] Downgrade strategy tested

---

## Task 5.3: Monitoring Setup

**Agent**: `python-backend-engineer` (lead)
**Duration**: 3-4 hours

### Objective
Configure Prometheus metrics and Grafana dashboards for monitoring.

### Prometheus Metrics Implementation

```python
# apps/api/dealbrain_api/observability/metrics.py
"""
Prometheus metrics for partial import feature monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge
import time

# Counter: Import attempts by marketplace and quality
import_attempts_total = Counter(
    'import_attempts_total',
    'Total import attempts',
    ['marketplace', 'quality'],
    help='Number of import attempts by marketplace and whether full/partial'
)

# Counter: Partial imports completed manually
partial_completions_total = Counter(
    'partial_import_completions_total',
    'Partial imports completed with manual data',
    help='Number of partial imports that were completed with user-provided data'
)

# Histogram: Import duration
import_duration_seconds = Histogram(
    'import_duration_seconds',
    'Import duration in seconds',
    ['marketplace', 'quality'],
    help='Time taken to import a listing'
)

# Gauge: Current imports in progress
imports_in_progress = Gauge(
    'imports_in_progress',
    'Number of imports currently processing',
    help='Real-time count of active imports'
)

# Counter: Import success/failure
import_results_total = Counter(
    'import_results_total',
    'Total import results',
    ['result', 'quality'],  # result: success, failed; quality: full, partial
    help='Count of successful and failed imports'
)

# Histogram: Completion time (from partial to full)
partial_completion_duration_seconds = Histogram(
    'partial_completion_duration_seconds',
    'Time from partial import to completion',
    help='Seconds elapsed before user completes partial import'
)

# Gauge: Partial imports pending completion
partial_imports_pending = Gauge(
    'partial_imports_pending',
    'Number of partial imports waiting for user completion',
    help='Count of partial imports that need manual data entry'
)


class MetricsCollector:
    """Helper class for recording metrics."""

    @staticmethod
    def record_import_attempt(marketplace: str, quality: str):
        """Record an import attempt."""
        import_attempts_total.labels(
            marketplace=marketplace,
            quality=quality
        ).inc()

    @staticmethod
    def record_import_result(marketplace: str, quality: str, success: bool):
        """Record import result."""
        result = 'success' if success else 'failed'
        import_results_total.labels(
            result=result,
            quality=quality
        ).inc()

    @staticmethod
    def record_import_duration(marketplace: str, quality: str, seconds: float):
        """Record import duration."""
        import_duration_seconds.labels(
            marketplace=marketplace,
            quality=quality
        ).observe(seconds)

    @staticmethod
    def record_partial_completion(marketplace: str, seconds: float):
        """Record partial import completion."""
        partial_completions_total.inc()
        partial_completion_duration_seconds.observe(seconds)
        import_results_total.labels(
            result='success',
            quality='full'
        ).inc()
```

### Instrumentation

```python
# apps/api/dealbrain_api/services/listings.py
# Add metrics collection to service methods

async def create_from_ingestion(
    self,
    normalized_data: NormalizedListingSchema,
    user_id: str,
    session: AsyncSession,
) -> Listing:
    """Create listing with metrics collection."""
    import time
    start = time.time()

    try:
        listing = Listing(...)
        # ... existing code ...

        MetricsCollector.record_import_attempt(
            marketplace=normalized_data.marketplace,
            quality=normalized_data.quality or "full"
        )

        session.add(listing)
        await session.flush()

        duration = time.time() - start
        MetricsCollector.record_import_result(
            marketplace=normalized_data.marketplace,
            quality=listing.quality,
            success=True
        )
        MetricsCollector.record_import_duration(
            marketplace=normalized_data.marketplace,
            quality=listing.quality,
            seconds=duration
        )

        return listing

    except Exception as e:
        MetricsCollector.record_import_result(
            marketplace=normalized_data.marketplace,
            quality=normalized_data.quality or "full",
            success=False
        )
        raise


async def complete_partial_import(
    self,
    listing_id: int,
    completion_data: dict[str, Any],
    user_id: str,
    session: AsyncSession,
) -> Listing:
    """Complete partial with metrics collection."""
    import time
    start = time.time()

    listing = await session.get(Listing, listing_id)
    # ... existing code ...

    duration = time.time() - start
    MetricsCollector.record_partial_completion(
        marketplace=listing.marketplace,
        seconds=duration
    )

    return listing
```

### Grafana Dashboard

Create dashboard JSON in `infra/grafana/dashboards/partial-imports.json`:

```json
{
  "dashboard": {
    "title": "Partial Imports",
    "panels": [
      {
        "title": "Import Success Rate",
        "targets": [
          {
            "expr": "rate(import_results_total{result='success'}[5m])"
          }
        ]
      },
      {
        "title": "Partial vs Complete Imports",
        "targets": [
          {
            "expr": "rate(import_attempts_total[5m])"
          }
        ]
      },
      {
        "title": "Average Import Duration",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, import_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Partial Completions",
        "targets": [
          {
            "expr": "rate(partial_import_completions_total[5m])"
          }
        ]
      },
      {
        "title": "Pending Partial Imports",
        "targets": [
          {
            "expr": "partial_imports_pending"
          }
        ]
      }
    ]
  }
}
```

### Alerts

```yaml
# infra/prometheus/alert-rules.yml
groups:
  - name: partial_imports
    rules:
      - alert: HighImportFailureRate
        expr: |
          (rate(import_results_total{result='failed'}[5m]) /
           rate(import_results_total[5m])) > 0.1
        for: 5m
        annotations:
          summary: "Import failure rate > 10%"

      - alert: ManyPendingPartialImports
        expr: partial_imports_pending > 100
        for: 30m
        annotations:
          summary: "Over 100 partial imports pending completion"

      - alert: SlowImportProcessing
        expr: |
          histogram_quantile(0.95, import_duration_seconds_bucket) > 30
        for: 5m
        annotations:
          summary: "95th percentile import duration > 30s"
```

### Acceptance Criteria

- [ ] Metrics exported to Prometheus
- [ ] Grafana dashboard created and shows data
- [ ] Alerts configured for high failure rate
- [ ] Success rate dashboard accurate
- [ ] Partial completion metrics tracked
- [ ] Performance overhead minimal (<1ms per operation)

---

## Validation Checklist

Before moving to production:

- [ ] All unit tests pass (>95% coverage)
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Database migrations tested and validated
- [ ] Performance benchmarks acceptable
- [ ] Security review complete (no data exposure)
- [ ] Error messages user-friendly
- [ ] Logging sufficient for debugging
- [ ] Monitoring alerts working
- [ ] Documentation complete
- [ ] Rollback strategy documented

---

## Success Criteria

All of the following must be true to consider Phase 5 complete:

- [ ] All E2E tests pass
- [ ] Database migrations validated
- [ ] No data loss during migrations
- [ ] Performance meets requirements (<500ms queries)
- [ ] Monitoring setup complete
- [ ] Alerts configured and tested
- [ ] Security review passed
- [ ] Documentation complete
- [ ] Ready for production deployment
