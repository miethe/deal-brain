---
title: "Phase 2: Backend API & Services"
description: "Build API endpoints and services for completing partial imports and polling bulk job status"
audience: [ai-agents, developers]
tags:
  - implementation
  - backend
  - api
  - services
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: pending
related:
  - /docs/project_plans/import-partial-data-manual-population/implementation-plan.md
  - /docs/project_plans/import-partial-data-manual-population/phase-1-backend-schema-database.md
---

# Phase 2: Backend API & Services

**Duration**: 2-3 days
**Dependencies**: Phase 1 complete (migrations applied)
**Risk Level**: Low (pure business logic)

## Phase Overview

Phase 2 implements the business logic and API endpoints for partial imports. This includes:

1. Updating ListingsService to support creating listings without prices
2. Adding a new method to complete partial imports
3. Creating API endpoints for completion and bulk status polling
4. Comprehensive service and integration testing

**Key Outcomes**:
- ListingsService supports nullable prices
- Completion endpoint updates partial listings with new data
- Bulk status endpoint provides real-time progress tracking
- All services fully tested with edge cases

---

## Task 2.1: Update ListingsService for Partial Imports

**Agent**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/services/listings.py`
**Duration**: 4-5 hours

### Objective
Support creating listings without price, skip metrics calculation when price is missing.

### Method 1: Create from Ingestion

Update or create the `create_from_ingestion` method:

```python
async def create_from_ingestion(
    self,
    normalized_data: NormalizedListingSchema,
    user_id: str,
    session: AsyncSession,
) -> Listing:
    """
    Create listing from normalized ingestion data.
    Supports partial imports - price may be None.

    Args:
        normalized_data: Validated ingestion schema
        user_id: User creating the listing
        session: Database session

    Returns:
        Created listing (may be partial with no price)

    Note:
        - Metrics calculation skipped if price is None
        - quality field set based on price presence
        - extraction_metadata and missing_fields preserved
    """
    listing = Listing(
        title=normalized_data.title,
        price_usd=normalized_data.price,  # May be None
        condition=normalized_data.condition,
        marketplace=normalized_data.marketplace,
        vendor_item_id=normalized_data.vendor_item_id,
        manufacturer=normalized_data.manufacturer,
        model_number=normalized_data.model_number,
        form_factor=normalized_data.form_factor,
        quality=normalized_data.quality or (
            "partial" if normalized_data.price is None else "full"
        ),
        extraction_metadata=normalized_data.extraction_metadata or {},
        missing_fields=normalized_data.missing_fields or [],
        # ... other fields ...
    )

    # Only calculate metrics if price exists
    if listing.price_usd is not None:
        await self._apply_valuation_and_scoring(listing, session)
    else:
        logger.info(
            f"Listing '{listing.title}' created without price - "
            "metrics deferred until completion"
        )

    session.add(listing)
    await session.flush()
    return listing
```

### Method 2: Complete Partial Import (NEW)

Add new method to ListingsService:

```python
async def complete_partial_import(
    self,
    listing_id: int,
    completion_data: dict[str, Any],
    user_id: str,
    session: AsyncSession,
) -> Listing:
    """
    Complete a partial import by providing missing fields.

    This method is called by the manual population modal when user
    provides missing data (typically price). It updates the listing,
    recalculates metrics, and marks as complete.

    Args:
        listing_id: Listing to complete
        completion_data: Dict with missing fields (e.g., {"price": 299.99})
        user_id: User completing the import
        session: Database session

    Returns:
        Updated listing with metrics calculated

    Raises:
        ValueError: If listing not found or not partial
        ValueError: If price invalid

    Example:
        >>> updated = await service.complete_partial_import(
        ...     listing_id=123,
        ...     completion_data={"price": 299.99},
        ...     user_id="user123",
        ...     session=session
        ... )
        >>> assert updated.quality == "full"
    """
    # Fetch listing
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise ValueError(f"Listing {listing_id} not found")

    # Verify listing is partial
    if listing.quality != "partial":
        raise ValueError(
            f"Listing {listing_id} is not partial (quality={listing.quality})"
        )

    # Update fields from completion data
    if "price" in completion_data:
        price_value = completion_data["price"]

        # Validate price
        if not isinstance(price_value, (int, float)):
            raise ValueError(f"Price must be numeric, got {type(price_value)}")
        if price_value <= 0:
            raise ValueError(f"Price must be positive, got {price_value}")

        listing.price_usd = float(price_value)

        # Track manual entry in metadata
        if not listing.extraction_metadata:
            listing.extraction_metadata = {}
        listing.extraction_metadata["price"] = "manual"

        logger.info(f"Completed partial listing {listing_id}: price={price_value}")

    # Remove completed fields from missing_fields
    listing.missing_fields = [
        f for f in (listing.missing_fields or [])
        if f not in completion_data
    ]

    # Update quality if all required fields present
    if not listing.missing_fields and listing.price_usd is not None:
        listing.quality = "full"
        logger.info(f"Listing {listing_id} now complete (quality=full)")
    else:
        # Still partial if missing other fields
        listing.quality = "partial"

    # Calculate metrics now that we have price
    if listing.price_usd is not None and listing.quality == "full":
        await self._apply_valuation_and_scoring(listing, session)

    await session.flush()
    return listing
```

### Acceptance Criteria

- [ ] Can create listing with price=None
- [ ] Metrics not calculated when price=None
- [ ] Can complete partial listing with price
- [ ] Metrics calculated after completion
- [ ] extraction_metadata tracks "manual" for user-entered fields
- [ ] quality updated to "full" after completion (if no other missing fields)
- [ ] Validates price is positive number
- [ ] Raises ValueError for invalid listing_id
- [ ] Raises ValueError if listing already complete
- [ ] All existing service tests pass
- [ ] No breaking changes to existing methods

### Testing

```python
# tests/test_listings_service.py
async def test_create_partial_listing_no_metrics(session):
    """Test partial listing created without metrics."""
    service = ListingsService()
    normalized = NormalizedListingSchema(
        title="Dell OptiPlex",
        price=None,
        condition="refurb",
        marketplace="amazon",
        quality="partial",
        missing_fields=["price"],
        extraction_metadata={"title": "extracted", "price": "extraction_failed"}
    )

    listing = await service.create_from_ingestion(
        normalized_data=normalized,
        user_id="user123",
        session=session
    )

    assert listing.price_usd is None
    assert listing.quality == "partial"
    assert listing.adjusted_price_usd is None  # No metrics calculated
    assert "price" in listing.missing_fields

async def test_complete_partial_import_with_price(session):
    """Test completing partial import with price."""
    # Create partial listing
    listing = Listing(
        title="Test PC",
        price_usd=None,
        quality="partial",
        condition="used",
        marketplace="other",
        missing_fields=["price"],
        extraction_metadata={"title": "extracted", "price": "extraction_failed"}
    )
    session.add(listing)
    await session.flush()
    listing_id = listing.id

    # Complete it
    service = ListingsService()
    updated = await service.complete_partial_import(
        listing_id=listing_id,
        completion_data={"price": 299.99},
        user_id="user123",
        session=session
    )

    assert updated.price_usd == 299.99
    assert updated.quality == "full"
    assert updated.extraction_metadata["price"] == "manual"
    assert updated.missing_fields == []
    assert updated.adjusted_price_usd is not None  # Metrics calculated

async def test_complete_partial_import_invalid_price():
    """Test completion rejects invalid prices."""
    service = ListingsService()
    listing = Listing(title="Test", price_usd=None, quality="partial")

    with pytest.raises(ValueError, match="Price must be positive"):
        await service.complete_partial_import(
            listing_id=1,
            completion_data={"price": -100},
            user_id="user123",
            session=session
        )

async def test_complete_already_complete_listing():
    """Test completion rejects non-partial listings."""
    listing = Listing(
        title="Complete",
        price_usd=299.99,
        quality="full",
        condition="used",
        marketplace="other"
    )
    session.add(listing)
    await session.flush()

    service = ListingsService()
    with pytest.raises(ValueError, match="is not partial"):
        await service.complete_partial_import(
            listing_id=listing.id,
            completion_data={"price": 399.99},
            user_id="user123",
            session=session
        )

async def test_complete_nonexistent_listing():
    """Test completion rejects nonexistent listing."""
    service = ListingsService()
    with pytest.raises(ValueError, match="not found"):
        await service.complete_partial_import(
            listing_id=99999,
            completion_data={"price": 299.99},
            user_id="user123",
            session=session
        )
```

---

## Task 2.2: Create Completion API Endpoint

**Agent**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/api/listings.py`
**Duration**: 2-3 hours

### Objective
Add PATCH endpoint for completing partial imports with validation and error handling.

### Endpoint: `PATCH /api/v1/listings/{listing_id}/complete`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import session_dependency
from ..services.listings import ListingsService
from dealbrain_core.schemas.listings import ListingSchema

router = APIRouter()


class CompletePartialImportRequest(BaseModel):
    """Request schema for completing a partial import."""

    price: float = Field(
        ...,
        gt=0,
        description="Listing price in USD (must be positive)"
    )

    class Config:
        json_schema_extra = {
            "example": {"price": 299.99}
        }


class CompletePartialImportResponse(BaseModel):
    """Response schema for completed listing."""

    id: int
    title: str
    price_usd: float | None
    quality: str
    missing_fields: list[str]
    adjusted_price_usd: float | None
    adjusted_deal_rating: str | None


@router.patch(
    "/api/v1/listings/{listing_id}/complete",
    response_model=CompletePartialImportResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_partial_import(
    listing_id: int,
    request: CompletePartialImportRequest,
    session: AsyncSession = Depends(session_dependency),
    # current_user: dict = Depends(get_current_user),  # TODO: Add auth
) -> CompletePartialImportResponse:
    """
    Complete a partial import by providing missing fields.

    This endpoint allows users to fill in missing data (typically price)
    for listings that were partially imported from URL extraction. After
    completion, the listing's quality is updated to "full" and metrics
    are calculated.

    Args:
        listing_id: ID of the partial listing to complete
        request: Completion data (at minimum, price)
        session: Database session
        current_user: Authenticated user (TODO)

    Returns:
        Updated listing with metrics calculated and quality="full"

    Raises:
        404: Listing not found
        400: Listing is not partial or validation failed
        422: Invalid request data

    Example:
        ```
        PATCH /api/v1/listings/123/complete
        Content-Type: application/json

        {"price": 299.99}

        Response:
        {
            "id": 123,
            "title": "Dell OptiPlex 7090",
            "price_usd": 299.99,
            "quality": "full",
            "missing_fields": [],
            "adjusted_price_usd": 349.99,
            "adjusted_deal_rating": "great_deal"
        }
        ```
    """
    service = ListingsService()

    try:
        updated_listing = await service.complete_partial_import(
            listing_id=listing_id,
            completion_data=request.model_dump(),
            user_id="system",  # TODO: Use current_user["id"]
            session=session,
        )
        await session.commit()

        return CompletePartialImportResponse(
            id=updated_listing.id,
            title=updated_listing.title,
            price_usd=updated_listing.price_usd,
            quality=updated_listing.quality,
            missing_fields=updated_listing.missing_fields or [],
            adjusted_price_usd=updated_listing.adjusted_price_usd,
            adjusted_deal_rating=updated_listing.adjusted_deal_rating,
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        logger.exception(f"Unexpected error completing partial import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete import"
        )
```

### Acceptance Criteria

- [ ] Endpoint validates price is positive
- [ ] Endpoint returns 400 if listing not partial
- [ ] Endpoint returns 404 if listing not found
- [ ] Endpoint returns 200 with updated listing on success
- [ ] Metrics calculated after completion
- [ ] Response includes all required fields
- [ ] Proper error messages returned
- [ ] Integration test passes
- [ ] OpenAPI schema generation works

### Testing

```python
# tests/test_api_listings.py
async def test_complete_partial_import_endpoint_success(client, session):
    """Test successful completion of partial import."""
    # Create partial listing
    listing = Listing(
        title="Test PC",
        price_usd=None,
        quality="partial",
        condition="used",
        marketplace="other",
        missing_fields=["price"]
    )
    session.add(listing)
    await session.commit()

    # Complete via API
    response = await client.patch(
        f"/api/v1/listings/{listing.id}/complete",
        json={"price": 299.99}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["price_usd"] == 299.99
    assert data["quality"] == "full"
    assert data["missing_fields"] == []

async def test_complete_partial_import_not_found(client):
    """Test completion returns 404 for nonexistent listing."""
    response = await client.patch(
        "/api/v1/listings/99999/complete",
        json={"price": 299.99}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

async def test_complete_partial_import_invalid_price(client):
    """Test completion rejects invalid price."""
    response = await client.patch(
        "/api/v1/listings/1/complete",
        json={"price": -100}
    )

    assert response.status_code == 422  # Validation error

async def test_complete_already_complete_listing(client, session):
    """Test completion rejects already complete listings."""
    listing = Listing(
        title="Complete",
        price_usd=299.99,
        quality="full",
        condition="used",
        marketplace="other"
    )
    session.add(listing)
    await session.commit()

    response = await client.patch(
        f"/api/v1/listings/{listing.id}/complete",
        json={"price": 399.99}
    )

    assert response.status_code == 400
    assert "not partial" in response.json()["detail"].lower()
```

---

## Task 2.3: Create Bulk Import Status Endpoint

**Agent**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/api/ingestion.py`
**Duration**: 4-5 hours

### Objective
Add status polling endpoint for bulk imports with pagination and quality indicators.

### Schemas

```python
# apps/api/dealbrain_api/schemas/ingestion.py

class PerRowImportStatus(BaseModel):
    """Status of a single URL in bulk import job."""
    url: str
    status: str  # queued, running, complete, failed
    listing_id: int | None = None
    quality: str | None = None  # full, partial
    error: str | None = None


class BulkIngestionStatusResponse(BaseModel):
    """Overall status of bulk import job."""
    bulk_job_id: str
    status: str  # running, complete, partial, failed
    total_urls: int
    completed: int
    success: int  # quality=full
    partial: int  # quality=partial
    failed: int
    running: int
    queued: int
    per_row_status: list[PerRowImportStatus]
    offset: int
    limit: int
    has_more: bool
```

### Endpoint: `GET /api/v1/ingest/bulk/{bulk_job_id}/status`

```python
from sqlalchemy import select, func
from fastapi import APIRouter, Query, Depends, HTTPException

router = APIRouter()


@router.get(
    "/api/v1/ingest/bulk/{bulk_job_id}/status",
    response_model=BulkIngestionStatusResponse
)
async def get_bulk_import_status(
    bulk_job_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(session_dependency),
) -> BulkIngestionStatusResponse:
    """
    Poll bulk import job status with pagination.

    Returns overall job status and per-URL details including
    quality indicators (full/partial) and listing references.

    This endpoint is called by the frontend import modal to track
    progress of bulk URL imports. The frontend polls every 2 seconds
    until status becomes "complete" or "failed".

    Args:
        bulk_job_id: Unique bulk job identifier
        offset: Pagination offset (default 0)
        limit: Pagination limit (default 20, max 100)
        session: Database session

    Returns:
        Bulk job status with per-row details

    Example:
        ```
        GET /api/v1/ingest/bulk/bulk-abc123/status?offset=0&limit=20

        Response:
        {
            "bulk_job_id": "bulk-abc123",
            "status": "running",
            "total_urls": 50,
            "completed": 30,
            "success": 28,
            "partial": 2,
            "failed": 0,
            "running": 20,
            "queued": 0,
            "per_row_status": [
                {
                    "url": "https://example.com/item1",
                    "status": "complete",
                    "listing_id": 123,
                    "quality": "full",
                    "error": null
                },
                {
                    "url": "https://example.com/item2",
                    "status": "complete",
                    "listing_id": 124,
                    "quality": "partial",
                    "error": null
                }
            ],
            "offset": 0,
            "limit": 20,
            "has_more": true
        }
        ```
    """
    # Query paginated ImportSession records for this bulk_job_id
    stmt = (
        select(ImportSession)
        .where(ImportSession.bulk_job_id == bulk_job_id)
        .offset(offset)
        .limit(limit)
        .order_by(ImportSession.created_at)
    )
    result = await session.execute(stmt)
    sessions = result.scalars().all()

    # Count by status and quality
    count_stmt = (
        select(
            ImportSession.status,
            ImportSession.quality,
            func.count()
        )
        .where(ImportSession.bulk_job_id == bulk_job_id)
        .group_by(ImportSession.status, ImportSession.quality)
    )
    count_result = await session.execute(count_stmt)
    counts = count_result.all()

    # Aggregate counts
    total_urls = sum(c[2] for c in counts)
    queued = sum(c[2] for c in counts if c[0] == "queued")
    running = sum(c[2] for c in counts if c[0] == "running")
    complete = sum(c[2] for c in counts if c[0] == "complete")
    partial = sum(c[2] for c in counts if c[1] == "partial" and c[0] == "complete")
    failed = sum(c[2] for c in counts if c[0] == "failed")

    # Determine overall status
    if queued + running > 0:
        overall_status = "running"
    elif failed == total_urls and total_urls > 0:
        overall_status = "failed"
    elif partial > 0:
        overall_status = "partial"
    else:
        overall_status = "complete" if total_urls > 0 else "queued"

    # Build per-row status
    per_row_status = [
        PerRowImportStatus(
            url=s.url or s.filename or "",
            status=s.status,
            listing_id=s.listing_id,
            quality=s.quality,
            error=s.conflicts_json.get("error") if s.conflicts_json else None
        )
        for s in sessions
    ]

    return BulkIngestionStatusResponse(
        bulk_job_id=bulk_job_id,
        status=overall_status,
        total_urls=total_urls,
        completed=complete + partial + failed,
        success=complete - partial,  # complete without partial
        partial=partial,
        failed=failed,
        running=running,
        queued=queued,
        per_row_status=per_row_status,
        offset=offset,
        limit=limit,
        has_more=len(sessions) == limit
    )
```

### Acceptance Criteria

- [ ] Endpoint returns correct aggregated counts
- [ ] Endpoint paginates per_row_status correctly
- [ ] Endpoint identifies partial imports via quality field
- [ ] Endpoint returns listing_id for completed imports
- [ ] Overall status determined correctly
- [ ] Integration test with 50+ URLs passes
- [ ] Performance acceptable (query <500ms for large jobs)

### Testing

```python
# tests/test_api_ingestion.py
async def test_bulk_import_status_empty_job(client, session):
    """Test status endpoint for nonexistent job."""
    response = await client.get(
        "/api/v1/ingest/bulk/nonexistent/status"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_urls"] == 0
    assert data["status"] == "queued"

async def test_bulk_import_status_running(client, session):
    """Test status endpoint with mixed statuses."""
    bulk_job_id = "test-bulk-123"

    # Create mixed import sessions
    for i in range(5):
        s = ImportSession(
            filename=f"url_{i}",
            upload_path=f"https://example.com/{i}",
            url=f"https://example.com/{i}",
            bulk_job_id=bulk_job_id,
            status="complete" if i < 3 else "running",
            quality="partial" if i == 1 else "full",
            listing_id=100 + i if i < 3 else None
        )
        session.add(s)
    await session.commit()

    # Query status
    response = await client.get(
        f"/api/v1/ingest/bulk/{bulk_job_id}/status?limit=10"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_urls"] == 5
    assert data["success"] == 2  # i=0, i=2 (full, complete)
    assert data["partial"] == 1  # i=1 (partial, complete)
    assert data["running"] == 2  # i=3, i=4
    assert data["status"] == "running"  # Because 2 still running
    assert len(data["per_row_status"]) == 5

async def test_bulk_import_status_pagination(client, session):
    """Test pagination works correctly."""
    bulk_job_id = "test-bulk-large"

    # Create 35 import sessions
    for i in range(35):
        s = ImportSession(
            filename=f"url_{i}",
            bulk_job_id=bulk_job_id,
            status="complete",
            quality="full",
            listing_id=100 + i
        )
        session.add(s)
    await session.commit()

    # Get first page
    response1 = await client.get(
        f"/api/v1/ingest/bulk/{bulk_job_id}/status?offset=0&limit=20"
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["per_row_status"]) == 20
    assert data1["has_more"] is True

    # Get second page
    response2 = await client.get(
        f"/api/v1/ingest/bulk/{bulk_job_id}/status?offset=20&limit=20"
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["per_row_status"]) == 15
    assert data2["has_more"] is False

async def test_bulk_import_status_all_complete(client, session):
    """Test status when all imports complete."""
    bulk_job_id = "test-bulk-done"

    for i in range(10):
        s = ImportSession(
            filename=f"url_{i}",
            bulk_job_id=bulk_job_id,
            status="complete",
            quality="full" if i % 2 == 0 else "partial",
            listing_id=100 + i
        )
        session.add(s)
    await session.commit()

    response = await client.get(
        f"/api/v1/ingest/bulk/{bulk_job_id}/status"
    )

    data = response.json()
    assert data["status"] == "partial"  # Some are partial
    assert data["total_urls"] == 10
    assert data["completed"] == 10
    assert data["running"] == 0
    assert data["queued"] == 0
```

---

## Integration Testing for Phase 2

### End-to-End Service Integration

```python
# tests/test_phase2_integration.py
async def test_e2e_create_and_complete_partial_import(session):
    """Test complete flow: create partial → complete → metrics calculated."""
    service = ListingsService()

    # Step 1: Create partial listing
    normalized = NormalizedListingSchema(
        title="Dell OptiPlex 7090",
        price=None,
        condition="refurb",
        marketplace="amazon",
        quality="partial",
        missing_fields=["price"]
    )

    listing = await service.create_from_ingestion(
        normalized_data=normalized,
        user_id="user123",
        session=session
    )

    assert listing.price_usd is None
    assert listing.quality == "partial"
    assert listing.adjusted_price_usd is None
    listing_id = listing.id

    # Step 2: Complete partial import
    completed = await service.complete_partial_import(
        listing_id=listing_id,
        completion_data={"price": 299.99},
        user_id="user123",
        session=session
    )

    assert completed.price_usd == 299.99
    assert completed.quality == "full"
    assert completed.adjusted_price_usd is not None
```

### API Integration Test

```python
# tests/test_phase2_api_integration.py
async def test_e2e_api_complete_partial_import(client, session):
    """Test API flow: create partial → call endpoint → verify update."""
    # Create partial listing
    listing = Listing(
        title="Test PC",
        price_usd=None,
        quality="partial",
        condition="used",
        marketplace="other"
    )
    session.add(listing)
    await session.commit()
    listing_id = listing.id

    # Call completion endpoint
    response = await client.patch(
        f"/api/v1/listings/{listing_id}/complete",
        json={"price": 299.99}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all fields updated
    assert data["id"] == listing_id
    assert data["price_usd"] == 299.99
    assert data["quality"] == "full"
    assert data["missing_fields"] == []
    assert data["adjusted_price_usd"] is not None

    # Verify database updated
    fresh_listing = await session.get(Listing, listing_id)
    assert fresh_listing.price_usd == 299.99
    assert fresh_listing.quality == "full"
```

---

## Success Criteria

All of the following must be true to consider Phase 2 complete:

- [ ] ListingsService supports creating listings with price=None
- [ ] ListingsService.complete_partial_import works end-to-end
- [ ] Completion endpoint validates input and handles errors
- [ ] Bulk status endpoint returns correct aggregations
- [ ] Pagination works for large bulk jobs (50+ URLs)
- [ ] All tests pass (unit + integration + API)
- [ ] OpenAPI schema correctly generated
- [ ] Performance acceptable (<500ms for bulk queries)
- [ ] Ready to proceed to Phase 3 (Frontend)
