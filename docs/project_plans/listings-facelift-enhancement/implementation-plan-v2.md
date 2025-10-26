# Implementation Plan: Listings Facelift Enhancements V2

**Project:** Deal Brain - Listings Display Enhancement
**Version:** 2.0
**Date:** 2025-10-26
**Status:** Ready for Development
**Related PRD:** `prd-listings-facelift-v2.md`

---

## Overview

This implementation plan provides a phased approach to delivering the Listings Facelift Enhancements V2. The plan is organized into 4 phases aligned with the PRD timeline, with clear task dependencies and effort estimates.

### Tech Stack Reference

- **Frontend:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS
- **Backend:** FastAPI, Python 3.11+, async SQLAlchemy, Alembic
- **UI Components:** shadcn/ui, Radix UI primitives
- **State Management:** React Query (@tanstack/react-query)
- **Icons:** lucide-react
- **Testing:** pytest (backend), Jest + React Testing Library (frontend)

---

## Phase 1: Foundation

**Duration:** Week 1 (5 days)
**Goal:** Enhance modal and detail page with better information density and transparency

### TASK-001: Verify and Enhance GPU Display in Modal ✅ READY

**Feature:** FR-2 (Additional Modal Information)
**Effort:** S
**Dependencies:** None

#### Objective
Ensure GPU information is prominently displayed in the overview modal header/info section.

#### Files to Modify
- `apps/web/components/listings/listing-overview-modal.tsx`

#### Implementation Steps
1. Review current GPU display (lines 150-169)
2. Verify GPU name is shown with proper prominence
3. Add "(Integrated)" badge for iGPUs when `gpu.type === 'integrated'`
4. Ensure GPU tooltip is working correctly

#### Code Changes
```tsx
// In Hardware section, enhance GPU display
{listing.gpu_name && (
  <div className="flex flex-col">
    <span className="text-xs text-muted-foreground">GPU</span>
    <span className="font-medium">
      {listing.gpu?.id ? (
        <EntityTooltip
          entityType="gpu"
          entityId={listing.gpu.id}
          tooltipContent={(gpuData) => <GpuTooltipContent gpu={gpuData} />}
          fetchData={fetchEntityData}
          variant="inline"
        >
          {listing.gpu_name}
          {listing.gpu?.type === 'integrated' && (
            <Badge variant="outline" className="ml-1 text-xs">Integrated</Badge>
          )}
        </EntityTooltip>
      ) : (
        listing.gpu_name
      )}
    </span>
  </div>
)}
```

#### Testing
- [ ] GPU name displays prominently in modal
- [ ] Integrated GPU shows badge
- [ ] GPU tooltip works on hover
- [ ] Layout remains balanced with badge

---

### TASK-002: Enhance Clickable URL Links ✅ READY

**Feature:** FR-2 (Additional Modal Information)
**Effort:** S
**Dependencies:** None

#### Objective
Verify and enhance URL link display in overview modal.

#### Files to Modify
- `apps/web/components/listings/listing-overview-modal.tsx`

#### Implementation Steps
1. Review current URL display (lines 263-299)
2. Add link count indicator if more than 3 additional URLs
3. Improve styling and spacing of link section
4. Ensure all links have proper security attributes

#### Code Changes
```tsx
// In Links section, add count indicator
<Section title={`Links${listing.other_urls && listing.other_urls.length > 3 ? ` (${listing.other_urls.length + 1})` : ''}`}>
  <div className="space-y-2">
    {listing.listing_url && (
      <div className="flex items-center gap-2">
        <ExternalLink className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        <a
          href={listing.listing_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-primary hover:underline break-all"
        >
          View Original Listing
        </a>
      </div>
    )}
    {listing.other_urls && listing.other_urls.map((link, index) => (
      <div key={index} className="flex items-center gap-2">
        <ExternalLink className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        <a
          href={link.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-primary hover:underline break-all"
        >
          {link.label || `Additional Link ${index + 1}`}
        </a>
      </div>
    ))}
  </div>
</Section>
```

#### Testing
- [ ] All URLs are clickable
- [ ] Links open in new tab with security attributes
- [ ] Long URLs wrap correctly
- [ ] Link count indicator shows when > 3 links

---

### TASK-003: Add Detail Page Overview Tooltips ✅ READY

**Feature:** FR-4 (Detail Page Overview Tooltips)
**Effort:** M
**Dependencies:** None

#### Objective
Add hover tooltips to entity links in the detail page overview/hero section.

#### Files to Modify
- `apps/web/components/listings/detail-page-hero.tsx` (or equivalent overview component)

#### Implementation Steps
1. Locate the detail page overview/hero section component
2. Identify entity links (CPU, GPU, RAM, Storage)
3. Wrap entity links with `EntityTooltip` component
4. Use existing tooltip content components
5. Verify API endpoints are correct

#### Code Changes
```tsx
import { EntityTooltip } from "./entity-tooltip";
import { fetchEntityData } from "@/lib/api/entities";
import { CpuTooltipContent } from "./tooltips/cpu-tooltip-content";
import { GpuTooltipContent } from "./tooltips/gpu-tooltip-content";
import { RamSpecTooltipContent } from "./tooltips/ram-spec-tooltip-content";
import { StorageProfileTooltipContent } from "./tooltips/storage-profile-tooltip-content";

// In overview section, wrap CPU link
{listing.cpu?.id ? (
  <EntityTooltip
    entityType="cpu"
    entityId={listing.cpu.id}
    tooltipContent={(cpu) => <CpuTooltipContent cpu={cpu} />}
    fetchData={fetchEntityData}
    variant="inline"
  >
    {listing.cpu_name}
  </EntityTooltip>
) : (
  listing.cpu_name
)}

// Repeat pattern for GPU, RAM, Storage
```

#### Testing
- [ ] CPU tooltip appears on hover in overview
- [ ] GPU tooltip appears on hover in overview
- [ ] RAM tooltip appears on hover in overview
- [ ] Storage tooltip appears on hover in overview
- [ ] Tooltips use correct API endpoints
- [ ] Tooltip delay is 200ms

---

### TASK-004: Display Valuation Rules in Valuation Tab ✅ READY

**Feature:** FR-6 (Valuation Tab Rules Display)
**Effort:** M
**Dependencies:** None

#### Objective
Show all contributing rules (active and inactive) in the Valuation tab instead of "No rule-based adjustments" message.

#### Files to Modify
- `apps/web/components/listings/listing-valuation-tab.tsx`

#### Implementation Steps
1. Fetch valuation breakdown from `/v1/listings/{id}/valuation-breakdown`
2. Parse `adjustments` array (includes both active and inactive rules)
3. Replace empty state message with rules list
4. Display rules in table or accordion format
5. Color-code adjustment amounts (green for positive, red for negative, gray for zero)
6. Show rule descriptions in expandable sections

#### Code Changes
```tsx
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/utils";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

interface ValuationAdjustment {
  rule_id: number | null;
  rule_name: string;
  rule_description: string | null;
  rule_group_name: string | null;
  adjustment_amount: number;
}

function ValuationRulesList({ listingId }: { listingId: number }) {
  const { data: breakdown } = useQuery({
    queryKey: ['valuation-breakdown', listingId],
    queryFn: () => apiFetch(`/v1/listings/${listingId}/valuation-breakdown`),
  });

  if (!breakdown?.adjustments || breakdown.adjustments.length === 0) {
    return <p className="text-sm text-muted-foreground">No valuation rules available</p>;
  }

  return (
    <div className="space-y-2">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Rule</TableHead>
            <TableHead>Group</TableHead>
            <TableHead className="text-right">Adjustment</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {breakdown.adjustments.map((adj: ValuationAdjustment, idx: number) => (
            <TableRow key={idx}>
              <TableCell>
                <div className="flex flex-col">
                  <span className="font-medium">{adj.rule_name}</span>
                  {adj.rule_description && (
                    <span className="text-xs text-muted-foreground">{adj.rule_description}</span>
                  )}
                </div>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {adj.rule_group_name || '—'}
              </TableCell>
              <TableCell className="text-right">
                <span className={cn(
                  "font-medium",
                  adj.adjustment_amount > 0 && "text-green-600",
                  adj.adjustment_amount < 0 && "text-red-600",
                  adj.adjustment_amount === 0 && "text-muted-foreground"
                )}>
                  {adj.adjustment_amount > 0 && '+'}
                  ${adj.adjustment_amount.toFixed(2)}
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
```

#### Testing
- [ ] All rules display in valuation tab
- [ ] Active rules show non-zero adjustments
- [ ] Inactive rules show zero adjustments
- [ ] Color coding is correct
- [ ] Rule descriptions are visible
- [ ] Grouped rules show group name

---

### TASK-005: Phase 1 Testing & Integration

**Effort:** M
**Dependencies:** TASK-001, TASK-002, TASK-003, TASK-004

#### Testing Checklist
- [ ] Overview modal displays all enhancements correctly
- [ ] Detail page overview tooltips work
- [ ] Valuation tab shows rules list
- [ ] No console errors or warnings
- [ ] TypeScript compiles without errors
- [ ] Accessibility audit passes (keyboard navigation, screen reader)
- [ ] Mobile responsive behavior verified
- [ ] Performance impact measured (no significant degradation)

---

## Phase 2: Structure

**Duration:** Week 2 (5 days)
**Goal:** Reorganize specifications tab with better UX and optimize detail page layout

### TASK-006: Create Specifications Subsections ⚠️ COMPLEX

**Feature:** FR-3 (Enhanced Specifications Tab)
**Effort:** L
**Dependencies:** None

#### Objective
Reorganize the Specifications tab into logical subsections (Compute, Memory, Storage, Connectivity) with empty state handling.

#### Files to Modify
- `apps/web/components/listings/specifications-tab.tsx`

#### Implementation Steps
1. Restructure component into four main subsections
2. Create `SpecificationSubsection` reusable component
3. Implement empty state with "No data available" + "Add +" button
4. Maintain responsive grid layout
5. Ensure visual consistency

#### Code Structure
```tsx
interface SubsectionProps {
  title: string;
  children: React.ReactNode;
  isEmpty?: boolean;
  onAddClick?: () => void;
}

function SpecificationSubsection({ title, children, isEmpty, onAddClick }: SubsectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center justify-between">
          {title}
          {isEmpty && onAddClick && (
            <Button variant="ghost" size="sm" onClick={onAddClick}>
              Add +
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <p className="text-sm text-muted-foreground">No data available</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {children}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function SpecificationsTab({ listing }: SpecificationsTabProps) {
  const hasComputeData = listing.cpu || listing.gpu;
  const hasMemoryData = listing.ram_gb || listing.ram_type;
  const hasStorageData = listing.primary_storage_gb || listing.secondary_storage_gb;
  const hasConnectivityData = listing.ports_profile;

  return (
    <div className="space-y-6">
      {/* Compute Subsection */}
      <SpecificationSubsection
        title="Compute"
        isEmpty={!hasComputeData}
        onAddClick={() => console.log('Add compute data')}
      >
        {listing.cpu && <FieldGroup label="CPU" ... />}
        {listing.gpu && <FieldGroup label="GPU" ... />}
        {/* Performance scores */}
      </SpecificationSubsection>

      {/* Memory Subsection */}
      <SpecificationSubsection
        title="Memory"
        isEmpty={!hasMemoryData}
        onAddClick={() => console.log('Add memory data')}
      >
        {listing.ram_gb && <FieldGroup label="RAM Capacity" ... />}
        {listing.ram_type && <FieldGroup label="RAM Type" ... />}
      </SpecificationSubsection>

      {/* Storage Subsection */}
      <SpecificationSubsection
        title="Storage"
        isEmpty={!hasStorageData}
        onAddClick={() => console.log('Add storage data')}
      >
        {listing.primary_storage_gb && <FieldGroup label="Primary Storage" ... />}
        {listing.secondary_storage_gb && <FieldGroup label="Secondary Storage" ... />}
      </SpecificationSubsection>

      {/* Connectivity Subsection */}
      <SpecificationSubsection
        title="Connectivity"
        isEmpty={!hasConnectivityData}
        onAddClick={() => console.log('Add connectivity data')}
      >
        {/* Ports display */}
      </SpecificationSubsection>
    </div>
  );
}
```

#### Testing
- [ ] Four subsections render correctly
- [ ] Empty subsections show placeholder message
- [ ] "Add +" button appears for empty subsections
- [ ] Non-empty subsections display data correctly
- [ ] Grid layout is responsive
- [ ] Spacing and visual hierarchy are correct

---

### TASK-007: Create Quick-Add Dialogs ⚠️ COMPLEX

**Feature:** FR-3 (Enhanced Specifications Tab)
**Effort:** XL
**Dependencies:** TASK-006

#### Objective
Create quick-add dialogs for each subsection type to allow rapid data entry.

#### Files to Create
- `apps/web/components/listings/quick-add-compute-dialog.tsx`
- `apps/web/components/listings/quick-add-memory-dialog.tsx`
- `apps/web/components/listings/quick-add-storage-dialog.tsx`
- `apps/web/components/listings/quick-add-connectivity-dialog.tsx`

#### Implementation Steps
1. Create dialog component for each data type
2. Use React Hook Form for form state management
3. Include field validation
4. Implement PATCH request to update listing
5. Show success/error toast after submission
6. Refresh listing data after successful update

#### Example: Quick-Add Compute Dialog
```tsx
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

interface QuickAddComputeDialogProps {
  listingId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function QuickAddComputeDialog({ listingId, open, onOpenChange }: QuickAddComputeDialogProps) {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const updateListing = useMutation({
    mutationFn: (data: any) =>
      apiFetch(`/v1/listings/${listingId}`, {
        method: 'PATCH',
        body: JSON.stringify({ fields: data }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listing', listingId] });
      toast({ title: 'Success', description: 'Compute data updated' });
      onOpenChange(false);
    },
    onError: () => {
      toast({ title: 'Error', description: 'Failed to update', variant: 'destructive' });
    },
  });

  const onSubmit = (data: any) => {
    updateListing.mutate(data);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Compute Data</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="cpu_id">CPU</Label>
            <Input id="cpu_id" type="number" {...register("cpu_id")} />
          </div>
          <div>
            <Label htmlFor="gpu_id">GPU</Label>
            <Input id="gpu_id" type="number" {...register("gpu_id")} />
          </div>
          <Button type="submit" disabled={updateListing.isPending}>
            {updateListing.isPending ? 'Saving...' : 'Save'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

#### Testing
- [ ] Dialogs open when "Add +" button clicked
- [ ] Form validation works correctly
- [ ] Successful submission updates listing
- [ ] Toast notifications appear
- [ ] Dialog closes after success
- [ ] Errors are handled gracefully

---

### TASK-008: Optimize Detail Page Layout ⚠️ DESIGN REVIEW

**Feature:** FR-5 (Layout Optimization)
**Effort:** M
**Dependencies:** None

#### Objective
Audit and optimize the detail page layout for better space utilization and information hierarchy.

#### Files to Modify
- `apps/web/components/listings/detail-page-layout.tsx`
- `apps/web/components/listings/detail-page-hero.tsx`

#### Implementation Steps
1. Conduct layout audit (measure current spacing, hierarchy)
2. Reduce vertical spacing between sections (24px → 16px)
3. Implement 2-column layout for overview on wider screens
4. Move metadata to collapsed/accordion section
5. Increase font sizes for primary metrics
6. Add subtle visual separators

#### Layout Changes
```tsx
// Before: Single column, lots of whitespace
<div className="space-y-8">
  <HeroSection />
  <TabsSection />
</div>

// After: Tighter spacing, 2-column layout on desktop
<div className="space-y-4">
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <HeroSection />
    <PricingMetrics />
  </div>
  <Separator />
  <TabsSection />
</div>
```

#### Design Tokens
- Spacing: 16px between major sections (was 24px)
- Pricing font size: text-3xl (was text-2xl)
- Metrics font size: text-lg (was text-base)
- Separator: subtle border (bg-border)

#### Testing
- [ ] Layout is visually balanced
- [ ] Most important info is prominent
- [ ] Reduced scrolling needed on desktop
- [ ] Mobile layout remains single-column
- [ ] Touch targets meet 44x44px minimum
- [ ] Font sizes are readable on all devices

---

### TASK-009: Phase 2 Testing & Integration

**Effort:** M
**Dependencies:** TASK-006, TASK-007, TASK-008

#### Testing Checklist
- [ ] Specifications tab subsections render correctly
- [ ] Quick-add dialogs work for all types
- [ ] Detail page layout is optimized
- [ ] No regressions in existing functionality
- [ ] TypeScript compiles without errors
- [ ] Accessibility audit passes
- [ ] Mobile responsive behavior verified
- [ ] Performance benchmarked

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

## Risk Mitigation

### High-Risk Items

**RISK-001: Backend entity endpoints don't exist**
- **Mitigation:** Complete TASK-012 early in Phase 3
- **Fallback:** Create minimal endpoints with placeholder data

**RISK-002: Image loading impacts performance**
- **Mitigation:** Use Next.js Image optimization, lazy loading
- **Fallback:** Disable images by default, add opt-in toggle

**RISK-003: Quick-add dialogs increase complexity**
- **Mitigation:** Start with simple forms, iterate based on feedback
- **Fallback:** Link to full edit page instead of inline dialogs

---

## Success Criteria

### Definition of Done
- [ ] All 7 feature requirements implemented
- [ ] 80%+ test coverage
- [ ] Accessibility audit passes
- [ ] Performance metrics meet targets
- [ ] Zero critical bugs
- [ ] Documentation updated
- [ ] Product owner approval
- [ ] Production deployment successful

---

## Appendix

### Effort Estimates
- S (Small): 2-4 hours
- M (Medium): 4-8 hours
- L (Large): 1-2 days
- XL (Extra Large): 2-3 days

### Dependencies Graph
```
Phase 1 (Foundation)
  TASK-001 (GPU Display) → TASK-005 (Testing)
  TASK-002 (URL Links) → TASK-005
  TASK-003 (Tooltips) → TASK-005
  TASK-004 (Valuation Rules) → TASK-005

Phase 2 (Structure)
  TASK-006 (Subsections) → TASK-007 (Quick-Add) → TASK-009 (Testing)
  TASK-008 (Layout) → TASK-009

Phase 3 (Visuals & Navigation)
  TASK-010 (Image Component) → TASK-011 (Modal Integration) → TASK-018 (Testing)
  TASK-012 (Backend Endpoints) → TASK-013 (CPU Page) → TASK-018
  TASK-012 → TASK-014 (GPU Page) → TASK-018
  TASK-012 → TASK-015 (RAM Page) → TASK-018
  TASK-012 → TASK-016 (Storage Page) → TASK-018
  TASK-013, TASK-014, TASK-015, TASK-016 → TASK-017 (Entity Link) → TASK-018

Phase 4 (Polish)
  All previous phases → TASK-019, TASK-020, TASK-021 → TASK-024 (Deploy)
```

### Related Resources
- PRD: `docs/project_plans/listings-facelift-enhancement/prd-listings-facelift-v2.md`
- Tooltip Investigation: `docs/project_plans/listings-facelift-enhancement/tooltip-investigation-report.md`
- Original Requirements: `docs/project_plans/listings-facelift-enhancement/listings-facelift-enhancements-v2.md`
