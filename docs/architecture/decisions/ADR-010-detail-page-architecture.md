# ADR-010: Detail Page Architecture

**Status:** Accepted
**Date:** 2025-10-23
**Context:** Phase 4 - Listings Facelift Enhancement

---

## Context

We need to create a comprehensive detail page for listings at `/listings/[id]` that displays rich product information, interactive entity relationships, and tabbed content navigation. This page is the foundation for Phases 5-7 of the Listings Facelift Enhancement.

---

## Decision

### 1. Server Component Architecture for Detail Page

**Decision:** Implement the detail page route as a Next.js Server Component with server-side data fetching.

**Rationale:**
- **Performance:** Server-side rendering improves Largest Contentful Paint (LCP) by delivering fully-rendered HTML
- **SEO:** Search engines can crawl listing details with full metadata
- **Bundle Size:** Reduces client-side JavaScript by keeping data fetching on the server
- **Simplicity:** Eliminates need for client-side loading states for initial page render

**Implementation:**
```tsx
// apps/web/app/listings/[id]/page.tsx
export default async function ListingDetailPage({ params }: { params: { id: string } }) {
  const listing = await apiFetch(`/v1/listings/${params.id}`);
  return <DetailPageLayout listing={listing} />;
}
```

**Trade-offs:**
- ✅ Faster initial page load
- ✅ Better SEO and social sharing
- ✅ Reduced client bundle size
- ⚠️ Requires careful error handling (use error.tsx and not-found.tsx)
- ⚠️ Dynamic data requires client components for mutations

---

### 2. Eager Loading Strategy for Backend

**Decision:** Use SQLAlchemy `lazy="joined"` for all critical relationships in the Listing model.

**Rationale:**
- **Performance:** Prevents N+1 queries by loading all relationships in a single query
- **Consistency:** The Listing model already uses `lazy="joined"` for CPU, GPU, RAM, Storage, and Ports relationships
- **Response Time:** Ensures API response time stays under 500ms (p95) even with full relationship data

**Current Implementation (Already Exists):**
```python
# apps/api/dealbrain_api/models/core.py - Listing model
cpu: Mapped[Cpu | None] = relationship(back_populates="listings", lazy="joined")
gpu: Mapped[Gpu | None] = relationship(back_populates="listings", lazy="joined")
ram_spec: Mapped[RamSpec | None] = relationship(back_populates="listings", lazy="joined")
primary_storage_profile: Mapped[StorageProfile | None] = relationship(back_populates="listings_primary", lazy="joined")
ports_profile: Mapped[PortsProfile | None] = relationship(back_populates="listings", lazy="joined")
```

**Enhancement Needed:**
- Add explicit 404 handling in GET /v1/listings/{id} endpoint
- Verify all nested relationships are properly loaded (e.g., PortsProfile.ports)

**Trade-offs:**
- ✅ No N+1 queries
- ✅ Predictable response times
- ✅ Single database roundtrip
- ⚠️ Slightly larger response payload (~100-150KB)
- ⚠️ Not suitable for list endpoints (use selectinload there)

---

### 3. Image Fallback Hierarchy

**Decision:** Implement a three-tier fallback strategy for product images:
1. **Primary:** `listing.thumbnail_url` or `listing.image_url` (from import/upload)
2. **Fallback 1:** Manufacturer logo based on CPU/GPU manufacturer
3. **Fallback 2:** Generic PC/workstation icon from lucide-react

**Rationale:**
- **User Experience:** Always show a visual representation, even without product images
- **Brand Recognition:** Manufacturer logos help users identify products
- **Graceful Degradation:** System remains functional without images

**Implementation:**
```tsx
// apps/web/components/listings/product-image.tsx
const imageUrl = listing.thumbnail_url
  || listing.image_url
  || getManufacturerLogo(listing.manufacturer)
  || '/icons/pc-generic.svg';
```

**Trade-offs:**
- ✅ Always displays a meaningful image
- ✅ Improves visual consistency
- ⚠️ Requires manufacturer logo assets
- ⚠️ May need to handle external image loading errors

---

### 4. URL-Based Tab State Management

**Decision:** Use URL query parameters for active tab state (`?tab=specifications`).

**Rationale:**
- **Shareability:** Users can share links to specific tabs (e.g., `/listings/123?tab=valuation`)
- **Browser History:** Back button navigates between tabs correctly
- **Bookmarking:** Users can bookmark specific tab views
- **SEO:** Search engines can index different tab content

**Implementation:**
```tsx
// apps/web/components/listings/detail-page-tabs.tsx
const searchParams = useSearchParams();
const activeTab = searchParams.get('tab') || 'specifications';
```

**Trade-offs:**
- ✅ Shareable URLs
- ✅ Browser history integration
- ✅ SEO-friendly
- ⚠️ Requires client component for tab navigation (useSearchParams)
- ⚠️ Must handle invalid tab names gracefully

---

### 5. Responsive Design Strategy

**Decision:** Use mobile-first responsive design with three breakpoints:
- **Mobile:** < 640px (single column, stacked layout)
- **Tablet:** 640px - 1024px (2-column grid for cards)
- **Desktop:** > 1024px (full layout with sidebar)

**Rationale:**
- **Mobile Usage:** Significant portion of users access from mobile devices
- **Progressive Enhancement:** Start with simplest layout, enhance for larger screens
- **Tailwind CSS:** Aligns with Tailwind's default breakpoint system

**Implementation:**
```tsx
// Hero section responsive layout
<div className="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-6">
  <ProductImage />
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    {/* Summary cards */}
  </div>
</div>
```

**Trade-offs:**
- ✅ Consistent with mobile-first best practices
- ✅ Works on all screen sizes
- ✅ Leverages Tailwind CSS effectively
- ⚠️ Requires testing on multiple devices
- ⚠️ Some components may need mobile-specific variants

---

## Consequences

### Positive

1. **Performance:** LCP < 2.5s with server-side rendering and eager-loaded data
2. **User Experience:** Smooth page load with loading skeletons, no layout shifts
3. **Maintainability:** Clear separation between server and client components
4. **SEO:** Fully indexable listing detail pages with proper meta tags
5. **Scalability:** Architecture supports future enhancements (Phases 5-7)

### Negative

1. **Complexity:** Server Components require careful error boundary management
2. **Testing:** Need to test both server-side and client-side rendering paths
3. **State Management:** Tab state requires client component, breaking pure server component model

### Neutral

1. **Bundle Size:** Tradeoff between server rendering and client interactivity
2. **Caching:** Need to implement proper cache invalidation strategy for detail pages

---

## Implementation Tasks

**Phase 4 Tasks:**
- TASK-401: Enhance GET /v1/listings/{id} endpoint with explicit 404 handling
- TASK-402: Create detail page route as Server Component
- TASK-403: Create loading.tsx skeleton
- TASK-404: Create not-found.tsx page
- TASK-405: Create DetailPageLayout component
- TASK-406: Create BreadcrumbNav component
- TASK-407: Create DetailPageHero component
- TASK-408: Create ProductImage component with fallback hierarchy
- TASK-409: Create DetailPageTabs component with URL state
- TASK-410: Implement responsive design across all components

---

## References

- [Next.js Server Components](https://nextjs.org/docs/app/building-your-application/rendering/server-components)
- [SQLAlchemy Relationship Loading Techniques](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- [Tailwind CSS Responsive Design](https://tailwindcss.com/docs/responsive-design)
- Phase 4 Implementation Plan: `docs/project_plans/listings-facelift-enhancement/listings-facelift-implementation-plan.md`
- Detail Page Requirements: `docs/project_plans/listings-facelift-enhancement/requirements/detail-page.md`

---

**Signed-off by:** Lead Architect
**Reviewed by:** N/A (initial decision)
**Effective Date:** 2025-10-23
