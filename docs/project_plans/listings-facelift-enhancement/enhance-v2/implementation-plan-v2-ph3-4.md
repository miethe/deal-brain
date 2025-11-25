# Implementation Plan: Listings Facelift Enhancements V2 - Phases 3-4

**Project:** Deal Brain - Listings Display Enhancement
**Version:** 2.0
**Date:** 2025-10-26
**Status:** Ready for Development
**Related PRD:** `prd-listings-facelift-v2.md`

---

## Phase 3: Visuals & Navigation

**Duration:** Week 3 (7 days)
**Goal:** Add rich visual context and create entity catalog pages

### TASK-010: Create Product Image Component ⚠️ ASSETS NEEDED

**Feature:** FR-1 (Product Image Display)
**Effort:** M
**Dependencies:** None

#### Objective
Create a reusable ProductImage component with fallback hierarchy for the overview modal.

#### Files to Create
- `apps/web/components/listings/product-image-display.tsx`

#### Files to Add (Assets)
- `public/images/fallbacks/intel-logo.svg`
- `public/images/fallbacks/amd-logo.svg`
- `public/images/fallbacks/mini-pc-icon.svg`
- `public/images/fallbacks/desktop-icon.svg`
- `public/images/fallbacks/generic-pc.svg`

#### Implementation Steps
1. Create ProductImageDisplay component
2. Implement fallback hierarchy logic
3. Use Next.js Image component for optimization
4. Add loading skeleton
5. Implement lightbox for full-size view
6. Handle error states gracefully

#### Component Structure
```tsx
import Image from "next/image";
import { useState } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";

interface ProductImageDisplayProps {
  listing: {
    thumbnail_url?: string;
    image_url?: string;
    manufacturer?: string;
    cpu?: { manufacturer?: string };
    form_factor?: string;
  };
  className?: string;
}

export function ProductImageDisplay({ listing, className }: ProductImageDisplayProps) {
  const [imageError, setImageError] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const getImageSrc = (): string => {
    // Level 1: Listing images
    if (!imageError && listing.thumbnail_url) return listing.thumbnail_url;
    if (!imageError && listing.image_url) return listing.image_url;

    // Level 2: Manufacturer logo
    if (listing.manufacturer) {
      const manufacturerSlug = listing.manufacturer.toLowerCase().replace(/\s+/g, '-');
      return `/images/manufacturers/${manufacturerSlug}.svg`;
    }

    // Level 3: CPU manufacturer logo
    if (listing.cpu?.manufacturer) {
      return `/images/fallbacks/${listing.cpu.manufacturer.toLowerCase()}-logo.svg`;
    }

    // Level 4: Form factor icon
    if (listing.form_factor) {
      const formFactorSlug = listing.form_factor.toLowerCase().replace(/\s+/g, '-');
      return `/images/fallbacks/${formFactorSlug}-icon.svg`;
    }

    // Level 5: Generic placeholder
    return '/images/fallbacks/generic-pc.svg';
  };

  const imageSrc = getImageSrc();

  return (
    <>
      <div className={cn("relative cursor-pointer group", className)} onClick={() => setLightboxOpen(true)}>
        {isLoading && <Skeleton className="w-full h-full absolute inset-0" />}
        <Image
          src={imageSrc}
          alt={listing.title || 'Product image'}
          width={400}
          height={300}
          className="rounded-lg object-contain transition-opacity group-hover:opacity-90"
          onLoadingComplete={() => setIsLoading(false)}
          onError={() => setImageError(true)}
        />
      </div>

      {/* Lightbox for full-size view */}
      <Dialog open={lightboxOpen} onOpenChange={setLightboxOpen}>
        <DialogContent className="max-w-4xl">
          <Image
            src={imageSrc}
            alt={listing.title || 'Product image'}
            width={800}
            height={600}
            className="w-full h-auto object-contain"
          />
        </DialogContent>
      </Dialog>
    </>
  );
}
```

#### Testing
- [ ] Image displays in overview modal
- [ ] Fallback hierarchy works for all 5 levels
- [ ] Loading skeleton appears during load
- [ ] Error state triggers fallback
- [ ] Lightbox opens on click
- [ ] Next.js Image optimization is active
- [ ] Images are lazy-loaded

---

### TASK-011: Integrate Product Image in Modal

**Feature:** FR-1 (Product Image Display)
**Effort:** S
**Dependencies:** TASK-010

#### Objective
Add ProductImageDisplay component to the overview modal.

#### Files to Modify
- `apps/web/components/listings/listing-overview-modal.tsx`

#### Implementation Steps
1. Import ProductImageDisplay component
2. Add image section after modal header
3. Adjust spacing and layout
4. Test with various listing types

#### Code Changes
```tsx
import { ProductImageDisplay } from "./product-image-display";

// In ListingOverviewModalComponent, after DialogHeader:
<DialogHeader>
  <DialogTitle className="text-xl">{listing.title}</DialogTitle>
</DialogHeader>

{/* Add product image */}
<ProductImageDisplay listing={listing} className="w-full max-w-md mx-auto" />

<div className="space-y-4">
  {/* Rest of modal content */}
</div>
```

#### Testing
- [ ] Image displays correctly in modal
- [ ] Modal layout remains balanced
- [ ] Image doesn't cause layout shift
- [ ] Lightbox works from modal context

---

### TASK-012: Verify Backend Entity Endpoints ⚠️ BACKEND REQUIRED

**Feature:** FR-7 (Entity Link Routing)
**Effort:** M
**Dependencies:** None

#### Objective
Verify that all required entity detail endpoints exist in the backend. Create any missing endpoints.

#### Required Endpoints
- `GET /v1/cpus/{id}` - Returns CPU details
- `GET /v1/gpus/{id}` - Returns GPU details
- `GET /v1/ram-specs/{id}` - Returns RAM spec details
- `GET /v1/storage-profiles/{id}` - Returns storage profile details

#### Optional Endpoints (for "Used in" section)
- `GET /v1/cpus/{id}/listings` - Returns listings using this CPU
- `GET /v1/gpus/{id}/listings` - Returns listings using this GPU
- `GET /v1/ram-specs/{id}/listings` - Returns listings using this RAM spec
- `GET /v1/storage-profiles/{id}/listings` - Returns listings using this storage profile

#### Backend Files to Check/Create
- `apps/api/dealbrain_api/api/cpus.py`
- `apps/api/dealbrain_api/api/gpus.py`
- `apps/api/dealbrain_api/api/ram_specs.py`
- `apps/api/dealbrain_api/api/storage_profiles.py`

#### Implementation (if endpoints don't exist)
```python
# apps/api/dealbrain_api/api/cpus.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import session_dependency
from ..models import CPU
from dealbrain_core.schemas import CPURead

router = APIRouter(prefix="/v1/cpus", tags=["cpus"])

@router.get("/{cpu_id}", response_model=CPURead)
async def get_cpu(
    cpu_id: int,
    session: AsyncSession = Depends(session_dependency)
):
    cpu = await session.get(CPU, cpu_id)
    if not cpu:
        raise HTTPException(status_code=404, detail="CPU not found")
    return CPURead.model_validate(cpu)
```

#### Testing
- [ ] All entity endpoints return 200 status
- [ ] Response schemas match TypeScript types
- [ ] Endpoints handle 404 gracefully
- [ ] Performance is acceptable (< 200ms)

---

### TASK-013: Create CPU Detail Page ⚠️ NEW ROUTES

**Feature:** FR-7 (Entity Link Routing)
**Effort:** L
**Dependencies:** TASK-012

#### Objective
Create a detail page for CPU entities at `/catalog/cpus/[id]`.

#### Files to Create
- `apps/web/app/catalog/cpus/[id]/page.tsx`
- `apps/web/app/catalog/cpus/[id]/loading.tsx`
- `apps/web/app/catalog/cpus/[id]/not-found.tsx`
- `apps/web/components/catalog/cpu-detail-layout.tsx`

#### Implementation Steps
1. Create catalog directory structure
2. Implement server component for data fetching
3. Create CPU detail layout component
4. Display CPU specifications
5. Show "Used in" listings section
6. Add comparison with similar CPUs (optional, Phase 4)

#### Page Structure
```tsx
// apps/web/app/catalog/cpus/[id]/page.tsx
import { notFound } from "next/navigation";
import { apiFetch } from "@/lib/utils";
import { CPUDetailLayout } from "@/components/catalog/cpu-detail-layout";
import type { CPU } from "@/types/cpu";

interface PageProps {
  params: { id: string };
}

async function getCPU(id: string): Promise<CPU | null> {
  try {
    return await apiFetch(`/v1/cpus/${id}`);
  } catch {
    return null;
  }
}

export default async function CPUDetailPage({ params }: PageProps) {
  const cpu = await getCPU(params.id);
  if (!cpu) notFound();
  return <CPUDetailLayout cpu={cpu} />;
}
```

#### Layout Component
```tsx
// apps/web/components/catalog/cpu-detail-layout.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface CPUDetailLayoutProps {
  cpu: CPU;
}

export function CPUDetailLayout({ cpu }: CPUDetailLayoutProps) {
  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{cpu.model}</h1>
        <p className="text-muted-foreground">{cpu.manufacturer}</p>
      </div>

      {/* Specifications */}
      <Card>
        <CardHeader>
          <CardTitle>Specifications</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <SpecField label="Cores" value={cpu.cores} />
            <SpecField label="Threads" value={cpu.threads} />
            <SpecField label="Base Clock" value={`${cpu.base_clock_ghz} GHz`} />
            <SpecField label="Boost Clock" value={`${cpu.boost_clock_ghz} GHz`} />
            <SpecField label="TDP" value={`${cpu.tdp_watts}W`} />
            <SpecField label="Generation" value={cpu.generation} />
          </div>
        </CardContent>
      </Card>

      {/* Benchmark Scores */}
      <Card>
        <CardHeader>
          <CardTitle>Benchmark Scores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard label="CPU Mark (Multi)" value={cpu.cpu_mark} />
            <MetricCard label="CPU Mark (Single)" value={cpu.single_thread_rating} />
            <MetricCard label="iGPU Mark" value={cpu.igpu_mark} />
          </div>
        </CardContent>
      </Card>

      {/* Used In Listings */}
      <Card>
        <CardHeader>
          <CardTitle>Used In Listings</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Fetch and display listings using this CPU */}
        </CardContent>
      </Card>
    </div>
  );
}
```

#### Testing
- [ ] CPU detail page loads without 404
- [ ] All specifications display correctly
- [ ] Benchmark scores are formatted properly
- [ ] "Used in" listings section shows related listings
- [ ] Page is mobile responsive
- [ ] Back navigation works correctly

---

### TASK-014: Create GPU Detail Page

**Feature:** FR-7 (Entity Link Routing)
**Effort:** L
**Dependencies:** TASK-012

#### Objective
Create a detail page for GPU entities at `/catalog/gpus/[id]`.

#### Files to Create
- `apps/web/app/catalog/gpus/[id]/page.tsx`
- `apps/web/app/catalog/gpus/[id]/loading.tsx`
- `apps/web/app/catalog/gpus/[id]/not-found.tsx`
- `apps/web/components/catalog/gpu-detail-layout.tsx`

#### Implementation
Follow similar pattern to TASK-013, adapted for GPU specifications:
- Model name, manufacturer
- GPU type (integrated/discrete)
- VRAM capacity and type
- Benchmark scores (3D Mark, etc.)
- Architecture and generation
- "Used in" listings

#### Testing
- [ ] GPU detail page loads correctly
- [ ] Integrated/discrete badge displays
- [ ] VRAM info is formatted correctly
- [ ] Related listings show correctly

---

### TASK-015: Create RAM Spec Detail Page

**Feature:** FR-7 (Entity Link Routing)
**Effort:** M
**Dependencies:** TASK-012

#### Objective
Create a detail page for RAM spec entities at `/catalog/ram-specs/[id]`.

#### Files to Create
- `apps/web/app/catalog/ram-specs/[id]/page.tsx`
- `apps/web/app/catalog/ram-specs/[id]/loading.tsx`
- `apps/web/app/catalog/ram-specs/[id]/not-found.tsx`
- `apps/web/components/catalog/ram-spec-detail-layout.tsx`

#### RAM Spec Fields to Display
- Capacity (GB)
- Type (DDR4, DDR5, etc.)
- Speed (MHz)
- Latency (CAS latency)
- Voltage
- Configuration (e.g., "2x8GB")
- "Used in" listings

#### Testing
- [ ] RAM spec detail page loads correctly
- [ ] All specifications display correctly
- [ ] Related listings show correctly

---

### TASK-016: Create Storage Profile Detail Page

**Feature:** FR-7 (Entity Link Routing)
**Effort:** M
**Dependencies:** TASK-012

#### Objective
Create a detail page for storage profile entities at `/catalog/storage-profiles/[id]`.

#### Files to Create
- `apps/web/app/catalog/storage-profiles/[id]/page.tsx`
- `apps/web/app/catalog/storage-profiles/[id]/loading.tsx`
- `apps/web/app/catalog/storage-profiles/[id]/not-found.tsx`
- `apps/web/components/catalog/storage-profile-detail-layout.tsx`

#### Storage Profile Fields to Display
- Capacity (GB/TB)
- Type (NVMe, SSD, HDD, etc.)
- Interface (M.2, SATA, etc.)
- Sequential read/write speeds
- Random read/write IOPS
- Form factor
- "Used in" listings

#### Testing
- [ ] Storage profile detail page loads correctly
- [ ] Performance metrics are formatted correctly
- [ ] Related listings show correctly

---

### TASK-017: Update EntityLink Component

**Feature:** FR-7 (Entity Link Routing)
**Effort:** S
**Dependencies:** TASK-013, TASK-014, TASK-015, TASK-016

#### Objective
Update the EntityLink component to route to the new catalog detail pages.

#### Files to Modify
- `apps/web/components/listings/entity-link.tsx`

#### Implementation Steps
1. Map entity types to catalog routes
2. Update href generation logic
3. Verify all entity links use EntityLink component

#### Code Changes
```tsx
import Link from "next/link";
import { cn } from "@/lib/utils";

interface EntityLinkProps {
  entityType: 'cpu' | 'gpu' | 'ram-spec' | 'storage-profile';
  entityId: number;
  children: React.ReactNode;
  className?: string;
}

export function EntityLink({ entityType, entityId, children, className }: EntityLinkProps) {
  const routeMap = {
    'cpu': '/catalog/cpus',
    'gpu': '/catalog/gpus',
    'ram-spec': '/catalog/ram-specs',
    'storage-profile': '/catalog/storage-profiles',
  };

  const href = `${routeMap[entityType]}/${entityId}`;

  return (
    <Link
      href={href}
      className={cn(
        "text-primary hover:underline font-medium",
        className
      )}
    >
      {children}
    </Link>
  );
}
```

#### Testing
- [ ] All entity links route correctly
- [ ] No 404 errors when clicking entity links
- [ ] Links maintain proper styling
- [ ] Back navigation works from entity pages

---

### TASK-018: Phase 3 Testing & Integration

**Effort:** L
**Dependencies:** TASK-010, TASK-011, TASK-012, TASK-013, TASK-014, TASK-015, TASK-016, TASK-017

#### Testing Checklist
- [ ] Product images display in overview modal
- [ ] All entity catalog pages load correctly
- [ ] Entity links navigate without errors
- [ ] "Used in" listings sections show correct data
- [ ] No regressions in existing functionality
- [ ] TypeScript compiles without errors
- [ ] Accessibility audit passes
- [ ] Mobile responsive behavior verified
- [ ] Performance benchmarked (image loading, page navigation)

---

## Phase 4: Polish & Testing

**Duration:** Week 4 (5 days)
**Goal:** Production-ready enhancements with comprehensive testing

### TASK-019: End-to-End Testing

**Effort:** L

#### Test Scenarios
1. **Overview Modal Journey**
   - Open modal from listings table
   - Verify product image loads
   - Hover over entity tooltips
   - Click entity links to navigate to catalog pages
   - Return to listings page

2. **Detail Page Journey**
   - Navigate to listing detail page
   - Verify overview tooltips work
   - Navigate to specifications tab
   - View valuation tab with rules
   - Click entity links

3. **Entity Catalog Journey**
   - Navigate to CPU detail page
   - View specifications
   - Click "Used in" listing
   - Navigate back to CPU page

#### Testing Tools
- Playwright for E2E tests
- React Testing Library for component tests
- Jest for unit tests

#### Files to Create
- `apps/web/__tests__/e2e/listings-modal.spec.ts`
- `apps/web/__tests__/e2e/detail-page.spec.ts`
- `apps/web/__tests__/e2e/entity-catalog.spec.ts`

---

### TASK-020: Accessibility Audit

**Effort:** M

#### Audit Checklist
- [ ] Keyboard navigation works for all interactive elements
- [ ] Focus indicators are visible
- [ ] Screen reader announcements are appropriate
- [ ] Color contrast meets WCAG AA standards
- [ ] Images have proper alt text
- [ ] Forms have proper labels
- [ ] ARIA attributes are used correctly

#### Tools
- axe DevTools
- WAVE browser extension
- Lighthouse accessibility audit

---

### TASK-021: Performance Optimization

**Effort:** M

#### Optimization Areas
1. **Image Loading**
   - Implement lazy loading
   - Optimize image sizes
   - Use WebP format where supported
   - Measure Core Web Vitals impact

2. **Component Rendering**
   - Add React.memo where appropriate
   - Optimize re-renders
   - Profile with React DevTools

3. **API Calls**
   - Implement proper caching strategies
   - Debounce expensive operations
   - Optimize React Query configuration

#### Performance Metrics
- Lighthouse score > 90
- Time to Interactive < 3s
- Largest Contentful Paint < 2.5s

---

### TASK-022: Bug Fixes & Refinements

**Effort:** M

#### Review Areas
- Edge case handling
- Error state improvements
- Loading state refinements
- Visual polish
- Code cleanup

---

### TASK-023: Documentation Updates

**Effort:** S

#### Documentation to Update
- Component documentation (JSDoc)
- API endpoint documentation
- User-facing changelog
- Developer README

---

### TASK-024: Production Deployment

**Effort:** S

#### Pre-Deployment Checklist
- [ ] All tests passing
- [ ] TypeScript compilation successful
- [ ] No console errors or warnings
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Rollback plan documented

#### Deployment Steps
1. Merge feature branch to main
2. Run database migrations
3. Deploy backend services
4. Deploy frontend application
5. Monitor error tracking
6. Verify in production

---

### Related Resources
- PRD: `docs/project_plans/listings-facelift-enhancement/enhance-v2/prd-listings-facelift-v2.md`
- Implementation Plan Phases 1-2: `docs/project_plans/listings-facelift-enhancement/enhance-v2/implementation-plan-v2.md`
- Tooltip Investigation: `docs/project_plans/listings-facelift-enhancement/investigations/tooltip-investigation-report.md`
- Original Requirements: `docs/project_plans/listings-facelift-enhancement/enhance-v2/listings-facelift-enhancements-v2.md`
