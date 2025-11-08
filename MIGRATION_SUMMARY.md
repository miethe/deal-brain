# Database Migrations for Partial Import Support

## Summary

Successfully created and tested two database migrations to support the partial import feature in Phase 1:

### Migration 0025: Listing Model Changes
**File**: `/mnt/containers/deal-brain/apps/api/alembic/versions/0025_partial_import_support.py`

**Changes**:
1. Made `listing.price_usd` nullable to allow partial imports without price data
2. Added `listing.quality` column (String(20), default='full') to track data completeness
3. Added `listing.extraction_metadata` column (JSON) for field provenance tracking
4. Added `listing.missing_fields` column (JSON) to list fields requiring manual entry
5. Created indexes for efficient filtering:
   - `idx_listing_quality` on `quality`
   - `idx_listing_quality_created` on `quality, created_at`

**Use Cases**:
- Creating listings with missing price data from extraction failures
- Tracking which fields were extracted vs manually entered
- Filtering partial imports for manual completion workflow

**Downgrade Strategy**:
- **WARNING**: Deletes all partial imports (price_usd IS NULL)
- Drops new columns and indexes
- Restores price_usd NOT NULL constraint
- Data loss is documented in migration comments

### Migration 0026: ImportSession Bulk Tracking
**File**: `/mnt/containers/deal-brain/apps/api/alembic/versions/0026_bulk_job_tracking.py`

**Changes**:
1. Added `import_session.bulk_job_id` column (String(36), indexed) to group bulk imports
2. Added `import_session.quality` column (String(20)) to track per-import data quality
3. Added `import_session.listing_id` column (Integer, ForeignKey) to link sessions to listings
4. Added `import_session.completed_at` column (DateTime(timezone=True)) for completion tracking
5. Created indexes for efficient queries:
   - `idx_import_session_bulk_job_id` on `bulk_job_id`
   - `idx_import_session_bulk_job_status` on `bulk_job_id, status`
   - `idx_import_session_listing_id` on `listing_id`

**Use Cases**:
- Tracking multiple URL imports under a single bulk job ID
- Querying bulk job status and progress
- Linking import sessions to created listings for audit trails
- Filtering imports by quality (full vs partial)

**Foreign Key Behavior**:
- `listing_id` uses `ON DELETE SET NULL` to preserve import history even if listing is deleted

## Model Updates

Updated `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`:

### Listing Model
```python
# Partial Import Support (Phase 1)
price_usd: Mapped[float | None] = mapped_column(nullable=True)  # Now nullable
quality: Mapped[str] = mapped_column(String(20), nullable=False, default="full", server_default="full")
extraction_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
missing_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
```

### ImportSession Model
```python
# Bulk Job Tracking (Phase 1.2)
bulk_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
quality: Mapped[str | None] = mapped_column(String(20), nullable=True)
listing_id: Mapped[int | None] = mapped_column(ForeignKey("listing.id", ondelete="SET NULL"), nullable=True)
completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

## Testing

Created comprehensive test suite in `/mnt/containers/deal-brain/tests/test_migrations_partial.py`:

**Test Coverage** (12 tests, all passing):
- ✅ Listing with NULL price_usd creation
- ✅ Default quality='full' for existing listings
- ✅ extraction_metadata field provenance tracking
- ✅ missing_fields tracking
- ✅ Filtering partial vs full listings
- ✅ Bulk job grouping by bulk_job_id
- ✅ ImportSession quality tracking
- ✅ listing_id foreign key relationship
- ✅ completed_at timestamp tracking
- ✅ Efficient bulk job status queries
- ✅ End-to-end partial import workflow
- ✅ Bulk job summary aggregation

**Test Results**:
```
tests/test_migrations_partial.py::TestMigration0025PartialImport::test_listing_price_usd_nullable PASSED
tests/test_migrations_partial.py::TestMigration0025PartialImport::test_listing_quality_default PASSED
tests/test_migrations_partial.py::TestMigration0025PartialImport::test_listing_extraction_metadata PASSED
tests/test_migrations_partial.py::TestMigration0025PartialImport::test_listing_missing_fields PASSED
tests/test_migrations_partial.py::TestMigration0025PartialImport::test_partial_vs_full_listings PASSED
tests/test_migrations_partial.py::TestMigration0026BulkJobTracking::test_import_session_bulk_job_id PASSED
tests/test_migrations_partial.py::TestMigration0026BulkJobTracking::test_import_session_quality PASSED
tests/test_migrations_partial.py::TestMigration0026BulkJobTracking::test_import_session_listing_id PASSED
tests/test_migrations_partial.py::TestMigration0026BulkJobTracking::test_import_session_completed_at PASSED
tests/test_migrations_partial.py::TestMigration0026BulkJobTracking::test_bulk_job_status_queries PASSED
tests/test_migrations_partial.py::TestMigrationIntegration::test_end_to_end_partial_import_workflow PASSED
tests/test_migrations_partial.py::TestMigrationIntegration::test_bulk_job_summary_query PASSED

12 passed in 1.59s
```

## Migration Status

**Current State**: Both migrations applied successfully
```bash
$ poetry run alembic current
0026 (head)
```

**Upgrade/Downgrade Tested**:
- ✅ Upgrade 0024 → 0025 → 0026
- ✅ Downgrade 0026 → 0025
- ✅ Downgrade 0025 → 0024
- ✅ Re-upgrade to head

## Schema Validation

The migrations align with the `NormalizedListingSchema` in `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/ingestion.py`:

```python
class NormalizedListingSchema(DealBrainModel):
    price: Decimal | None = Field(None, ...)  # Nullable price
    quality: str = Field(default="full", pattern=r"^(full|partial)$")
    extraction_metadata: dict[str, str] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
```

## Next Steps

The database schema is now ready for Phase 1 implementation:

1. **Task 1.3**: Update ListingsService to handle partial imports
2. **Task 1.4**: Create manual completion UI for partial listings
3. **Task 1.5**: Implement bulk import tracking with bulk_job_id

## Files Changed

1. `/mnt/containers/deal-brain/apps/api/alembic/versions/0025_partial_import_support.py` (new)
2. `/mnt/containers/deal-brain/apps/api/alembic/versions/0026_bulk_job_tracking.py` (new)
3. `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py` (modified)
4. `/mnt/containers/deal-brain/tests/test_migrations_partial.py` (new)

## Performance Considerations

**Indexes Created**:
- Listings can be efficiently filtered by quality
- Partial listings can be sorted by creation date for manual completion workflow
- Bulk jobs can be queried efficiently by bulk_job_id and status
- Import sessions can be linked to listings for audit trails

**Query Patterns Supported**:
```sql
-- Find all partial imports for manual completion
SELECT * FROM listing WHERE quality = 'partial' ORDER BY created_at DESC;

-- Get bulk job status
SELECT status, quality, COUNT(*)
FROM import_session
WHERE bulk_job_id = 'uuid-here'
GROUP BY status, quality;

-- Find listings created from a specific import session
SELECT l.*
FROM listing l
JOIN import_session i ON i.listing_id = l.id
WHERE i.bulk_job_id = 'uuid-here';
```

## Success Criteria Verification

✅ Both migrations created with proper revision chain (0024 → 0025 → 0026)
✅ Migrations apply without errors
✅ Can create listing with price_usd=NULL
✅ Existing listings get quality='full' by default
✅ ImportSession can track bulk jobs
✅ All 12 tests pass
✅ Downgrade works (with documented data loss warning)
