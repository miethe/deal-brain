---
title: "UX Improvements & Data Enhancement - Implementation Plan"
description: "Detailed phased implementation plan for Nov 18th UX improvements, import enhancements, and bug fixes"
audience: [ai-agents, developers]
tags: [implementation, planning, phases, ux, import, enhancements]
created: 2025-11-18
updated: 2025-11-18
category: "product-planning"
status: draft
related:
  - /docs/project_plans/PRDs/enhancements/ux-improvements-nov-18-v1.md
  - /docs/project_plans/requests/needs-designed/11-18.md
---

# Implementation Plan: UX Improvements & Data Enhancement

**Feature**: UX Improvements & Data Enhancement - November 18th
**PRD**: [ux-improvements-nov-18-v1.md](../../PRDs/enhancements/ux-improvements-nov-18-v1.md)
**Total Effort**: 34 story points
**Estimated Duration**: 6-8 weeks (with parallel work)
**Status**: Draft

---

## Executive Summary

This implementation plan addresses 11 distinct enhancements across 6 phased deliveries:

1. **Phase 1**: Critical UI Bug Fixes (2 pts) - Dual-handle sliders, table header fix
2. **Phase 2**: Listing Workflow Enhancements (5 pts) - Quick edit expansion, edit buttons
3. **Phase 3**: Real-Time Updates Infrastructure (8 pts) - SSE events, auto-recalculation
4. **Phase 4**: Amazon Import Enhancement (8 pts) - Enhanced scraping, NLP extraction
5. **Phase 5**: CPU Catalog Improvements (3 pts) - Sorting, filtering by listings
6. **Phase 6**: Column Selector (8 pts) - Dynamic columns, persistence

**Implementation Strategy**:
- **Quick Wins First**: Phase 1 (bug fixes) delivers immediate user value
- **Parallel Execution**: Phases 1-2, Phases 4-5 can run concurrently
- **Foundation Building**: Phase 3 enables future real-time features
- **Progressive Enhancement**: Each phase delivers standalone value

**Key Success Criteria**:
- All phases pass quality gates (tests, accessibility, performance)
- No regressions in existing functionality
- Performance NFRs met (import <500ms, recalc <2s, updates <2s)
- User acceptance testing passes for each phase

---

## Implementation Strategy

### Architectural Approach

**Frontend-Heavy Implementation**:
- Most work is UI/UX improvements (Phases 1, 2, 5, 6)
- Backend changes limited to Phase 3 (real-time) and Phase 4 (import)
- Reuse existing components and patterns where possible

**Layered Architecture Sequence** (for backend work):
- **Phase 3 & 4**: Routers → Services → Domain Logic
- Real-time updates don't require new database schema
- Amazon import enhances existing import service

**Technology Stack**:
- **Frontend**: React (Next.js), TanStack Query, shadcn/ui components
- **Backend**: FastAPI, SQLAlchemy, Celery (existing)
- **Real-Time**: Server-Sent Events (SSE) via FastAPI
- **NLP**: spaCy or custom regex patterns
- **UI Components**: Recharts for sliders, custom table components

### Parallel Work Opportunities

**Week 1-2**:
- **Track A**: Phase 1 (UI Bug Fixes) - ui-engineer-enhanced
- **Track B**: Phase 2 start (Quick Edit Modal) - frontend-developer

**Week 3-4**:
- **Track A**: Phase 2 completion (Workflow buttons) - ui-engineer-enhanced
- **Track B**: Phase 3 start (Real-Time Infrastructure) - backend-architect, python-backend-engineer

**Week 5-6**:
- **Track A**: Phase 3 completion (Auto-recalc) - python-backend-engineer
- **Track B**: Phase 4 start (Amazon Import - Scraping) - python-backend-engineer

**Week 7-8**:
- **Track A**: Phase 4 completion (Amazon Import - NLP) - ai-engineer
- **Track B**: Phase 5 (CPU Catalog) - frontend-developer

**Week 9-10**:
- **Track A**: Phase 6 (Column Selector) - ui-engineer-enhanced, frontend-developer
- **Track B**: Integration testing, documentation

### Critical Path

**Blocking Dependencies**:
- Phase 3 must complete before Phase 2's auto-recalculation features
- No other hard dependencies between phases

**Risk Mitigation**:
- **Amazon Scraping**: May require iteration if page structure varies
- **NLP Accuracy**: May need pattern tuning to hit 70% target
- **SSE Performance**: Load testing required for 100+ concurrent connections

---

## Phase Overview

| Phase | Title | Effort | Duration | Dependencies | Subagents |
|-------|-------|--------|----------|--------------|-----------|
| 1 | Critical UI Bug Fixes | 2 pts | 2-3 days | None | ui-engineer-enhanced |
| 2 | Listing Workflow Enhancements | 5 pts | 5-7 days | None | ui-engineer-enhanced, frontend-developer |
| 3 | Real-Time Updates Infrastructure | 8 pts | 7-10 days | None | backend-architect, python-backend-engineer |
| 4 | Amazon Import Enhancement | 8 pts | 7-10 days | None | python-backend-engineer, ai-engineer |
| 5 | CPU Catalog Improvements | 3 pts | 3-5 days | None | frontend-developer |
| 6 | Column Selector | 8 pts | 7-10 days | None | ui-engineer-enhanced, frontend-developer |

**Total**: 34 story points, ~6-8 weeks with parallel execution

---

## Phase 1: Critical UI Bug Fixes

**Effort**: 2 story points
**Duration**: 2-3 days
**Priority**: Immediate
**Lead Subagent**: ui-engineer-enhanced

### Overview

Fix two critical UI bugs affecting user experience: single-handle range sliders and hidden table rows.

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate | Subagent |
|----|------|-------------|---------------------|----------|----------|
| UI-001 | Implement dual-handle range sliders | Replace single-handle sliders with dual-handle components (min/max) | - All range sliders show two handles<br>- Current range values displayed<br>- Touch-friendly on mobile<br>- Accessible (keyboard nav) | 1 pt | ui-engineer-enhanced |
| UI-002 | Fix hidden table rows | Adjust table layout to prevent first row hiding behind sticky header | - First row fully visible without scroll<br>- Sticky header doesn't overlap content<br>- Fix applies to all list views | 0.5 pt | ui-engineer-enhanced |
| UI-003 | Cross-browser testing | Test slider and table fixes across browsers and devices | - Verified on Chrome, Firefox, Safari<br>- Tested on desktop and mobile<br>- No regressions | 0.5 pt | test-automator |

### Implementation Details

**UI-001: Dual-Handle Range Sliders**

**Files to Modify**:
- `apps/web/components/ui/slider.tsx` - Base slider component
- `apps/web/components/cpus/cpu-filters.tsx` - CPU filter sliders
- Any other range filter components

**Approach**:
1. Evaluate slider libraries (shadcn/ui's Slider, react-range, rc-slider)
2. Implement dual-handle variant of Slider component
3. Add value display (e.g., "1.5 GHz - 4.2 GHz")
4. Ensure accessibility (ARIA labels, keyboard control)
5. Replace all single-handle range sliders

**Example Implementation**:
```tsx
// apps/web/components/ui/range-slider.tsx
import * as SliderPrimitive from "@radix-ui/react-slider"

export function RangeSlider({ min, max, value, onValueChange, formatValue }) {
  return (
    <div className="space-y-2">
      <SliderPrimitive.Root
        min={min}
        max={max}
        value={value}
        onValueChange={onValueChange}
        className="relative flex items-center w-full h-5"
      >
        <SliderPrimitive.Track>
          <SliderPrimitive.Range />
        </SliderPrimitive.Track>
        <SliderPrimitive.Thumb /> {/* Min handle */}
        <SliderPrimitive.Thumb /> {/* Max handle */}
      </SliderPrimitive.Root>
      <div className="flex justify-between text-sm">
        <span>{formatValue(value[0])}</span>
        <span>{formatValue(value[1])}</span>
      </div>
    </div>
  )
}
```

**UI-002: Fix Hidden Table Rows**

**Files to Modify**:
- `apps/web/components/ui/data-table.tsx` - Base table component
- `apps/web/app/listings/page.tsx` - Listings table
- `apps/web/app/cpus/page.tsx` - CPUs table

**Approach**:
1. Identify sticky header z-index and height
2. Add padding/margin to table body to account for header height
3. Test scroll behavior to ensure no overlap
4. Apply fix to all table components

**Example Fix**:
```tsx
// Adjust table container
<div className="relative">
  <div className="sticky top-0 z-10 bg-background">
    {/* Table header */}
  </div>
  <div className="pt-[calc(header-height)]"> {/* Padding offset */}
    {/* Table body */}
  </div>
</div>
```

### Quality Gates

- [ ] All range sliders have two handles and display current range
- [ ] Sliders accessible via keyboard (tab, arrow keys)
- [ ] First table row fully visible in all list views
- [ ] No regressions in existing UI functionality
- [ ] Cross-browser testing passed
- [ ] Mobile-responsive on iOS and Android

---

## Phase 2: Listing Workflow Enhancements

**Effort**: 5 story points
**Duration**: 5-7 days
**Priority**: High
**Lead Subagents**: ui-engineer-enhanced, frontend-developer

### Overview

Streamline listing editing workflows by expanding quick edit modal, adding quick edit button to view modal, and adding edit button to detail page.

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate | Subagent |
|----|------|-------------|---------------------|----------|----------|
| WF-001 | Expand quick edit modal fields | Add CPU, RAM, Storage, GPU fields to quick edit modal | - Fields match full edit page<br>- Validation consistent<br>- Searchable dropdowns for CPU/GPU<br>- Pre-populated with current data | 2 pts | ui-engineer-enhanced |
| WF-002 | Add Quick Edit button to view modal | Add "Quick Edit" button to listing view modal toolbar | - Button appears in bottom toolbar<br>- Opens quick edit modal<br>- Modal pre-populated<br>- No navigation away from view | 1 pt | frontend-developer |
| WF-003 | Add Edit button to listing detail page | Add "Edit" button to listing detail page header | - Button in top-right next to Delete<br>- Opens full edit page<br>- Consistent styling | 0.5 pt | ui-engineer-enhanced |
| WF-004 | Update quick edit modal component library | Extract quick edit fields as reusable components | - Components reusable across contexts<br>- TypeScript types defined<br>- Props match full edit page | 1 pt | frontend-developer |
| WF-005 | Integration testing for workflows | Test complete edit workflows (view → quick edit → save) | - View → Quick Edit workflow works<br>- Detail page → Edit workflow works<br>- Data persists correctly | 0.5 pt | test-automator |

### Implementation Details

**WF-001: Expand Quick Edit Modal Fields**

**Files to Modify**:
- `apps/web/components/listings/quick-edit-modal.tsx` - Quick edit modal component
- `apps/web/components/listings/listing-form-fields.tsx` - Shared form field components
- `apps/web/lib/validations/listing-schema.ts` - Validation schemas

**Approach**:
1. Identify field components from full edit page:
   - CPU field (searchable dropdown with autocomplete)
   - RAM field (capacity + type dropdowns)
   - Storage field (capacity + type dropdowns)
   - GPU field (searchable dropdown with autocomplete)
2. Extract as reusable components if not already
3. Add to quick edit modal layout
4. Reuse validation schemas from full edit page
5. Ensure modal scrolls if content exceeds viewport

**Example Structure**:
```tsx
// apps/web/components/listings/quick-edit-modal.tsx
export function QuickEditModal({ listing, open, onOpenChange }) {
  const form = useForm({
    resolver: zodResolver(listingQuickEditSchema),
    defaultValues: {
      cpu_id: listing.cpu_id,
      ram_capacity_gb: listing.ram_capacity_gb,
      ram_type: listing.ram_type,
      storage_capacity_gb: listing.storage_capacity_gb,
      storage_type: listing.storage_type,
      gpu_id: listing.gpu_id,
    }
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Quick Edit Listing</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <CpuField name="cpu_id" control={form.control} />
          <RamFields
            capacityName="ram_capacity_gb"
            typeName="ram_type"
            control={form.control}
          />
          <StorageFields
            capacityName="storage_capacity_gb"
            typeName="storage_type"
            control={form.control}
          />
          <GpuField name="gpu_id" control={form.control} />
          <DialogFooter>
            <Button type="submit">Save Changes</Button>
          </DialogFooter>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
```

**WF-002: Add Quick Edit Button to View Modal**

**Files to Modify**:
- `apps/web/components/listings/listing-view-modal.tsx` - View modal component

**Approach**:
1. Add "Quick Edit" button to modal footer/toolbar
2. Store quick edit modal open state
3. Pass listing data to quick edit modal
4. Handle modal transitions (view → quick edit)

**Example**:
```tsx
// apps/web/components/listings/listing-view-modal.tsx
export function ListingViewModal({ listing, open, onOpenChange }) {
  const [quickEditOpen, setQuickEditOpen] = useState(false)

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          {/* Listing details */}
          <DialogFooter>
            <Button variant="outline" onClick={() => setQuickEditOpen(true)}>
              Quick Edit
            </Button>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <QuickEditModal
        listing={listing}
        open={quickEditOpen}
        onOpenChange={setQuickEditOpen}
      />
    </>
  )
}
```

**WF-003: Add Edit Button to Listing Detail Page**

**Files to Modify**:
- `apps/web/app/listings/[id]/page.tsx` - Listing detail page

**Approach**:
1. Add "Edit" button to page header next to "Delete"
2. Link to full edit page: `/listings/[id]/edit`
3. Ensure consistent styling with Delete button

**Example**:
```tsx
// apps/web/app/listings/[id]/page.tsx
export default function ListingDetailPage({ params }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1>Listing Details</h1>
        <div className="flex gap-2">
          <Button asChild>
            <Link href={`/listings/${params.id}/edit`}>
              <PencilIcon className="mr-2 h-4 w-4" />
              Edit
            </Link>
          </Button>
          <DeleteListingButton listingId={params.id} />
        </div>
      </div>
      {/* Listing content */}
    </div>
  )
}
```

### Quality Gates

- [ ] Quick edit modal includes CPU, RAM, Storage, GPU fields
- [ ] Fields match full edit page (validation, components, UX)
- [ ] Quick Edit button appears in view modal footer
- [ ] Quick Edit opens pre-populated with listing data
- [ ] Edit button appears on listing detail page header
- [ ] Edit button navigates to full edit page
- [ ] All workflows tested end-to-end
- [ ] Mobile-responsive on small screens

---

## Phase 3: Real-Time Updates Infrastructure

**Effort**: 8 story points
**Duration**: 7-10 days
**Priority**: High
**Lead Subagents**: backend-architect, python-backend-engineer

### Overview

Implement Server-Sent Events (SSE) infrastructure for real-time UI updates and automatic valuation recalculation triggers.

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate | Subagent |
|----|------|-------------|---------------------|----------|----------|
| RT-001 | Design SSE event architecture | Design event types, payload schemas, pub/sub patterns | - Event types documented<br>- Payload schemas defined<br>- Redis pub/sub strategy defined | 1 pt | backend-architect |
| RT-002 | Implement SSE endpoint in FastAPI | Create SSE endpoint for streaming events to clients | - `/api/v1/events` endpoint created<br>- Handles client connections<br>- Streams events from Redis<br>- Supports reconnection | 2 pts | python-backend-engineer |
| RT-003 | Implement event publishers | Add event publishing to listing create/update endpoints | - Publishes `listing.created` event<br>- Publishes `listing.updated` event<br>- Event payloads include listing ID, changes | 1 pt | python-backend-engineer |
| RT-004 | Implement frontend SSE client | Create React hook for SSE connection and event handling | - `useEventStream` hook created<br>- Handles connection lifecycle<br>- Parses event types<br>- Auto-reconnects on disconnect | 2 pts | frontend-developer |
| RT-005 | Implement auto-recalculation triggers | Trigger valuation recalc when listings/rules change | - Recalc queued on price/component change<br>- Recalc queued on valuation rule change<br>- Only affected listings recalculated<br>- Completes in <2s for 100 listings | 1.5 pts | python-backend-engineer |
| RT-006 | Add recalculation progress indicators | Show UI feedback during background recalculation | - Toast notification on recalc start<br>- Progress indicator if >5s<br>- Completion notification | 0.5 pt | frontend-developer |

### Implementation Details

**RT-001: Design SSE Event Architecture**

**Event Types**:
```typescript
// Event type definitions
type EventType =
  | 'listing.created'
  | 'listing.updated'
  | 'listing.deleted'
  | 'valuation.recalculated'
  | 'import.completed'

interface ListingCreatedEvent {
  type: 'listing.created'
  data: {
    listing_id: string
    timestamp: string
  }
}

interface ListingUpdatedEvent {
  type: 'listing.updated'
  data: {
    listing_id: string
    changes: string[] // Field names that changed
    timestamp: string
  }
}

interface ValuationRecalculatedEvent {
  type: 'valuation.recalculated'
  data: {
    listing_ids: string[]
    timestamp: string
  }
}
```

**Redis Pub/Sub Pattern**:
- Channel: `dealbrain:events`
- Publishers: API endpoints (create/update/delete)
- Subscribers: SSE endpoint (streams to connected clients)

**RT-002: Implement SSE Endpoint in FastAPI**

**Files to Create**:
- `apps/api/dealbrain_api/api/v1/events.py` - SSE endpoint

**Approach**:
```python
# apps/api/dealbrain_api/api/v1/events.py
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
import json

router = APIRouter()

async def event_stream(request: Request):
    """Stream events to client via SSE"""
    redis = request.app.state.redis
    pubsub = redis.pubsub()
    await pubsub.subscribe("dealbrain:events")

    try:
        while True:
            if await request.is_disconnected():
                break

            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                event_data = json.loads(message["data"])
                yield {
                    "event": event_data["type"],
                    "data": json.dumps(event_data["data"])
                }

            await asyncio.sleep(0.1)  # Prevent busy loop
    finally:
        await pubsub.unsubscribe("dealbrain:events")

@router.get("/events")
async def events(request: Request):
    """SSE endpoint for real-time events"""
    return EventSourceResponse(event_stream(request))
```

**RT-003: Implement Event Publishers**

**Files to Modify**:
- `apps/api/dealbrain_api/services/listings.py` - Add event publishing

**Approach**:
```python
# apps/api/dealbrain_api/services/listings.py
async def create_listing(db: AsyncSession, data: ListingCreate) -> ListingDTO:
    # ... existing creation logic ...

    # Publish event
    await publish_event({
        "type": "listing.created",
        "data": {
            "listing_id": str(listing.id),
            "timestamp": datetime.utcnow().isoformat()
        }
    })

    return listing_dto

async def update_listing(db: AsyncSession, listing_id: UUID, data: ListingUpdate) -> ListingDTO:
    # ... existing update logic ...

    # Determine changed fields
    changes = [field for field in data.model_dump(exclude_unset=True).keys()]

    # Publish event
    await publish_event({
        "type": "listing.updated",
        "data": {
            "listing_id": str(listing_id),
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat()
        }
    })

    return listing_dto

# Helper function
async def publish_event(event: dict):
    """Publish event to Redis pub/sub"""
    redis = get_redis()  # Get from app state
    await redis.publish("dealbrain:events", json.dumps(event))
```

**RT-004: Implement Frontend SSE Client**

**Files to Create**:
- `apps/web/hooks/use-event-stream.ts` - SSE client hook

**Approach**:
```typescript
// apps/web/hooks/use-event-stream.ts
import { useEffect, useRef } from 'react'

export function useEventStream(eventType: string, handler: (data: any) => void) {
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    // Create EventSource connection
    const eventSource = new EventSource(`${API_URL}/api/v1/events`)
    eventSourceRef.current = eventSource

    // Listen for specific event type
    eventSource.addEventListener(eventType, (event) => {
      const data = JSON.parse(event.data)
      handler(data)
    })

    // Handle errors and reconnect
    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      eventSource.close()

      // Reconnect after 5s
      setTimeout(() => {
        // Recreate connection (useEffect will handle cleanup)
      }, 5000)
    }

    // Cleanup on unmount
    return () => {
      eventSource.close()
    }
  }, [eventType, handler])
}

// Usage in listings page
export function useListingUpdates() {
  const queryClient = useQueryClient()

  useEventStream('listing.created', (data) => {
    // Invalidate listings query to refetch
    queryClient.invalidateQueries(['listings'])
    toast.success('New listing added')
  })

  useEventStream('listing.updated', (data) => {
    // Invalidate specific listing
    queryClient.invalidateQueries(['listing', data.listing_id])
  })
}
```

**RT-005: Implement Auto-Recalculation Triggers**

**Files to Modify**:
- `apps/api/dealbrain_api/services/listings.py` - Trigger recalc on update
- `apps/api/dealbrain_api/services/valuation_rules.py` - Trigger recalc on rule changes

**Approach**:
```python
# apps/api/dealbrain_api/services/listings.py
async def update_listing(db: AsyncSession, listing_id: UUID, data: ListingUpdate) -> ListingDTO:
    # ... existing update logic ...

    # Check if recalculation needed
    recalc_fields = {'price', 'cpu_id', 'gpu_id', 'ram_capacity_gb', 'storage_capacity_gb'}
    if recalc_fields & set(data.model_dump(exclude_unset=True).keys()):
        # Queue recalculation for this listing
        await queue_recalculation([listing_id])

    return listing_dto

# apps/api/dealbrain_api/services/valuation_rules.py
async def update_valuation_rule(db: AsyncSession, rule_id: UUID, data: ValuationRuleUpdate):
    # ... existing update logic ...

    # Find all affected listings (using this rule's component type)
    affected_listings = await get_listings_with_component_type(db, rule.component_type)

    # Queue recalculation
    await queue_recalculation([l.id for l in affected_listings])

    return rule_dto

# Celery task for recalculation
@celery_app.task
def recalculate_listings(listing_ids: list[str]):
    """Background task to recalculate listing valuations"""
    db = get_db()

    for listing_id in listing_ids:
        try:
            listing = db.query(Listing).filter(Listing.id == listing_id).one()
            # Recompute valuation using core logic
            valuation_result = compute_valuation(listing)
            listing.adjusted_price = valuation_result.adjusted_price
            listing.valuation_breakdown = valuation_result.breakdown
            db.commit()
        except Exception as e:
            logger.error(f"Failed to recalculate listing {listing_id}: {e}")
            db.rollback()

    # Publish completion event
    publish_event({
        "type": "valuation.recalculated",
        "data": {"listing_ids": listing_ids}
    })
```

### Quality Gates

- [ ] SSE endpoint handles 100+ concurrent connections
- [ ] Events published correctly on listing create/update/delete
- [ ] Frontend receives events and updates UI within 2s
- [ ] Auto-reconnection works on connection loss
- [ ] Recalculation triggers only for affected listings
- [ ] Recalculation completes in <2s for 100 listings
- [ ] No memory leaks from long-lived connections
- [ ] Load testing passed (100+ concurrent users)

---

## Phase 4: Amazon Import Enhancement

**Effort**: 8 story points
**Duration**: 7-10 days
**Priority**: Medium
**Lead Subagents**: python-backend-engineer, ai-engineer

### Overview

Enhance Amazon import to populate 70%+ of fields through improved scraping and NLP-based extraction from titles/descriptions.

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate | Subagent |
|----|------|-------------|---------------------|----------|----------|
| AI-001 | Enhance Amazon scraper | Improve scraping to extract more structured data from product pages | - Extracts specs table<br>- Extracts manufacturer, model<br>- Handles page structure variations<br>- Graceful degradation | 2 pts | python-backend-engineer |
| AI-002 | Implement NLP extraction patterns | Create regex/NLP patterns to extract component data from titles/descriptions | - Patterns for CPU (Intel Core i7-12700, AMD Ryzen 5 5600X, etc.)<br>- Patterns for RAM (16GB DDR4, 32GB DDR5, etc.)<br>- Patterns for Storage (512GB NVMe SSD, 1TB HDD, etc.)<br>- Patterns for GPU (RTX 3060, RX 6600, etc.) | 2.5 pts | ai-engineer |
| AI-003 | Implement extraction confidence scoring | Score extraction confidence (high/medium/low) for user review | - Confidence algorithm defined<br>- Low-confidence extractions flagged<br>- User can review/correct | 1 pt | ai-engineer |
| AI-004 | Implement catalog matching | Match extracted CPU/GPU names to catalog entries (fuzzy matching) | - Fuzzy matching algorithm<br>- Handles variations (i7-12700K vs Core i7-12700K)<br>- Fallback to manual entry if no match | 1.5 pts | python-backend-engineer |
| AI-005 | Integration testing | Test import with 20+ Amazon URLs across product types | - 70%+ fields populated<br>- Extraction accuracy validated<br>- Performance <500ms per listing | 1 pt | test-automator |

### Implementation Details

**AI-001: Enhance Amazon Scraper**

**Files to Modify**:
- `apps/api/dealbrain_api/importers/amazon_scraper.py` - Amazon scraping logic

**Approach**:
1. Use BeautifulSoup to parse product page HTML
2. Extract structured data:
   - Product title
   - Product description
   - Specifications table (varies by product type)
   - Price
   - Manufacturer (if available)
   - Model number (if available)
3. Handle variations in page structure (desktop vs. mobile)
4. Add error handling for missing elements

**Example**:
```python
# apps/api/dealbrain_api/importers/amazon_scraper.py
import requests
from bs4 import BeautifulSoup

async def scrape_amazon_product(url: str) -> dict:
    """Scrape Amazon product page for structured data"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract title
    title = soup.find(id='productTitle')
    title_text = title.get_text().strip() if title else ""

    # Extract specifications table
    specs = {}
    spec_table = soup.find('table', id='productDetails_techSpec_section_1')
    if spec_table:
        for row in spec_table.find_all('tr'):
            key = row.find('th').get_text().strip()
            value = row.find('td').get_text().strip()
            specs[key] = value

    # Extract manufacturer and model
    manufacturer = specs.get('Manufacturer', '')
    model = specs.get('Model Number', '')

    return {
        'title': title_text,
        'manufacturer': manufacturer,
        'model': model,
        'specs': specs,
    }
```

**AI-002: Implement NLP Extraction Patterns**

**Files to Create**:
- `apps/api/dealbrain_api/importers/nlp_extractor.py` - NLP extraction logic
- `apps/api/dealbrain_api/importers/extraction_patterns.yaml` - Extraction patterns

**Approach**:
1. Define regex patterns for each component type
2. Apply patterns to title and description
3. Extract all matches with confidence scores
4. Validate against known formats

**Example Patterns**:
```yaml
# apps/api/dealbrain_api/importers/extraction_patterns.yaml
cpu_patterns:
  - pattern: '(Intel|AMD)\s+(Core\s+)?([iR][3579]|Ryzen\s+[3579])\s*-?\s*(\d{4,5}[A-Z]*)'
    confidence: high
    examples:
      - "Intel Core i7-12700K"
      - "AMD Ryzen 5 5600X"
  - pattern: '(Intel|AMD)\s+(\w+)\s+(\d{4,5})'
    confidence: medium
    examples:
      - "Intel Xeon 1234"

ram_patterns:
  - pattern: '(\d+)\s*GB\s+(DDR[345])'
    confidence: high
    examples:
      - "16GB DDR4"
      - "32GB DDR5"
  - pattern: '(\d+)\s*GB\s+(RAM|Memory)'
    confidence: medium
    examples:
      - "16GB RAM"

storage_patterns:
  - pattern: '(\d+)\s*(GB|TB)\s+(NVMe\s+)?(SSD|HDD)'
    confidence: high
    examples:
      - "512GB NVMe SSD"
      - "1TB HDD"

gpu_patterns:
  - pattern: '(NVIDIA\s+)?(GeForce\s+)?(RTX|GTX)\s*(\d{4})\s*(Ti)?'
    confidence: high
    examples:
      - "NVIDIA GeForce RTX 3060"
      - "RTX 3060 Ti"
  - pattern: '(AMD\s+)?(Radeon\s+)?(RX)\s*(\d{4})'
    confidence: high
    examples:
      - "AMD Radeon RX 6600"
```

**Example Implementation**:
```python
# apps/api/dealbrain_api/importers/nlp_extractor.py
import re
import yaml

class NLPExtractor:
    def __init__(self):
        with open('extraction_patterns.yaml') as f:
            self.patterns = yaml.safe_load(f)

    def extract_cpu(self, text: str) -> dict:
        """Extract CPU information from text"""
        for pattern_def in self.patterns['cpu_patterns']:
            pattern = pattern_def['pattern']
            confidence = pattern_def['confidence']

            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return first match with confidence
                cpu_text = ' '.join(matches[0])
                return {
                    'value': cpu_text,
                    'confidence': confidence,
                    'pattern': pattern
                }

        return None

    def extract_ram(self, text: str) -> dict:
        """Extract RAM information from text"""
        for pattern_def in self.patterns['ram_patterns']:
            pattern = pattern_def['pattern']
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                capacity_gb = int(matches[0][0])
                ram_type = matches[0][1]
                return {
                    'capacity_gb': capacity_gb,
                    'type': ram_type,
                    'confidence': pattern_def['confidence']
                }

        return None

    # Similar methods for storage, GPU, etc.
```

**AI-003: Implement Extraction Confidence Scoring**

**Approach**:
- **High Confidence**: Exact pattern match + validated against catalog
- **Medium Confidence**: Pattern match but not in catalog
- **Low Confidence**: Weak pattern match or multiple possible values

**Example**:
```python
def score_extraction_confidence(extracted_value: str, catalog_entries: list) -> str:
    """Score extraction confidence"""
    # Check if extracted value matches catalog entry
    if fuzzy_match(extracted_value, catalog_entries, threshold=0.9):
        return 'high'
    elif fuzzy_match(extracted_value, catalog_entries, threshold=0.7):
        return 'medium'
    else:
        return 'low'
```

**AI-004: Implement Catalog Matching**

**Files to Modify**:
- `apps/api/dealbrain_api/services/catalog_matcher.py` - Fuzzy matching logic

**Approach**:
```python
from fuzzywuzzy import fuzz

def match_cpu_to_catalog(extracted_cpu: str, cpus: list[CPU]) -> CPU | None:
    """Fuzzy match extracted CPU to catalog entry"""
    best_match = None
    best_score = 0

    for cpu in cpus:
        # Try matching against CPU name
        score = fuzz.ratio(extracted_cpu.lower(), cpu.name.lower())

        # Also try matching against common aliases
        if cpu.aliases:
            for alias in cpu.aliases:
                alias_score = fuzz.ratio(extracted_cpu.lower(), alias.lower())
                score = max(score, alias_score)

        if score > best_score:
            best_score = score
            best_match = cpu

    # Return match if confidence >70%
    return best_match if best_score > 70 else None
```

### Quality Gates

- [ ] Amazon imports populate 70%+ of fields
- [ ] NLP extraction patterns achieve 85%+ accuracy
- [ ] Extraction completes in <500ms per listing
- [ ] Low-confidence extractions flagged for review
- [ ] Catalog matching handles common name variations
- [ ] Graceful degradation if scraping fails
- [ ] Tested with 20+ real Amazon URLs

---

## Phase 5: CPU Catalog Improvements

**Effort**: 3 story points
**Duration**: 3-5 days
**Priority**: Medium
**Lead Subagent**: frontend-developer

### Overview

Add sorting and filtering capabilities to the /cpus catalog page, including filtering by listing availability and sorting by listing count.

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate | Subagent |
|----|------|-------------|---------------------|----------|----------|
| CPU-001 | Implement CPU sorting | Add sorting controls for all CPU fields | - Sort by: name, clock speed, cores, threads, TDP, benchmark scores<br>- Ascending/descending toggle<br>- Sort persisted in URL query params | 1 pt | frontend-developer |
| CPU-002 | Implement listing count query | Add backend query to get listing count per CPU | - API endpoint returns CPU with listing count<br>- Efficient query (no N+1)<br>- Cached for performance | 1 pt | python-backend-engineer |
| CPU-003 | Implement listing filters | Add "CPUs with listings" filter and listing count sort | - Filter toggle: "CPUs with listings"<br>- Sort option: "Listing count"<br>- Listing count badge on CPU cards | 1 pt | frontend-developer |

### Implementation Details

**CPU-001: Implement CPU sorting**

**Files to Modify**:
- `apps/web/app/cpus/page.tsx` - CPU catalog page
- `apps/web/components/cpus/cpu-filters.tsx` - Filter/sort controls

**Approach**:
```tsx
// apps/web/app/cpus/page.tsx
export default function CpuCatalogPage({ searchParams }) {
  const sortBy = searchParams.sortBy || 'name'
  const sortOrder = searchParams.sortOrder || 'asc'

  const { data: cpus } = useQuery({
    queryKey: ['cpus', { sortBy, sortOrder }],
    queryFn: () => fetchCpus({ sortBy, sortOrder })
  })

  return (
    <div>
      <CpuSortControls sortBy={sortBy} sortOrder={sortOrder} />
      <CpuGrid cpus={cpus} />
    </div>
  )
}

// apps/web/components/cpus/cpu-sort-controls.tsx
export function CpuSortControls({ sortBy, sortOrder }) {
  return (
    <div className="flex gap-4">
      <Select value={sortBy} onValueChange={(value) => updateSearchParams({ sortBy: value })}>
        <SelectTrigger>
          <SelectValue placeholder="Sort by" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="name">Name</SelectItem>
          <SelectItem value="clock_speed_ghz">Clock Speed</SelectItem>
          <SelectItem value="core_count">Core Count</SelectItem>
          <SelectItem value="thread_count">Thread Count</SelectItem>
          <SelectItem value="tdp">TDP</SelectItem>
          <SelectItem value="cpu_mark">CPU Mark</SelectItem>
          <SelectItem value="single_thread_rating">Single Thread</SelectItem>
        </SelectContent>
      </Select>

      <Button
        variant="outline"
        onClick={() => toggleSortOrder()}
      >
        {sortOrder === 'asc' ? <ArrowUpIcon /> : <ArrowDownIcon />}
      </Button>
    </div>
  )
}
```

**CPU-002: Implement Listing Count Query**

**Files to Modify**:
- `apps/api/dealbrain_api/api/v1/cpus.py` - CPU endpoints
- `apps/api/dealbrain_api/repositories/cpus.py` - CPU repository
- `apps/api/dealbrain_api/schemas/cpu.py` - CPU DTO

**Approach**:
```python
# apps/api/dealbrain_api/repositories/cpus.py
async def get_cpus_with_listing_counts(
    db: AsyncSession,
    sort_by: str = "name",
    sort_order: str = "asc"
) -> list[tuple[CPU, int]]:
    """Get CPUs with listing counts"""
    from sqlalchemy import func, select
    from dealbrain_api.models import CPU, Listing

    # Query with left join to count listings per CPU
    query = (
        select(CPU, func.count(Listing.id).label('listing_count'))
        .outerjoin(Listing, Listing.cpu_id == CPU.id)
        .group_by(CPU.id)
    )

    # Apply sorting
    if sort_by == 'listing_count':
        order_col = func.count(Listing.id)
    else:
        order_col = getattr(CPU, sort_by)

    if sort_order == 'desc':
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())

    result = await db.execute(query)
    return result.all()

# apps/api/dealbrain_api/schemas/cpu.py
class CpuWithListingCount(BaseModel):
    """CPU DTO with listing count"""
    id: UUID
    name: str
    clock_speed_ghz: float
    core_count: int
    # ... other CPU fields ...
    listing_count: int  # Added field
```

**CPU-003: Implement Listing Filters**

**Files to Modify**:
- `apps/web/app/cpus/page.tsx` - Add filter toggle
- `apps/web/components/cpus/cpu-card.tsx` - Add listing count badge

**Approach**:
```tsx
// Filter toggle
<Switch
  checked={showOnlyWithListings}
  onCheckedChange={setShowOnlyWithListings}
  label="Only show CPUs with listings"
/>

// CPU card with badge
<Card>
  <CardHeader>
    <div className="flex justify-between">
      <CardTitle>{cpu.name}</CardTitle>
      {cpu.listing_count > 0 && (
        <Badge variant="secondary">
          {cpu.listing_count} listings
        </Badge>
      )}
    </div>
  </CardHeader>
  {/* ... rest of card ... */}
</Card>
```

### Quality Gates

- [ ] CPUs sortable by all specification fields
- [ ] Sort persisted in URL (shareable links)
- [ ] "CPUs with listings" filter works correctly
- [ ] Listing count displayed on CPU cards
- [ ] Sort by listing count works (most popular first)
- [ ] Performance: Listing count query <100ms
- [ ] Mobile-responsive sort/filter controls

---

## Phase 6: Column Selector

**Effort**: 8 story points
**Duration**: 7-10 days
**Priority**: Low
**Lead Subagents**: ui-engineer-enhanced, frontend-developer

### Overview

Implement dynamic column selection for all entity list views with persistence across sessions.

### Tasks

| ID | Task | Description | Acceptance Criteria | Estimate | Subagent |
|----|------|-------------|---------------------|----------|----------|
| COL-001 | Design column selector component | Create reusable column selector UI component | - Dropdown/modal UI designed<br>- Checkbox list for columns<br>- Drag-to-reorder functionality<br>- Reset to default button | 2 pts | ui-designer, ui-engineer-enhanced |
| COL-002 | Implement column persistence | Save column preferences to localStorage | - Preferences keyed by entity type<br>- Load preferences on mount<br>- Update on selection change | 1 pt | frontend-developer |
| COL-003 | Implement dynamic table rendering | Render table columns based on selected columns | - Table adapts to selected columns<br>- Column order matches selector<br>- Hidden columns not rendered | 1.5 pts | frontend-developer |
| COL-004 | Implement for Listings entity | Add column selector to listings page | - All listing fields available<br>- Includes custom fields<br>- Default columns defined | 1.5 pts | ui-engineer-enhanced |
| COL-005 | Implement for other entities | Add column selector to CPUs, GPUs, Valuation Rules, Profiles | - Consistent UI across entities<br>- Entity-specific field lists<br>- Separate preferences per entity | 1.5 pts | frontend-developer |
| COL-006 | Accessibility and testing | Ensure keyboard navigation and screen reader support | - Keyboard navigable<br>- ARIA labels<br>- Screen reader tested | 0.5 pt | web-accessibility-checker |

### Implementation Details

**COL-001: Design Column Selector Component**

**Files to Create**:
- `apps/web/components/ui/column-selector.tsx` - Reusable column selector

**Approach**:
```tsx
// apps/web/components/ui/column-selector.tsx
interface ColumnDefinition {
  id: string
  label: string
  defaultVisible: boolean
}

interface ColumnSelectorProps {
  columns: ColumnDefinition[]
  selectedColumns: string[]
  onColumnsChange: (columnIds: string[]) => void
}

export function ColumnSelector({ columns, selectedColumns, onColumnsChange }: ColumnSelectorProps) {
  const [localColumns, setLocalColumns] = useState(selectedColumns)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline">
          <Columns3Icon className="mr-2 h-4 w-4" />
          Columns
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64">
        <DropdownMenuLabel>Select Columns</DropdownMenuLabel>
        <DropdownMenuSeparator />

        <DndContext onDragEnd={handleDragEnd}>
          <SortableContext items={localColumns}>
            {columns.map((col) => (
              <SortableColumnItem
                key={col.id}
                column={col}
                checked={localColumns.includes(col.id)}
                onCheckedChange={(checked) => toggleColumn(col.id, checked)}
              />
            ))}
          </SortableContext>
        </DndContext>

        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={resetToDefault}>
          Reset to Default
        </DropdownMenuItem>

        <div className="p-2">
          <Button onClick={() => onColumnsChange(localColumns)} className="w-full">
            Apply
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

**COL-002: Implement Column Persistence**

**Files to Create**:
- `apps/web/hooks/use-column-preferences.ts` - Column persistence hook

**Approach**:
```typescript
// apps/web/hooks/use-column-preferences.ts
export function useColumnPreferences(entityType: string, defaultColumns: string[]) {
  const [selectedColumns, setSelectedColumns] = useState<string[]>([])

  // Load from localStorage on mount
  useEffect(() => {
    const storageKey = `column-preferences-${entityType}`
    const stored = localStorage.getItem(storageKey)

    if (stored) {
      setSelectedColumns(JSON.parse(stored))
    } else {
      setSelectedColumns(defaultColumns)
    }
  }, [entityType, defaultColumns])

  // Save to localStorage on change
  const updateColumns = (columns: string[]) => {
    setSelectedColumns(columns)
    const storageKey = `column-preferences-${entityType}`
    localStorage.setItem(storageKey, JSON.stringify(columns))
  }

  const resetToDefault = () => {
    updateColumns(defaultColumns)
  }

  return { selectedColumns, updateColumns, resetToDefault }
}
```

**COL-003: Implement Dynamic Table Rendering**

**Files to Modify**:
- `apps/web/components/ui/data-table.tsx` - Make table dynamic

**Approach**:
```tsx
// apps/web/components/ui/data-table.tsx
interface DataTableProps<TData> {
  columns: ColumnDef<TData>[] // All available columns
  selectedColumnIds: string[] // Visible column IDs
  data: TData[]
}

export function DataTable<TData>({ columns, selectedColumnIds, data }: DataTableProps<TData>) {
  // Filter columns based on selection
  const visibleColumns = columns.filter(col => selectedColumnIds.includes(col.id))

  // Reorder columns based on selectedColumnIds order
  const orderedColumns = selectedColumnIds
    .map(id => visibleColumns.find(col => col.id === id))
    .filter(Boolean)

  const table = useReactTable({
    data,
    columns: orderedColumns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map((headerGroup) => (
          <TableRow key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <TableHead key={header.id}>
                {flexRender(header.column.columnDef.header, header.getContext())}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {/* Render rows with visible columns */}
      </TableBody>
    </Table>
  )
}
```

**COL-004: Implement for Listings Entity**

**Files to Modify**:
- `apps/web/app/listings/page.tsx` - Add column selector

**Approach**:
```tsx
// Define all available columns
const ALL_LISTING_COLUMNS: ColumnDefinition[] = [
  { id: 'manufacturer', label: 'Manufacturer', defaultVisible: true },
  { id: 'model', label: 'Model', defaultVisible: true },
  { id: 'cpu', label: 'CPU', defaultVisible: true },
  { id: 'ram', label: 'RAM', defaultVisible: true },
  { id: 'storage', label: 'Storage', defaultVisible: true },
  { id: 'gpu', label: 'GPU', defaultVisible: false },
  { id: 'price', label: 'Price', defaultVisible: true },
  { id: 'adjusted_price', label: 'Adj. Price', defaultVisible: true },
  { id: 'cpu_mark', label: 'CPU Mark', defaultVisible: false },
  { id: 'form_factor', label: 'Form Factor', defaultVisible: false },
  // ... all other fields including custom fields
]

export default function ListingsPage() {
  const defaultColumns = ALL_LISTING_COLUMNS
    .filter(col => col.defaultVisible)
    .map(col => col.id)

  const { selectedColumns, updateColumns, resetToDefault } = useColumnPreferences(
    'listings',
    defaultColumns
  )

  return (
    <div>
      <div className="flex justify-between mb-4">
        <h1>Listings</h1>
        <ColumnSelector
          columns={ALL_LISTING_COLUMNS}
          selectedColumns={selectedColumns}
          onColumnsChange={updateColumns}
        />
      </div>

      <DataTable
        columns={listingTableColumns} // All column definitions
        selectedColumnIds={selectedColumns}
        data={listings}
      />
    </div>
  )
}
```

### Quality Gates

- [ ] Column selector component reusable across entities
- [ ] Drag-to-reorder columns works intuitively
- [ ] Column preferences persist across sessions
- [ ] Reset to default restores original column set
- [ ] Implemented for Listings, CPUs, GPUs, Valuation Rules, Profiles
- [ ] All entity fields (including custom fields) available
- [ ] Keyboard accessible (tab navigation, space to toggle)
- [ ] Screen reader announces selected columns
- [ ] Mobile-responsive (simplified UI on small screens)

---

## Risk Mitigation

### Technical Risks

**Risk 1: Amazon Scraping Reliability**
- **Impact**: High (blocks field population)
- **Mitigation**:
  - Implement fallback to NLP extraction
  - Add monitoring/alerting for scraping failures
  - Cache scraped data (24hr TTL) to reduce re-scraping
  - Provide manual override for failed extractions

**Risk 2: NLP Extraction Accuracy <70%**
- **Impact**: Medium (reduces auto-population value)
- **Mitigation**:
  - Manually tune patterns based on real data
  - Add user feedback mechanism for corrections
  - Iteratively improve patterns based on feedback
  - Provide confidence scores for user review

**Risk 3: SSE Performance Under Load**
- **Impact**: High (affects real-time updates)
- **Mitigation**:
  - Implement connection throttling (max 100 connections)
  - Use Redis pub/sub for efficient message distribution
  - Add reconnection backoff to prevent thundering herd
  - Load test with 100+ concurrent connections

**Risk 4: Recalculation Performance Issues**
- **Impact**: Medium (slow UI updates)
- **Mitigation**:
  - Queue recalculation tasks (Celery)
  - Only recalculate affected listings (not full catalog)
  - Add rate limiting (max 1000 listings/batch)
  - Show progress indicator for long-running recalcs

### Schedule Risks

**Risk 5: Phases Take Longer Than Estimated**
- **Impact**: Medium (delays later phases)
- **Mitigation**:
  - Prioritize high-value phases (1, 2, 3)
  - Allow parallel work on independent phases
  - Phase 6 (Column Selector) can be descoped if needed

### Scope Risks

**Risk 6: Feature Creep During Implementation**
- **Impact**: Low (scope expansion)
- **Mitigation**:
  - Strictly adhere to PRD requirements
  - Document new requests as separate PRDs
  - Focus on MVP for each phase

---

## Resource Requirements

### Team Composition

**Frontend Development** (4 weeks total):
- ui-engineer-enhanced: Phases 1, 2, 6 (3 weeks)
- frontend-developer: Phases 2, 3, 5, 6 (3 weeks)
- ui-designer: Phase 6 design (1 week)

**Backend Development** (3 weeks total):
- python-backend-engineer: Phases 3, 4, 5 (3 weeks)
- backend-architect: Phase 3 design (1 week)
- ai-engineer: Phase 4 NLP (2 weeks)

**QA/Testing** (2 weeks total):
- test-automator: All phases (2 weeks, distributed)
- web-accessibility-checker: Phase 6 (3 days)

**Documentation**:
- documentation-writer: All phases (1 week, distributed)

### Infrastructure

**Backend**:
- Redis for pub/sub (SSE events)
- Celery workers for recalculation tasks
- FastAPI with SSE support

**Frontend**:
- React 18+ with Next.js 14
- TanStack Query for data fetching
- shadcn/ui component library

**External Services**:
- Amazon product pages (public access, no API required)

---

## Success Metrics

### Delivery Metrics

- [ ] All 6 phases completed on schedule
- [ ] Code coverage >80% for new code
- [ ] Zero P0/P1 bugs in production
- [ ] All quality gates passed

### Business Metrics

- [ ] Amazon import time reduced from 5 min → <1 min per listing
- [ ] Edit workflow clicks reduced from 3 → 1
- [ ] Slider confusion reports eliminated
- [ ] Table visibility issues eliminated
- [ ] User satisfaction score >4/5 for new features

### Technical Metrics

- [ ] Amazon import field population: 70%+
- [ ] SSE handles 100+ concurrent connections
- [ ] Recalculation completes in <2s for 100 listings
- [ ] Column selector load time <100ms
- [ ] No performance regressions

---

## Communication Plan

### Status Reporting

**Daily Standups**:
- Share progress on current phase tasks
- Identify blockers (especially Amazon scraping, NLP tuning)
- Coordinate parallel work

**Weekly Demos**:
- Demo completed phases to stakeholders
- Gather feedback on UX/functionality
- Adjust upcoming phases if needed

**Phase Completions**:
- Document lessons learned
- Update progress tracking
- Plan next phase kickoff

### Escalation

**Technical Blockers**:
- Escalate to backend-architect (SSE, architecture)
- Escalate to lead-architect (cross-cutting decisions)

**Schedule Delays**:
- Escalate to PM if phase exceeds estimate by >20%
- Discuss descoping or resource reallocation

---

## Post-Implementation Plan

### Monitoring

**Phase 3 (Real-Time Updates)**:
- Monitor SSE connection count and duration
- Alert on connection failures or high latency
- Track event delivery success rate

**Phase 4 (Amazon Import)**:
- Monitor import success rate (field population %)
- Track NLP extraction accuracy
- Alert on scraping failures

**Phase 5 (CPU Catalog)**:
- Monitor listing count query performance
- Track sort/filter usage analytics

**Phase 6 (Column Selector)**:
- Track most commonly selected columns
- Monitor localStorage usage and errors

### Maintenance

**Pattern Updates** (Phase 4):
- Review NLP extraction patterns quarterly
- Update based on new CPU/GPU naming conventions
- Add new patterns for emerging products

**Performance Tuning** (Phase 3):
- Optimize recalculation batch size based on metrics
- Tune SSE connection limits based on load

---

## Appendix

### A. Technology Stack

**Frontend**:
- React 18.2+
- Next.js 14 (App Router)
- TanStack Query 5.x
- shadcn/ui (Radix UI + Tailwind)
- react-hook-form + zod

**Backend**:
- Python 3.11+
- FastAPI 0.104+
- SQLAlchemy 2.x (async)
- Celery 5.x
- Redis 7.x

**Libraries**:
- BeautifulSoup4 (HTML parsing)
- spaCy or regex (NLP extraction)
- fuzzywuzzy (fuzzy matching)
- sse-starlette (SSE support)
- dnd-kit (drag-and-drop)

### B. File Structure

**Backend**:
```
apps/api/dealbrain_api/
├── api/v1/
│   ├── events.py                    # RT-002: SSE endpoint
│   └── cpus.py                      # CPU-002: Listing count endpoint
├── services/
│   ├── listings.py                  # RT-003, RT-005: Event publishing, recalc triggers
│   └── catalog_matcher.py           # AI-004: Catalog matching
├── importers/
│   ├── amazon_scraper.py            # AI-001: Enhanced scraping
│   ├── nlp_extractor.py             # AI-002: NLP extraction
│   └── extraction_patterns.yaml     # AI-002: Extraction patterns
└── repositories/
    └── cpus.py                      # CPU-002: Listing count query
```

**Frontend**:
```
apps/web/
├── app/
│   ├── listings/
│   │   ├── page.tsx                 # COL-004: Column selector
│   │   └── [id]/page.tsx            # WF-003: Edit button
│   └── cpus/
│       └── page.tsx                 # CPU-001, CPU-003: Sort & filter
├── components/
│   ├── listings/
│   │   ├── quick-edit-modal.tsx     # WF-001: Expanded modal
│   │   └── listing-view-modal.tsx   # WF-002: Quick edit button
│   ├── cpus/
│   │   ├── cpu-sort-controls.tsx    # CPU-001: Sort controls
│   │   └── cpu-filters.tsx          # CPU-003: Filters
│   └── ui/
│       ├── range-slider.tsx         # UI-001: Dual-handle slider
│       ├── data-table.tsx           # UI-002, COL-003: Dynamic table
│       └── column-selector.tsx      # COL-001: Column selector
└── hooks/
    ├── use-event-stream.ts          # RT-004: SSE client
    └── use-column-preferences.ts    # COL-002: Column persistence
```

### C. Related Documents

- PRD: [ux-improvements-nov-18-v1.md](../../PRDs/enhancements/ux-improvements-nov-18-v1.md)
- Enhancement Request: [11-18.md](../../requests/needs-designed/11-18.md)

### D. Progress Tracking

Progress tracking will be set up at:
`.claude/progress/ux-improvements-nov-18/all-phases-progress.md`

---

**Next Steps**:
1. Review and approve implementation plan
2. Set up progress tracking document
3. Kick off Phase 1 (Critical UI Bug Fixes)
4. Begin parallel Phase 2 planning (Listing Workflow Enhancements)
