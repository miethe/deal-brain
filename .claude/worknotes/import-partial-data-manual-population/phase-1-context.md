# Phase 1 Context: Backend Schema & Database Changes

**Phase**: 1 of 6
**Last Updated**: 2025-11-08

---

## Implementation Context

This document captures technical decisions, gotchas, and architectural notes discovered during Phase 1 implementation.

---

## Key Architectural Decisions

### Decision 1: Nullable Price Strategy

**Choice**: Make `listings.price_usd` nullable in database

**Rationale**:
- Cleanest NULL semantics (NULL = "not yet provided")
- Simplest implementation (single column change)
- Matches Pydantic schema definition
- Allows storing partial imports immediately

**Trade-offs**:
- Requires NULL checks in all price-dependent queries
- Migration is irreversible if partial imports exist
- Existing analytics queries need updates

**Implementation Notes**:
- Add `WHERE price_usd IS NOT NULL` to aggregation queries
- Update dashboard filters to handle NULL prices
- Consider indexing strategy for quality-based queries

---

### Decision 2: Minimum Viable Data

**Choice**: Only `title` required for import success

**Rationale**:
- Title is most universal field across all marketplaces
- Provides user context even without other data
- Simplest validation logic
- Aligns with user mental model

**Alternative Rejected**: Require title OR (cpu_model + manufacturer)
- **Why Rejected**: Too complex to validate, confusing UX, edge cases difficult to handle

**Implementation Notes**:
- Update `validate_minimum_data()` to check only title
- Log warning if other key fields missing (CPU, RAM, etc.)
- Consider future enhancement: suggest title from CPU model if title missing

---

### Decision 3: Quality Tracking

**Choice**: Add `quality` enum field with values "full" | "partial"

**Schema**:
```python
quality: Mapped[str] = mapped_column(String(20), default='full')
```

**Rationale**:
- Explicit completeness indicator
- Enables dashboard filtering ("Show only complete imports")
- Extensible to future quality levels
- Simple binary distinction for MVP

**Future Enhancements**:
- Add "needs_review" quality level
- Add "verified" quality level
- Multi-field completeness scoring (0-100)

---

### Decision 4: Provenance Tracking

**Choice**: Add `extraction_metadata` JSON field

**Schema**:
```python
extraction_metadata: Mapped[dict] = mapped_column(JSON(), default=dict)
```

**Format**:
```json
{
  "title": "extracted",
  "price": "manual",
  "cpu_model": "extracted",
  "manufacturer": "extracted",
  "ram_gb": "manual"
}
```

**Rationale**:
- Track data source per field
- Supports data trust indicators in UI
- Enables data quality analytics
- Flexible JSON structure for future fields

**UI Usage**:
- Show badges: "Price manually entered"
- Highlight manually entered fields in yellow
- Filter listings by data source

---

## Database Schema Changes

### Migration 0022: Partial Import Support

**File**: `apps/api/alembic/versions/0022_partial_import_support.py`

**Changes**:
1. Make `listings.price_usd` nullable
2. Add `listings.quality` column
3. Add `listings.extraction_metadata` column
4. Add `listings.missing_fields` column

**Gotchas**:
- ⚠️ Irreversible migration if partial imports exist
- Existing listings default to `quality='full'`
- NULL price requires updating dependent queries
- JSON columns default to `{}` not `NULL`

**Testing**:
- Test in dev with empty database
- Test in staging with real data
- Verify existing listings unaffected
- Test rollback with cleanup script

---

## Adapter Changes

### BaseAdapter Validation Logic

**File**: `apps/api/dealbrain_api/adapters/base.py`

**Before**:
```python
required_fields = ["title", "price"]
missing = [f for f in required_fields if f not in data or not data[f]]
if missing:
    raise AdapterException(...)
```

**After**:
```python
# Only title is required
if not data.get("title", "").strip():
    raise AdapterException(
        AdapterError.INVALID_SCHEMA,
        "Title is required for import"
    )

# Price is optional - log warning if missing
if not data.get("price"):
    logger.warning(f"[{self.name}] No price extracted - import will be partial")
```

**Rationale**:
- Removes price requirement
- Preserves title requirement
- Logs warning for observability
- Clearer error messages

---

## Service Layer Changes

### ListingsService Updates

**File**: `apps/api/dealbrain_api/services/listings.py`

**Key Changes**:

1. **Accept NULL Price**:
```python
async def create_from_ingestion(
    self,
    listing_data: NormalizedListingSchema,
    user_id: str,
) -> Listing:
    listing = Listing(
        title=listing_data.title,
        price_usd=listing_data.price,  # May be None
        quality="partial" if listing_data.price is None else "full",
        extraction_metadata=listing_data.extraction_metadata or {},
        # ...
    )
```

2. **Skip Metrics for NULL Price**:
```python
# Only calculate metrics if price is present
if listing.price_usd is not None:
    await self._apply_valuation_and_scoring(listing)
else:
    # Defer metrics until price is provided
    listing.adjusted_price_usd = None
    listing.valuation_breakdown = None
```

**Rationale**:
- Metrics require price as input
- NULL is cleaner than invalid/zero values
- Deferred calculation on completion

---

## Integration Patterns

### Quality Field Usage

**Setting Quality**:
```python
quality = "partial" if listing_data.price is None else "full"
```

**Querying Partial Imports**:
```python
partial_imports = await session.execute(
    select(Listing)
    .where(Listing.quality == "partial")
    .where(Listing.user_id == user_id)
)
```

**Dashboard Filter**:
```python
# Show only complete imports
if filter_quality == "full":
    query = query.where(Listing.quality == "full")
```

---

## Testing Strategy

### Unit Tests

**File**: `tests/test_schemas_ingestion.py`

**Test Cases**:
- Schema validates with `price=None`
- `validate_minimum_data()` passes with only title
- Quality defaults to "full"
- Extraction metadata stores correctly

### Integration Tests

**File**: `tests/test_ingestion_service_partial.py`

**Test Cases**:
- Import with NULL price creates listing
- Listing has `quality='partial'`
- Metrics are NULL for partial imports
- Adapter succeeds without price

---

## Known Gotchas

### 1. Existing Queries Need Updates

**Issue**: Queries that aggregate prices will include NULLs

**Solution**: Add `WHERE price_usd IS NOT NULL` to:
- Average price calculations
- Price range filters
- Valuation metrics
- Dashboard analytics

**Example**:
```python
# Before
avg_price = await session.scalar(select(func.avg(Listing.price_usd)))

# After
avg_price = await session.scalar(
    select(func.avg(Listing.price_usd))
    .where(Listing.price_usd.is_not(None))
)
```

---

### 2. Frontend NULL Handling

**Issue**: Frontend expects price to always exist

**Solution**: Update TypeScript types:
```typescript
interface Listing {
  price_usd: number | null;  // Was: number
  quality: "full" | "partial";
  // ...
}
```

**Display Logic**:
```typescript
{listing.price_usd !== null ? (
  <PriceDisplay value={listing.price_usd} />
) : (
  <Badge variant="warning">Price needed</Badge>
)}
```

---

### 3. CSV Export with NULL Prices

**Issue**: NULL price exports as empty cell

**Solution**: Use explicit placeholder:
```python
price_str = str(listing.price_usd) if listing.price_usd else "N/A"
```

---

## Rollback Strategy

### Scenario: Need to Downgrade Migration

**Preconditions**:
1. No partial imports exist in database, OR
2. Acceptable to delete all partial imports

**Steps**:
1. Check for partial imports: `SELECT COUNT(*) FROM listing WHERE quality = 'partial'`
2. If count > 0, decide:
   - Keep partials: Cannot downgrade
   - Delete partials: Run cleanup script
3. Run downgrade migration

**Cleanup Script**:
```sql
-- Delete all partial imports
DELETE FROM listing WHERE quality = 'partial';

-- Verify no NULL prices remain
SELECT COUNT(*) FROM listing WHERE price_usd IS NULL;

-- If count = 0, safe to downgrade
```

---

## Future Enhancements

### Post-MVP Considerations

1. **Quality Scoring**: Extend to 0-100 scale based on field completeness
2. **Field-Level Confidence**: Track extraction confidence per field
3. **Auto-Completion**: ML-based price estimation for partials
4. **Bulk Completion**: Complete multiple partials at once
5. **Data Verification**: Mark fields as "verified" by user

---

## Questions & Answers

### Q: What if title is empty string?

**A**: Validation checks `title.strip()`, so empty/whitespace-only titles are rejected.

### Q: Can we have partial imports with price but missing other fields?

**A**: Yes, quality only tracks price presence. Future: track all missing fields.

### Q: What happens to abandoned partial imports?

**A**: They persist in database. Future: cleanup job to delete after 30 days.

### Q: Can users edit manually-entered fields later?

**A**: Not in MVP. Future: edit modal with provenance tracking updates.

---

**Last Updated**: 2025-11-08
