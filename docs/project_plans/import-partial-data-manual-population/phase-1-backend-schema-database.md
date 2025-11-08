---
title: "Phase 1: Backend Schema & Database Changes"
description: "Update schema validation, apply database migrations, and adapter changes to support nullable prices and partial imports"
audience: [ai-agents, developers]
tags:
  - implementation
  - backend
  - database
  - schema
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: in-progress
related:
  - /docs/project_plans/import-partial-data-manual-population/implementation-plan.md
---

# Phase 1: Backend Schema & Database Changes

**Duration**: 2-3 days
**Dependencies**: None (can start immediately)
**Risk Level**: Medium (database migration requires careful testing)

## Phase Overview

Phase 1 establishes the foundation for partial imports by updating the schema to accept listings without prices, creating database migrations for new nullable fields, and modifying adapters to gracefully handle extraction failures.

**Key Outcomes**:
- NormalizedListingSchema accepts price=None
- Database supports nullable price_usd and quality tracking
- Adapters set quality="partial" when price extraction fails
- All migrations tested and validated

---

## Task 1.1: Update NormalizedListingSchema

**Agent**: `python-backend-engineer`
**File**: `packages/core/dealbrain_core/schemas/ingestion.py`
**Duration**: 2-3 hours

### Objective
Update schema validation to support partial imports and track data extraction quality.

### Changes Required

1. Update `validate_minimum_data()` validator to only require title
2. Add `quality` field (full/partial)
3. Add `extraction_metadata` field (dict tracking field sources)
4. Add `missing_fields` field (list of fields needing manual entry)

### Implementation

```python
class NormalizedListingSchema(DealBrainModel):
    # Existing fields unchanged
    title: str = Field(...)  # REQUIRED
    price: Decimal | None = Field(None, ...)  # OPTIONAL (already set)

    # NEW FIELDS
    quality: str = Field(
        default="full",
        pattern=r"^(full|partial)$",
        description="Data completeness indicator"
    )
    extraction_metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Field provenance tracking: {field_name: 'extracted'|'manual'|'extraction_failed'}"
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="List of fields requiring manual entry"
    )

    @field_validator("price")
    @classmethod
    def validate_minimum_data(cls, price: Decimal | None, info) -> Decimal | None:
        """Only require title - price is fully optional."""
        if price is None:
            title = info.data.get("title")
            if not title or not str(title).strip():
                raise ValueError("Title is required for all imports")
        return price
```

### Acceptance Criteria

- [ ] Schema validates with `price=None` and `title="Test"`
- [ ] Schema rejects with `price=None` and `title=None`
- [ ] `quality` defaults to "full"
- [ ] `extraction_metadata` defaults to empty dict
- [ ] `missing_fields` defaults to empty list
- [ ] All existing tests pass
- [ ] Schema can be serialized/deserialized correctly

### Testing

```python
# tests/test_schemas.py
def test_normalized_listing_schema_optional_price():
    schema = NormalizedListingSchema(
        title="Test Listing",
        price=None,
        condition="used",
        marketplace="other"
    )
    assert schema.price is None
    assert schema.quality == "full"
    assert schema.extraction_metadata == {}
    assert schema.missing_fields == []

def test_normalized_listing_schema_rejects_no_title():
    with pytest.raises(ValueError, match="Title is required"):
        NormalizedListingSchema(
            title=None,
            price=None,
            condition="used",
            marketplace="other"
        )

def test_normalized_listing_schema_partial():
    schema = NormalizedListingSchema(
        title="Test",
        price=None,
        quality="partial",
        missing_fields=["price"],
        extraction_metadata={"title": "extracted", "price": "extraction_failed"}
    )
    assert schema.quality == "partial"
    assert "price" in schema.missing_fields
```

---

## Task 1.2: Database Migration - Nullable Price

**Agent**: `data-layer-expert`
**File**: `apps/api/alembic/versions/0022_partial_import_support.py`
**Duration**: 3-4 hours

### Objective
Make `listings.price_usd` nullable and add quality tracking fields to the Listing model.

### Critical Decision

This is an **irreversible migration** if partial imports exist in production. We need a rollback strategy:
- Downgrade only possible in non-production environments
- In production, rollback requires manual data review
- Use feature flag (Phase 6) for gradual rollout to minimize risk

### Migration Script

```python
"""Partial import support: nullable price and quality tracking

Revision ID: 0022
Revises: 0021
Create Date: 2025-11-08
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # 1. Make price_usd nullable
    op.alter_column(
        'listing',
        'price_usd',
        existing_type=sa.Float(),
        nullable=True
    )

    # 2. Add quality column (full | partial)
    op.add_column(
        'listing',
        sa.Column('quality', sa.String(20), nullable=False, server_default='full')
    )

    # 3. Add extraction_metadata JSON for field provenance tracking
    op.add_column(
        'listing',
        sa.Column('extraction_metadata', sa.JSON(), nullable=False, server_default='{}')
    )

    # 4. Add missing_fields JSON array for tracking incomplete fields
    op.add_column(
        'listing',
        sa.Column('missing_fields', sa.JSON(), nullable=False, server_default='[]')
    )


def downgrade():
    # WARNING: This will DELETE partial imports if they exist
    op.execute("DELETE FROM listing WHERE price_usd IS NULL")

    op.drop_column('listing', 'missing_fields')
    op.drop_column('listing', 'extraction_metadata')
    op.drop_column('listing', 'quality')

    op.alter_column(
        'listing',
        'price_usd',
        existing_type=sa.Float(),
        nullable=False
    )
```

### Model Update

Update `apps/api/dealbrain_api/models/core.py`:

```python
class Listing(Base, TimestampMixin):
    # ... existing fields ...

    price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # NEW FIELDS
    quality: Mapped[str] = mapped_column(String(20), default="full")
    extraction_metadata: Mapped[dict] = mapped_column(JSON, default={})
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=[])
```

### Acceptance Criteria

- [ ] Migration runs successfully in dev environment
- [ ] Migration runs successfully in staging environment
- [ ] Can create listing with `price_usd=NULL`
- [ ] Existing listings have `quality='full'` after migration
- [ ] Downgrade tested in isolated environment (deletes partial imports)
- [ ] No data loss for listings with prices
- [ ] Schema validation works with nullable price
- [ ] Performance impact <10ms on queries

### Testing

```bash
# Apply migration
make migrate

# Test in Python shell
poetry run python
>>> from apps.api.dealbrain_api.models.core import Listing
>>> from apps.api.dealbrain_api.db import session_scope
>>> async with session_scope() as session:
...     listing = Listing(
...         title="Test",
...         price_usd=None,
...         condition="used",
...         marketplace="other",
...         quality="partial"
...     )
...     session.add(listing)
...     await session.commit()
...     assert listing.price_usd is None
```

### Migration Validation Tests

```python
# tests/test_migrations.py
async def test_migration_0022_nullable_price(session):
    """Verify price_usd column is nullable after migration."""
    # Should not raise
    listing = Listing(
        title="Test",
        price_usd=None,
        condition="used",
        marketplace="other"
    )
    session.add(listing)
    await session.flush()
    assert listing.price_usd is None

async def test_migration_0022_quality_tracking(session):
    """Verify quality and tracking fields added."""
    listing = Listing(
        title="Test",
        price_usd=None,
        quality="partial",
        extraction_metadata={"title": "extracted"},
        missing_fields=["price"]
    )
    session.add(listing)
    await session.flush()
    assert listing.quality == "partial"
    assert listing.missing_fields == ["price"]

async def test_migration_0022_existing_data(session):
    """Verify existing listings default to quality='full'."""
    # Create a listing with price (pre-migration pattern)
    listing = Listing(
        title="Existing Listing",
        price_usd=299.99,
        condition="used",
        marketplace="other"
    )
    session.add(listing)
    await session.commit()

    # Refresh and verify defaults applied
    stmt = select(Listing).where(Listing.id == listing.id)
    result = await session.execute(stmt)
    refreshed = result.scalar_one()

    assert refreshed.quality == "full"
    assert refreshed.extraction_metadata == {}
    assert refreshed.missing_fields == []
```

---

## Task 1.3: Update Adapter Base Class

**Agent**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/adapters/base.py`
**Duration**: 2-3 hours

### Objective
Remove price requirement from adapter validation and set quality indicators when price extraction fails.

### Changes

```python
class BaseAdapter(ABC):
    def _validate_response(self, data: dict[str, Any]) -> None:
        """
        Validate minimum viable data - only title required.
        Sets quality indicators and tracking metadata.
        """

        # BEFORE: required_fields = ["title", "price"]
        # AFTER: only title required
        required_fields = ["title"]

        missing = [f for f in required_fields if f not in data or not data[f]]

        if missing:
            raise AdapterException(
                AdapterError.INVALID_SCHEMA,
                f"Missing required fields: {', '.join(missing)}",
            )

        # Track extraction quality
        has_price = bool(data.get("price"))

        if not has_price:
            logger.warning(
                f"[{self.name}] No price extracted - will create partial import"
            )
            data["quality"] = "partial"
            data["missing_fields"] = ["price"]

            # Track what WAS extracted
            data["extraction_metadata"] = {
                k: "extracted"
                for k, v in data.items()
                if v and k not in ["quality", "missing_fields", "extraction_metadata"]
            }
            data["extraction_metadata"]["price"] = "extraction_failed"
        else:
            data["quality"] = "full"
            data["missing_fields"] = []
            data["extraction_metadata"] = {
                k: "extracted"
                for k, v in data.items()
                if v and k not in ["quality", "missing_fields", "extraction_metadata"]
            }
```

### Acceptance Criteria

- [ ] Adapter accepts response with title only
- [ ] Adapter sets `quality="partial"` when price missing
- [ ] Adapter sets `missing_fields=["price"]` when price missing
- [ ] Adapter tracks `extraction_metadata` correctly
- [ ] All existing adapter tests pass
- [ ] No breaking changes to adapter interface
- [ ] Partial imports logged as warnings

### Testing

```python
# tests/test_adapters.py
async def test_adapter_accepts_partial_data():
    """Test adapter gracefully handles missing price."""
    adapter = JsonLdAdapter()
    data = {
        "title": "Dell OptiPlex 7090",
        "condition": "refurb",
        "marketplace": "amazon",
        "price": None
    }

    # Should not raise
    adapter._validate_response(data)

    assert data["quality"] == "partial"
    assert "price" in data["missing_fields"]
    assert data["extraction_metadata"]["title"] == "extracted"
    assert data["extraction_metadata"]["price"] == "extraction_failed"

async def test_adapter_full_import():
    """Test adapter still works with complete data."""
    adapter = JsonLdAdapter()
    data = {
        "title": "Dell OptiPlex 7090",
        "price": 299.99,
        "condition": "refurb",
        "marketplace": "amazon"
    }

    adapter._validate_response(data)

    assert data["quality"] == "full"
    assert data["missing_fields"] == []
    assert data["extraction_metadata"]["price"] == "extracted"

async def test_adapter_rejects_no_title():
    """Test adapter still requires title."""
    adapter = JsonLdAdapter()
    data = {"price": 299.99}

    with pytest.raises(AdapterException):
        adapter._validate_response(data)
```

---

## Task 1.4: Update ImportSession Model

**Agent**: `data-layer-expert`
**File**: `apps/api/dealbrain_api/models/core.py`
**Duration**: 2 hours

### Objective
Add bulk job tracking and quality fields to ImportSession for linking related imports.

### Migration Script

Create `apps/api/alembic/versions/0023_bulk_job_tracking.py`:

```python
"""Bulk import job tracking

Revision ID: 0023
Revises: 0022
Create Date: 2025-11-08
"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add bulk job ID for linking related imports
    op.add_column(
        'import_session',
        sa.Column('bulk_job_id', sa.String(36), nullable=True, index=True)
    )

    # Add quality tracking
    op.add_column(
        'import_session',
        sa.Column('quality', sa.String(20), nullable=True)
    )

    # Add listing reference
    op.add_column(
        'import_session',
        sa.Column('listing_id', sa.Integer, sa.ForeignKey('listing.id'), nullable=True)
    )

    # Add completion timestamp
    op.add_column(
        'import_session',
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Add index for bulk job queries
    op.create_index('ix_import_session_bulk_job_id', 'import_session', ['bulk_job_id'])


def downgrade():
    op.drop_index('ix_import_session_bulk_job_id')
    op.drop_column('import_session', 'completed_at')
    op.drop_column('import_session', 'listing_id')
    op.drop_column('import_session', 'quality')
    op.drop_column('import_session', 'bulk_job_id')
```

### Model Update

Update `apps/api/dealbrain_api/models/core.py`:

```python
class ImportSession(Base, TimestampMixin):
    # ... existing fields ...

    # NEW FIELDS for bulk import tracking
    bulk_job_id: Mapped[str | None] = mapped_column(String(36), index=True)
    quality: Mapped[str | None] = mapped_column(String(20))
    listing_id: Mapped[int | None] = mapped_column(ForeignKey("listing.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

### Acceptance Criteria

- [ ] Migration runs successfully
- [ ] Can query ImportSession by bulk_job_id efficiently
- [ ] Can link ImportSession to created Listing
- [ ] All existing tests pass
- [ ] Index created successfully

### Testing

```python
# tests/test_migrations.py
async def test_migration_0023_bulk_tracking(session):
    """Verify bulk job tracking fields added."""
    import_session = ImportSession(
        filename="test.xlsx",
        upload_path="/tmp/test.xlsx",
        bulk_job_id="bulk-123",
        quality="partial",
        listing_id=1
    )
    session.add(import_session)
    await session.flush()

    # Query by bulk_job_id
    stmt = select(ImportSession).where(
        ImportSession.bulk_job_id == "bulk-123"
    )
    result = await session.execute(stmt)
    found = result.scalar_one()
    assert found.bulk_job_id == "bulk-123"
```

---

## Integration Testing for Phase 1

### Schema Integration Test

```python
# tests/test_phase1_integration.py
async def test_phase1_schema_to_model_flow():
    """Test complete flow: schema validation → model creation → persistence."""
    async with session_scope() as session:
        # Create schema
        normalized = NormalizedListingSchema(
            title="Test Listing",
            price=None,
            condition="used",
            marketplace="other",
            quality="partial",
            missing_fields=["price"],
            extraction_metadata={"title": "extracted", "price": "extraction_failed"}
        )

        # Create model
        listing = Listing(
            title=normalized.title,
            price_usd=normalized.price,
            quality=normalized.quality,
            missing_fields=normalized.missing_fields,
            extraction_metadata=normalized.extraction_metadata,
            condition=normalized.condition,
            marketplace=normalized.marketplace
        )

        session.add(listing)
        await session.flush()

        # Verify persistence
        stmt = select(Listing).where(Listing.id == listing.id)
        result = await session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.price_usd is None
        assert retrieved.quality == "partial"
        assert "price" in retrieved.missing_fields
```

### Migration Safety Test

```python
# tests/test_phase1_safety.py
async def test_no_data_loss_on_upgrade():
    """Verify existing data preserved during migration."""
    async with session_scope() as session:
        # Create listing with price (pre-migration)
        listing = Listing(
            title="Expensive PC",
            price_usd=1299.99,
            condition="new",
            marketplace="other"
        )
        session.add(listing)
        await session.flush()
        listing_id = listing.id

    # Run migration (simulated in test)
    # ...

    async with session_scope() as session:
        # Verify data intact
        stmt = select(Listing).where(Listing.id == listing_id)
        result = await session.execute(stmt)
        retrieved = result.scalar_one()

        assert retrieved.price_usd == 1299.99
        assert retrieved.quality == "full"  # Should default
```

---

## Rollback Strategy

If Phase 1 needs to be rolled back in production:

1. **Feature Flag Approach** (Recommended for Phase 6):
   - Disable partial import feature flag
   - Partial imports still exist in database but won't be created
   - Data remains intact, migrations persist

2. **Full Rollback** (Only in dev/staging):
   ```bash
   poetry run alembic downgrade -1
   poetry run alembic downgrade -1
   # Deletes partial imports and restores NOT NULL constraint
   ```

3. **Production Rollback** (If feature flag not available):
   - Keep migrations applied
   - Disable at application level (return 400 error if price=None)
   - Manual cleanup of partial imports later

---

## Success Criteria

All of the following must be true to consider Phase 1 complete:

- [ ] Schema accepts price=None and title required
- [ ] Migrations 0022 and 0023 apply cleanly
- [ ] No data loss for existing listings
- [ ] Adapters gracefully handle missing prices
- [ ] All tests pass (unit + integration)
- [ ] Performance impact minimal (<10ms)
- [ ] Rollback strategy documented and tested
- [ ] Ready to proceed to Phase 2
