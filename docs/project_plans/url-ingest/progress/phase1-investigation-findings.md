# Phase 1 Investigation Findings
**Date:** 2025-10-22
**Investigator:** Lead Architect
**Status:** Investigation Complete

---

## Executive Summary

Phase 1 investigation has **confirmed both root causes** and identified clear paths to resolution:

1. **Progress Bar Issue:** Frontend uses time-based estimation (`calculateProgress(elapsed)`), backend has NO progress tracking
2. **Field Population Issue:** Adapters extract `images` and `description`, but **Listing model lacks these fields**

Both issues are **straightforward to fix** with database migrations and code updates.

---

## Issue 1: Progress Bar Not Reflecting Real Backend Status

### Root Cause Confirmed

**Frontend Implementation (`ingestion-status-display.tsx`):**
```typescript
// Lines 202-216: Time-based progress calculation
function calculateProgress(elapsed: number): number {
  if (elapsed < 5) {
    return Math.round(15 + (elapsed / 5) * 35);  // 15-50%
  } else if (elapsed < 15) {
    return Math.round(50 + ((elapsed - 5) / 10) * 35);  // 50-85%
  } else if (elapsed < 30) {
    return Math.min(96, Math.round(85 + ((elapsed - 15) / 15) * 11));  // 85-96%
  } else {
    return Math.min(98, Math.round(96 + ((elapsed - 30) / 60) * 2));  // 96-98%
  }
}
```

**Problems:**
- Progress is purely time-based, not tied to actual backend status
- Never reaches 100% during polling (caps at 96-98%)
- Only shows 100% briefly after job completes (lines 112-140)
- User cannot distinguish "just started" vs "almost done" when both show ~50%

**Backend Implementation (`tasks/ingestion.py`):**
```python
# Lines 56-83: Status transitions
import_session.status = "running"  # Line 56
await session.flush()

# ... long-running work happens here (no progress updates) ...

import_session.status = "complete"  # Line 67
await session.commit()
```

**Problems:**
- Only 3 status states: `queued` → `running` → `complete`/`failed`
- No granular progress during execution
- ImportSession model has NO `progress_pct` field
- Frontend polls every 2s but gets same "running" status throughout

**Backend Models (`models/core.py`):**
```python
class ImportSession(Base, TimestampMixin):
    # ... existing fields ...
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    # NO progress_pct field ❌
```

### Recommendations

**Fix Approach:**
1. Add `progress_pct` field to ImportSession model (nullable Integer, 0-100)
2. Update Celery task to set progress at milestones:
   - 10%: Task started (status=running)
   - 40%: Adapter extraction complete
   - 60%: Normalization complete
   - 80%: Deduplication complete
   - 100%: Listing upserted (status=complete)
3. Update API response to include `progress_pct`
4. Update frontend to use real `progress_pct` from backend (with time-based fallback)

**Implementation Effort:** ~6 hours (Phase 2)
- Backend changes: 3h (migration, task updates, API response)
- Frontend changes: 2h (use real progress)
- Testing: 1h

---

## Issue 2: Incomplete Field Population

### Root Cause Confirmed

**NormalizedListingSchema (`schemas/ingestion.py`) - What Adapters Extract:**
```python
class NormalizedListingSchema(DealBrainModel):
    title: str                    # ✅ Extracted
    price: Decimal                # ✅ Extracted
    currency: str                 # ✅ Extracted
    condition: str                # ✅ Extracted
    images: list[str]             # ✅ Extracted (list of URLs)
    seller: str | None            # ✅ Extracted
    marketplace: str              # ✅ Extracted
    vendor_item_id: str | None    # ✅ Extracted
    cpu_model: str | None         # ✅ Extracted
    ram_gb: int | None            # ✅ Extracted
    storage_gb: int | None        # ✅ Extracted
    description: str | None       # ✅ Extracted
```

**Listing Model (`models/core.py`) - What Database Has:**
```python
class Listing(Base, TimestampMixin):
    title: Mapped[str]                      # ✅ Persisted
    price_usd: Mapped[float]                # ✅ Persisted
    condition: Mapped[str]                  # ✅ Persisted
    marketplace: Mapped[str]                # ✅ Persisted
    vendor_item_id: Mapped[str | None]      # ✅ Persisted
    seller: Mapped[str | None]              # ✅ Persisted
    manufacturer: Mapped[str | None]        # ⚠️ Available but NOT populated
    model_number: Mapped[str | None]        # ⚠️ Available but NOT populated
    notes: Mapped[str | None]               # ⚠️ Available but NOT mapped from description
    ram_gb: Mapped[int]                     # ⚠️ Available but NOT populated from normalized
    primary_storage_gb: Mapped[int]         # ⚠️ Available but NOT populated from normalized
    # MISSING FIELDS:
    # image_url: NOT DEFINED ❌
    # description: NOT DEFINED ❌
```

**IngestionService (`services/ingestion.py`) - What Gets Persisted:**
```python
# Lines 718-734: _create_listing() method
listing = Listing(
    title=data.title,                    # ✅ Mapped
    price_usd=float(data.price),         # ✅ Mapped
    condition=condition.value,           # ✅ Mapped
    marketplace=data.marketplace,        # ✅ Mapped
    vendor_item_id=data.vendor_item_id,  # ✅ Mapped
    seller=data.seller,                  # ✅ Mapped
    dedup_hash=dedup_hash,               # ✅ Computed
    # MISSING MAPPINGS:
    # image_url <- data.images[0] ❌ (field doesn't exist)
    # description <- data.description ❌ (field doesn't exist)
    # manufacturer <- parsed from title ❌ (not implemented)
    # model_number <- parsed from title ❌ (not implemented)
    # ram_gb <- data.ram_gb ❌ (not mapped)
    # primary_storage_gb <- data.storage_gb ❌ (not mapped)
)
```

### Identified Gaps

| Field in NormalizedListingSchema | Listing Model Field | Status | Action Required |
|----------------------------------|---------------------|--------|-----------------|
| `images: list[str]` | ❌ `image_url` | MISSING | Add field + migration |
| `description: str` | ❌ `description` | MISSING | Add field + migration |
| N/A (parse from title) | `manufacturer` | EXISTS, NOT POPULATED | Add parsing logic |
| N/A (parse from title) | `model_number` | EXISTS, NOT POPULATED | Add parsing logic |
| `ram_gb: int` | `ram_gb` | EXISTS, NOT MAPPED | Add mapping |
| `storage_gb: int` | `primary_storage_gb` | EXISTS, NOT MAPPED | Add mapping |
| `cpu_model: str` | `cpu_id` (FK) | PARTIAL | Enhance CPU linking |

### Recommendations

**Fix Approach:**

**Step 1: Add Missing Database Fields (Migration)**
```python
# Alembic migration
def upgrade():
    op.add_column('listing', sa.Column('image_url', sa.Text(), nullable=True))
    op.add_column('listing', sa.Column('description', sa.Text(), nullable=True))
```

**Step 2: Add Brand/Model Parsing in ListingNormalizer**
```python
def _parse_brand_model(self, title: str) -> dict[str, str | None]:
    """Parse brand and model from product title."""
    BRAND_PATTERNS = [
        r"^(MINISFORUM|Dell|HP|Lenovo|ASUS|Acer|MSI)\b",
    ]
    MODEL_PATTERNS = [
        r"(Venus\s+\w+)",      # MINISFORUM Venus NAB9
        r"(OptiPlex\s+\d+)",   # Dell OptiPlex 7090
    ]
    # ... regex matching logic ...
    return {"brand": brand, "model": model}
```

**Step 3: Update IngestionService._create_listing()**
```python
listing = Listing(
    # ... existing mappings ...
    image_url=data.images[0] if data.images else None,  # NEW
    description=data.description,                       # NEW
    manufacturer=brand_model["brand"],                  # NEW
    model_number=brand_model["model"],                  # NEW
    ram_gb=data.ram_gb or 0,                           # NEW
    primary_storage_gb=data.storage_gb or 0,           # NEW
)
```

**Implementation Effort:** ~8 hours (Phase 3)
- Migration: 1h
- Brand/model parsing: 3h (with tests)
- Field persistence: 2h
- Testing: 2h

---

## Additional Findings

### CPU Enrichment Already Works
The ListingNormalizer already canonicalizes CPU models via catalog lookup:
```python
# services/ingestion.py lines 399-428
cpu_canonical = await self._canonicalize_cpu(specs.get("cpu_model"))
```

This works correctly, but the `_create_listing()` method doesn't link the CPU to the listing. Need to add:
```python
if normalized.cpu_model:
    cpu = await self._find_or_create_cpu(normalized.cpu_model)
    if cpu:
        listing.cpu_id = cpu.id
```

### Raw Data IS Preserved
The `_store_raw_payload()` method saves the full NormalizedListingSchema to the `RawPayload` table:
```python
# services/ingestion.py lines 754-780
payload_dict = raw_data.model_dump(mode="json")
raw_payload = RawPayload(
    listing_id=listing.id,
    adapter_name=adapter_name,
    payload_json=payload_dict,
    # ...
)
```

This means we can:
1. Backfill missing fields from existing RawPayload data (if needed)
2. Re-process old imports after fixing field mappings

---

## Architectural Compliance

### Layered Architecture ✅
- Issue is in **service layer** (IngestionService), not domain logic
- Fix maintains layer boundaries: Services → Models
- No changes to adapter layer needed (already extracting data correctly)

### Async-First Backend ✅
- All database operations use `async/await`
- Migration is synchronous (Alembic standard)
- Service methods already use `session.flush()` correctly

### Backward Compatibility ✅
- New fields are nullable (safe migration)
- Existing listings won't break (NULL values acceptable)
- Frontend can handle missing fields gracefully

---

## Success Metrics

### Issue 1: Progress Bar
- [ ] Progress bar reaches 100% on successful imports
- [ ] Progress updates reflect real backend milestones
- [ ] No time-based estimation during polling
- [ ] Completion animation plays smoothly

### Issue 2: Field Population
- [ ] 100% of new listings have `title`, `price`, `condition`
- [ ] 85%+ have `image_url` (when source provides images)
- [ ] 80%+ have `description` (when source provides description)
- [ ] 70%+ have `manufacturer` (parsed from title)
- [ ] 60%+ have `model_number` (parsed from title)
- [ ] CPU/RAM/storage populated when available in source

---

## Next Steps

**Immediate (Phase 2):**
1. Create Alembic migration for `progress_pct` field on ImportSession
2. Update Celery task to set progress at milestones
3. Update API response to include `progress_pct`
4. Update frontend to use real progress

**Following (Phase 3):**
1. Create Alembic migration for `image_url` and `description` fields on Listing
2. Implement brand/model parsing in ListingNormalizer
3. Update IngestionService to map all fields
4. Add tests for new functionality

**Final (Phase 4):**
1. Run comprehensive integration tests
2. Update documentation
3. Consider backfilling existing listings from RawPayload

---

## Files Reviewed

**Backend:**
- ✅ `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/ingestion.py` - NormalizedListingSchema
- ✅ `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py` - IngestionService
- ✅ `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py` - Listing, ImportSession models
- ✅ `/mnt/containers/deal-brain/apps/api/dealbrain_api/tasks/ingestion.py` - Celery task

**Frontend:**
- ✅ `/mnt/containers/deal-brain/apps/web/components/ingestion/ingestion-status-display.tsx` - Progress UI
- ✅ `/mnt/containers/deal-brain/apps/web/hooks/use-ingestion-job.ts` - Polling hook (referenced)

---

## Conclusion

Both issues have **clear, implementable solutions**:

1. **Progress Bar:** Add `progress_pct` field and update task to set milestones
2. **Field Population:** Add `image_url`/`description` fields and enhance field mapping

No architectural changes needed. Both fixes follow Deal Brain patterns and maintain backward compatibility.

**Ready to proceed to Phase 2 implementation.**
