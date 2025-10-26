# Listings Facelift Enhancement V2 - Working Context

**Project:** Deal Brain - Listings Display Enhancement
**Version:** 2.0
**Last Updated:** 2025-10-26

---

## Project Overview

This document provides working context for implementing Listings Facelift Enhancements V2, focusing on Phases 1-2 (Foundation and Structure).

**Primary Goals:**
- Enhance information density in overview modal and detail page
- Improve visual hierarchy and organization
- Add contextual tooltips for entity links
- Surface valuation rules transparently
- Reorganize specifications tab into logical subsections
- Optimize detail page layout for better space utilization

---

## Architecture Context

### Frontend Stack

- **Framework:** Next.js 14 (App Router)
- **UI Library:** React 18
- **Components:** shadcn/ui (built on Radix UI primitives)
- **Styling:** Tailwind CSS with CSS variables
- **State Management:**
  - Server state: React Query (@tanstack/react-query)
  - Client state: Zustand (as needed)
- **Forms:** React Hook Form + Zod validation
- **Icons:** lucide-react
- **Type Safety:** TypeScript (strict mode)

### Key Architecture Patterns

1. **Entity Tooltip Pattern:**
   - Use `EntityTooltip` component for all entity link hover interactions
   - Pattern: Popover-based with 200ms delay
   - API fetching via `fetchEntityData` from `lib/api/entities.ts`
   - Avoid old `/listings/entities/...` endpoints (now deprecated)

2. **API Integration:**
   - Use `apiFetch()` utility from `lib/utils.ts`
   - React Query for caching and invalidation
   - Proper error handling with toast notifications

3. **Accessibility:**
   - WCAG 2.1 AA compliance mandatory
   - Keyboard navigation support
   - Screen reader compatibility
   - Minimum touch target: 44x44px

4. **Responsive Design:**
   - Mobile-first approach
   - Grid layouts with responsive breakpoints
   - Minimum body text: 14px

---

## Key Files Reference

### Phase 1 (Foundation) Files

| File | Purpose | Key Areas |
|------|---------|-----------|
| `apps/web/components/listings/listing-overview-modal.tsx` | Overview modal component | Lines 150-169 (GPU display), 263-299 (URL links) |
| `apps/web/components/listings/detail-page-hero.tsx` | Detail page overview/hero section | Entity links for CPU, GPU, RAM, Storage |
| `apps/web/components/listings/listing-valuation-tab.tsx` | Valuation tab component | Replace "No rule-based adjustments" with rules list |
| `apps/web/components/listings/entity-tooltip.tsx` | Tooltip component | Refactored Popover pattern |
| `apps/web/components/listings/tooltips/cpu-tooltip-content.tsx` | CPU tooltip content | Reusable content component |
| `apps/web/components/listings/tooltips/gpu-tooltip-content.tsx` | GPU tooltip content | Reusable content component |
| `apps/web/components/listings/tooltips/ram-spec-tooltip-content.tsx` | RAM tooltip content | Reusable content component |
| `apps/web/components/listings/tooltips/storage-profile-tooltip-content.tsx` | Storage tooltip content | Reusable content component |
| `apps/web/lib/api/entities.ts` | Entity API utilities | `fetchEntityData` function |

### Phase 2 (Structure) Files

| File | Purpose | Key Areas |
|------|---------|-----------|
| `apps/web/components/listings/specifications-tab.tsx` | Specifications tab | Needs subsection reorganization |
| `apps/web/components/listings/detail-page-layout.tsx` | Detail page layout wrapper | Layout and spacing optimization |
| `apps/web/components/listings/quick-add-compute-dialog.tsx` | Quick-add dialog (NEW) | Compute data entry form |
| `apps/web/components/listings/quick-add-memory-dialog.tsx` | Quick-add dialog (NEW) | Memory data entry form |
| `apps/web/components/listings/quick-add-storage-dialog.tsx` | Quick-add dialog (NEW) | Storage data entry form |
| `apps/web/components/listings/quick-add-connectivity-dialog.tsx` | Quick-add dialog (NEW) | Connectivity data entry form |

### Shared UI Components

| Component | Location | Usage |
|-----------|----------|-------|
| `Card`, `CardHeader`, `CardTitle`, `CardContent` | `apps/web/components/ui/card.tsx` | Section containers |
| `Dialog`, `DialogContent`, `DialogHeader` | `apps/web/components/ui/dialog.tsx` | Modal dialogs |
| `Button` | `apps/web/components/ui/button.tsx` | Interactive elements |
| `Badge` | `apps/web/components/ui/badge.tsx` | Status indicators (e.g., "Integrated" GPU badge) |
| `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell`, `TableHead` | `apps/web/components/ui/table.tsx` | Tabular data display |
| `Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent` | `apps/web/components/ui/accordion.tsx` | Expandable sections |
| `Separator` | `apps/web/components/ui/separator.tsx` | Visual dividers |

---

## API Endpoints Reference

### Listings Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/v1/listings/{id}` | GET | Get listing details | Full listing object |
| `/v1/listings/{id}` | PATCH | Update listing fields | Updated listing object |
| `/v1/listings/{id}/valuation-breakdown` | GET | Get valuation rules and adjustments | Breakdown with adjustments array |

### Entity Endpoints

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/v1/cpus/{id}` | GET | Get CPU details | CPU object |
| `/v1/gpus/{id}` | GET | Get GPU details | GPU object |
| `/v1/ram-specs/{id}` | GET | Get RAM spec details | RAM spec object |
| `/v1/storage-profiles/{id}` | GET | Get storage profile details | Storage profile object |

**Note:** Use `/v1/cpus/{id}` pattern, NOT the old `/listings/entities/cpu/{id}` pattern.

---

## Design Patterns to Follow

### 1. EntityTooltip Implementation Pattern

```tsx
import { EntityTooltip } from "./entity-tooltip";
import { fetchEntityData } from "@/lib/api/entities";
import { CpuTooltipContent } from "./tooltips/cpu-tooltip-content";

// Wrap entity link with EntityTooltip
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
```

### 2. React Query Usage Pattern

```tsx
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/utils";

const { data: breakdown } = useQuery({
  queryKey: ['valuation-breakdown', listingId],
  queryFn: () => apiFetch(`/v1/listings/${listingId}/valuation-breakdown`),
});
```

### 3. Form Mutation Pattern

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";

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
    toast({ title: 'Success', description: 'Data updated' });
  },
  onError: () => {
    toast({ title: 'Error', description: 'Failed to update', variant: 'destructive' });
  },
});
```

### 4. Subsection Component Pattern

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
```

---

## Testing Requirements

### Component Testing

- [ ] All new components have unit tests
- [ ] Accessibility tested with keyboard navigation
- [ ] Screen reader compatibility verified
- [ ] Mobile responsiveness validated

### Integration Testing

- [ ] API endpoints return expected data
- [ ] Form submissions work correctly
- [ ] React Query cache invalidation works
- [ ] Toast notifications appear as expected

### Performance Testing

- [ ] No significant performance degradation
- [ ] Image loading doesn't block rendering
- [ ] Tooltips appear within 200ms
- [ ] Page load time remains acceptable

---

## Common Pitfalls to Avoid

### 1. ❌ Using Old Entity Endpoint Pattern

**Wrong:**
```tsx
apiFetch(`/listings/entities/cpu/${id}`)
```

**Correct:**
```tsx
apiFetch(`/v1/cpus/${id}`)
```

### 2. ❌ Forgetting React Query Cache Invalidation

After mutations, always invalidate relevant queries:

```tsx
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ['listing', listingId] });
}
```

### 3. ❌ Not Handling Empty States

Always provide empty state UI with clear messaging:

```tsx
{isEmpty ? (
  <p className="text-sm text-muted-foreground">No data available</p>
) : (
  <DataDisplay />
)}
```

### 4. ❌ Hardcoding API URLs

Always use `apiFetch()` utility which handles base URL and headers:

```tsx
// Wrong
fetch('http://localhost:8000/v1/listings/1')

// Correct
apiFetch('/v1/listings/1')
```

### 5. ❌ Missing TypeScript Types

Always define interfaces for API responses and component props:

```tsx
interface ValuationAdjustment {
  rule_id: number | null;
  rule_name: string;
  rule_description: string | null;
  rule_group_name: string | null;
  adjustment_amount: number;
}
```

---

## Commit Convention

Use conventional commits format:

```
feat(web): implement [feature] for listings facelift

- Added [component/feature]
- Updated [files]
- Tests passing

Refs: Phase 1-2, Task [ID]
```

Examples:
- `feat(web): add GPU badge to overview modal`
- `feat(web): display valuation rules in valuation tab`
- `refactor(web): reorganize specifications tab into subsections`

---

## Related Documentation

- **Implementation Plan:** [implementation-plan-v2.md](../implementation-plan-v2.md)
- **PRD:** [prd-listings-facelift-v2.md](../prd-listings-facelift-v2.md)
- **Progress Tracker:** [phase-1-2-progress.md](../progress/phase-1-2-progress.md)
- **Tooltip Investigation:** [tooltip-investigation-report.md](../../investigations/tooltip-investigation-report.md)
- **Original Requirements:** [listings-facelift-enhancements-v2.md](../listings-facelift-enhancements-v2.md)

---

## Quick Reference Commands

### Development
```bash
make web                 # Run Next.js dev server
make api                 # Run FastAPI dev server
make up                  # Start full Docker stack
```

### Testing
```bash
make test                # Run pytest suite
pnpm test                # Run frontend tests (if configured)
```

### Code Quality
```bash
make lint                # Lint Python and TypeScript
make format              # Format code
```
