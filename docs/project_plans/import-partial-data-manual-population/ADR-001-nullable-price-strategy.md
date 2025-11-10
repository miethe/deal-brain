---
status: "accepted"
date: 2025-11-08
decision_makers: [lead-architect]
---

# ADR 001: Nullable Price Strategy for Partial Imports

## Context

The Deal Brain URL import system currently requires both `title` and `price` for all imports. This all-or-nothing approach results in ~30% import success rate because price extraction frequently fails on dynamic marketplace pages (especially Amazon). Users lose valuable extracted data (title, images, CPU specs, RAM, storage) when price extraction fails.

We need to enable partial data extraction while maintaining data integrity and allowing users to manually complete missing fields.

## Decision

**We will make `listings.price_usd` nullable and support partial imports with manual completion.**

### Key Architectural Decisions

#### 1. Nullable Price in Database

**Decision**: Make `listings.price_usd` column nullable in PostgreSQL.

**Rationale**:
- Simplest implementation - allows storing listings without price
- Aligns with existing schema where `price` is already `Decimal | None` in Pydantic
- Enables persistence of partially extracted data
- Metrics calculation can be deferred until price is provided

**Trade-offs**:
- **Pros**:
  - Clean data model - NULL explicitly means "price not yet available"
  - No artificial default values (e.g., -1, 0) that require special handling
  - Easy to query for partial imports: `WHERE price_usd IS NULL`
- **Cons**:
  - Requires NULL checks in all queries that aggregate or filter by price
  - Irreversible migration if partial data exists (downgrade deletes partial imports)
  - Potential for incomplete listings to persist indefinitely

**Alternative Considered**: Separate `partial_listings` table
- **Rejected**: Adds complexity, requires data migration when completed, duplicates schema

#### 2. Minimum Viable Data Requirement

**Decision**: Only `title` is required for import success. Price is fully optional.

**Rationale**:
- Title provides minimum context for user to identify listing
- Users can complete partial imports by viewing title alone
- Supports edge case where CPU model is in title but price is missing
- Aligns with user mental model: "I can see what I imported even without price"

**Alternative Considered**: Require `title OR (cpu_model + manufacturer)`
- **Rejected**: Too complex, CPU model extraction also unreliable, title is universal

#### 3. Quality Tracking Mechanism

**Decision**: Add `quality` enum field to track "full" vs. "partial" imports.

**Rationale**:
- Explicit indicator of data completeness
- Enables filtering: show only partial imports, hide partial imports, etc.
- Supports future enhancements: "quality score" based on field completeness
- Decoupled from price NULL check (future: other missing fields can be tracked)

**Schema**:
```python
quality: Mapped[str] = mapped_column(
    String(20),
    nullable=False,
    default='full'
)
```

**Values**:
- `"full"`: All required fields present (title + price)
- `"partial"`: Missing required fields (title present, price missing)

**Alternative Considered**: Boolean `is_partial` flag
- **Rejected**: Less extensible, quality is conceptually broader than binary

#### 4. Provenance Tracking

**Decision**: Add `extraction_metadata` JSON field to track field sources.

**Rationale**:
- Users need visibility into which fields were extracted vs. manually entered
- Supports data quality analysis and trust
- Enables future "verify extracted data" workflows
- Debugging: understand adapter extraction patterns

**Schema**:
```python
extraction_metadata: Mapped[dict[str, str]] = mapped_column(
    JSON(),
    nullable=False,
    default=dict
)
```

**Example**:
```json
{
  "title": "extracted",
  "cpu_model": "extracted",
  "ram_gb": "extracted",
  "price": "manual",
  "condition": "manual"
}
```

**Alternative Considered**: Per-field boolean flags (`price_manual`, `title_manual`, etc.)
- **Rejected**: Schema explosion, not flexible for dynamic custom fields

#### 5. Metrics Calculation Strategy

**Decision**: Defer valuation and scoring until price is provided.

**Rationale**:
- Valuation rules require price as input (e.g., RAM deductions from price)
- Scoring profiles calculate $/performance metrics
- Attempting metrics without price would create invalid/meaningless results
- Clean separation: partial listings have NULL for all computed fields

**Implementation**:
```python
if listing.price_usd is not None:
    await self._apply_valuation_and_scoring(listing, session)
else:
    logger.info(f"Listing '{listing.title}' created without price - metrics deferred")
    listing.adjusted_price_usd = None
    listing.valuation_breakdown = None
    listing.score_cpu_multi = None
    # ... all metrics NULL
```

**Alternative Considered**: Calculate partial metrics using placeholder price (e.g., $0)
- **Rejected**: Produces misleading data, confuses users, pollutes analytics

#### 6. Manual Completion Flow

**Decision**: Use PATCH endpoint to update partial listing with completion data.

**Rationale**:
- RESTful: PATCH is semantically correct for partial updates
- Reuses existing listing record (no duplication)
- Atomic: completion and metrics calculation in single transaction
- Idempotent: can retry completion if network fails

**Endpoint**: `PATCH /api/v1/listings/{listing_id}/complete`

**Request Body**:
```json
{
  "price": 299.99
}
```

**Response**: Updated `ListingSchema` with metrics calculated

**Alternative Considered**: Separate completion workflow with status transitions
- **Rejected**: Over-engineered for simple use case, adds state machine complexity

#### 7. Real-Time Update Strategy

**Decision**: Use HTTP polling (2-second interval) for import status updates.

**Rationale**:
- Simple to implement and debug
- Works with existing HTTP infrastructure (no WebSocket setup needed)
- 2-second latency acceptable for this use case (imports take 3-10 seconds)
- Low load: polling stops when imports complete
- Future upgrade path to WebSocket if needed

**Implementation**:
```typescript
// Poll every 2 seconds
const pollInterval = setInterval(async () => {
  const status = await fetch(`/api/v1/ingest/bulk/${bulkJobId}/status`);
  // ... update UI
}, 2000);
```

**Alternative Considered**: WebSocket for real-time updates
- **Deferred**: Added complexity (connection management, reconnection logic), not needed for MVP

#### 8. UI Modal Trigger Strategy

**Decision**: Auto-open modal immediately when partial import completes.

**Rationale**:
- Immediate user action reduces abandonment
- User expects next step after import submission
- Clear UX: import → extract → "complete this" → done
- Minimizes partial listings left incomplete

**Behavior**:
- Import completes with `quality="partial"` → Modal opens
- Import completes with `quality="full"` → Success toast shown
- User can close modal → Partial listing persists for later completion

**Alternative Considered**: Show notification, require user to click "Complete" button
- **Rejected**: Extra step increases friction, higher abandonment rate

## Consequences

### Positive

1. **Import Success Rate**: Expected increase from ~30% to 80%+
2. **User Experience**: No data loss, immediate feedback, clear completion path
3. **Data Persistence**: Valuable extracted data saved even if price missing
4. **Extensibility**: Architecture supports future enhancements (other missing fields, quality scores)
5. **Debugging**: Provenance tracking enables adapter improvement

### Negative

1. **Schema Complexity**: NULL checks required in all price-related queries
2. **Migration Irreversibility**: Cannot downgrade if partial imports exist in production
3. **Incomplete Data Risk**: Partial listings may remain incomplete if users abandon modal
4. **Query Performance**: NULL checks add minor overhead (mitigated by indexes)

### Neutral

1. **Metrics Calculation Deferred**: Expected behavior, not a bug
2. **Manual Completion Required**: Intentional design, user provides missing data
3. **Real-Time Updates**: Polling acceptable for MVP, WebSocket future enhancement

## Monitoring

**Metrics to Track**:
- `import_attempts_total{quality="full|partial"}` - Import quality distribution
- `partial_import_completion_rate` - % of partial imports completed
- `time_to_completion` - Duration from partial import to completion
- `partial_listings_abandoned_7d` - Partials not completed within 7 days

**Alerts**:
- Partial import rate >40% → Investigate adapter extraction failures
- Completion rate <50% → Review modal UX, consider improvements
- Abandoned partials >100 → Consider automated cleanup or reminders

## Implementation Notes

### Migration Sequence

1. **Migration 0022**: Make price nullable, add quality/metadata columns
2. **Migration 0023**: Add bulk job tracking to ImportSession
3. **Deploy Backend**: Update adapters, services, API endpoints
4. **Deploy Frontend**: Update modal, polling hook, progress indicators
5. **Feature Flag**: Enable for beta users → gradual rollout

### Rollback Strategy

**If Critical Issue Found**:
1. Disable feature flag (`enable_partial_imports = false`)
2. Backend rejects imports without price (reverts to old behavior)
3. Frontend hides modal (no user-facing changes)
4. **Do NOT downgrade migration** (preserves partial imports)

**Data Cleanup** (if needed):
```sql
-- Delete incomplete partial imports after 30 days
DELETE FROM listing
WHERE quality = 'partial'
  AND price_usd IS NULL
  AND created_at < NOW() - INTERVAL '30 days';
```

## Related Decisions

- **Future**: Support other missing fields (manufacturer, condition, etc.)
- **Future**: ML-based price estimation for partial imports
- **Future**: Bulk manual completion UI for multiple partials
- **Future**: WebSocket upgrade for real-time updates at scale

## References

- PRD: `/docs/project_plans/import-partial-data-manual-population/PRD.md`
- Implementation Plan: `/docs/project_plans/import-partial-data-manual-population/implementation-plan.md`
- Existing Schema: `packages/core/dealbrain_core/schemas/ingestion.py`
- Database Models: `apps/api/dealbrain_api/models/core.py`
