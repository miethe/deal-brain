# Phase 1 Context: Auto-Close Modal Implementation

## Objective
Streamline listing creation workflow by auto-closing modal after successful save with list refresh, highlight animation, focus management, and success notification.

## Architectural Decisions (ADR)

### ADR-001: URL Search Parameters for Highlight State
**Decision:** Use URL search params (`?highlight=<id>`) for highlight state management

**Rationale:**
- Survives page refreshes and browser navigation
- Shareable URLs work correctly
- Automatic cleanup on navigation away
- No additional state management library needed
- Aligns with Deal Brain's server-first Next.js patterns

**Alternatives Considered:**
- Zustand store: Adds state complexity, doesn't survive refreshes
- React state: Lost on navigation, not shareable

**Status:** Approved

---

### ADR-002: Radix UI Toast System Integration
**Decision:** Use existing `use-toast` hook with Radix UI Toast primitives

**Rationale:**
- Toast system already implemented at `/apps/web/hooks/use-toast.ts` ✅
- Follows Deal Brain's Radix UI standard ✅
- Toaster component exists at `/apps/web/components/ui/toaster.tsx` ✅
- Only needs to be mounted in layout (currently missing)

**Implementation:**
```tsx
// In success handler
toast({
  title: "Success",
  description: "Listing created successfully",
  variant: "success"
})
```

**Status:** Approved

---

### ADR-003: CSS Animation with Data Attribute
**Decision:** Use CSS `@keyframes` animation with `data-highlighted` attribute

**Rationale:**
- Performant (GPU-accelerated transforms/opacity)
- Accessible (respects `prefers-reduced-motion`)
- Cleanup via `setTimeout` after 2s duration
- Non-blocking UX

**Implementation:**
```css
@keyframes highlight-pulse {
  0%, 100% { background-color: transparent; }
  50% { background-color: hsl(var(--primary) / 0.1); }
}

[data-highlighted="true"] {
  animation: highlight-pulse 2s ease-in-out;
}
```

**Status:** Approved

---

### ADR-004: Native Browser APIs for Scroll + Focus
**Decision:** React refs with `scrollIntoView()` and `focus()` APIs

**Rationale:**
- Native browser APIs for smooth scrolling
- Keyboard accessibility via focus management
- WCAG 2.1 AA compliant (focus indicators + ARIA)
- Works with both Catalog and Data views

**Implementation:**
```tsx
const highlightRef = useRef<HTMLDivElement>(null)

useEffect(() => {
  if (highlightId && highlightRef.current) {
    highlightRef.current.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    })
    highlightRef.current.focus()
  }
}, [highlightId])
```

**Status:** Approved

---

## Current Implementation Analysis

### Existing Components

**1. AddListingModal (`apps/web/components/listings/add-listing-modal.tsx`)**
- ✅ Has `onSuccess` prop (line 12)
- ✅ Calls `onSuccess()` in `handleSuccess` (line 19-20)
- ✅ Auto-closes modal via `onOpenChange(false)` (line 22)
- ❌ Does NOT pass listing ID through callback

**2. AddListingForm (`apps/web/components/listings/add-listing-form.tsx`)**
- ✅ Has `onSuccess` callback prop (line 99)
- ✅ Mutation returns listing object with ID (line 338-341)
- ✅ Invalidates React Query: `queryClient.invalidateQueries({ queryKey: ["listings"] })` (line 339)
- ✅ Calls `onSuccess?.()` after successful creation (line 376)
- ❌ Does NOT pass listing ID to callback

**3. Listings Page (`apps/web/app/listings/page.tsx`)**
- ✅ Has `handleSuccess` that closes modal (line 37-41)
- ✅ Calls `router.refresh()` (line 40)
- ✅ Uses React Query with queryKey `["listings", "records"]` (line 25)
- ❌ Does NOT accept listing ID parameter
- ❌ Does NOT set URL highlight parameter
- ❌ Does NOT show success toast

**4. Toast System**
- ✅ `use-toast` hook exists (`apps/web/hooks/use-toast.ts`)
- ✅ Toast UI component exists (`apps/web/components/ui/toast.tsx`)
- ✅ Toaster component exists (`apps/web/components/ui/toaster.tsx`)
- ❌ Toaster NOT mounted in app layout or providers

### Missing Functionality

**Callback Chain:**
- Listing ID needs to flow: `AddListingForm` → `AddListingModal` → `ListingsPage`
- TypeScript interfaces need updating to accept `listingId: number` parameter

**URL Highlight:**
- After creation, URL should become `/listings?highlight=<id>`
- Components need to read `highlight` param via `useSearchParams()`

**Highlight Animation:**
- CSS animation needed in global styles or component
- Conditional `data-highlighted` attribute on listing cards/rows
- Auto-cleanup after 2 seconds

**Scroll + Focus:**
- React ref needed for highlighted listing
- `useEffect` to scroll and focus when highlight param present
- ARIA attributes for screen readers

**Toast Notification:**
- Toaster component needs mounting in layout
- Toast call needed in success handler

---

## File Locations

### Frontend Files to Modify
- `/apps/web/components/listings/add-listing-form.tsx` - Update onSuccess signature
- `/apps/web/components/listings/add-listing-modal.tsx` - Pass listingId through
- `/apps/web/app/listings/page.tsx` - Enhanced handleSuccess with highlight logic
- `/apps/web/components/providers.tsx` or `/apps/web/components/app-shell.tsx` - Mount Toaster
- `/apps/web/app/globals.css` - Add highlight animation CSS

### Catalog View Components (check which needs highlight)
- `/apps/web/app/listings/_components/catalog-tab.tsx` - Catalog orchestrator
- `/apps/web/app/listings/_components/grid-view.tsx` - Grid layout (likely needs highlight)
- `/apps/web/app/listings/_components/dense-list-view.tsx` - List layout (likely needs highlight)
- `/apps/web/app/listings/_components/master-detail-view.tsx` - Master-detail layout (likely needs highlight)

### Data View Components
- `/apps/web/components/listings/listings-table.tsx` - Data table (needs highlight on row)

---

## Success Criteria

### Functional Requirements
- [ ] Modal closes automatically after 201 response (verify existing works)
- [ ] New listing ID is captured and passed through callback chain
- [ ] URL includes `?highlight=<id>` param after creation
- [ ] React Query invalidates both `["listings", "records"]` and `["listings", "count"]`
- [ ] New listing appears in table/catalog within 2 seconds
- [ ] New listing has 2-second pulse highlight animation
- [ ] Page scrolls to new listing if outside viewport (smooth behavior)
- [ ] Focus moves to new listing row (accessibility)
- [ ] Success toast displays: "Listing created successfully"

### Accessibility Requirements (WCAG 2.1 AA)
- [ ] Focus indicator visible on highlighted listing
- [ ] Keyboard navigation works throughout flow
- [ ] Screen reader announces listing creation success
- [ ] Animation respects `prefers-reduced-motion` media query
- [ ] ARIA attributes present on highlighted element

### Performance Requirements
- [ ] No regressions in existing modal behavior
- [ ] Animation is GPU-accelerated (transform/opacity)
- [ ] Scroll behavior is smooth but not janky
- [ ] React Query cache invalidation is efficient

---

## Implementation Notes

### React Query Invalidation
Currently only invalidates `["listings"]` - should invalidate both:
```tsx
queryClient.invalidateQueries({ queryKey: ["listings", "records"] })
queryClient.invalidateQueries({ queryKey: ["listings", "count"] })
```

### Toaster Mounting Location
Recommend mounting in `Providers` component to ensure global availability:
```tsx
// apps/web/components/providers.tsx
import { Toaster } from "./ui/toaster"

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster />
      </QueryClientProvider>
    </ThemeProvider>
  )
}
```

### Catalog View Highlight
The catalog tab has three view modes (grid, list, master-detail). Each view component will need:
- `highlightId` prop passed down
- Conditional `data-highlighted` attribute on cards/items
- Ref for scroll-to-view
- Focus management

### Animation Accessibility
Ensure animation respects user preferences:
```css
@media (prefers-reduced-motion: reduce) {
  [data-highlighted="true"] {
    animation: none;
    background-color: hsl(var(--primary) / 0.1);
  }
}
```

---

## Testing Strategy

### Manual Testing Checklist
1. Create new listing via modal
2. Verify modal closes automatically
3. Verify URL changes to include `?highlight=<id>`
4. Verify new listing appears in list
5. Verify highlight animation plays for 2 seconds
6. Verify page scrolls to new listing
7. Verify focus moves to new listing
8. Verify toast appears with success message
9. Test keyboard navigation after creation
10. Test with screen reader (NVDA/JAWS/VoiceOver)
11. Test with reduced motion preference enabled
12. Switch between catalog views (grid/list/master-detail)
13. Switch to data tab - verify highlight works there too

### Regression Testing
- [ ] Existing modal functionality unchanged
- [ ] Form validation still works
- [ ] CPU/RAM/Storage selectors still work
- [ ] Expanded modal mode still works
- [ ] Catalog filters still work
- [ ] Data table sorting/filtering still works

---

## Time Estimate
**Total: 3 days** (as per original plan)

**Breakdown:**
- Day 1: Callback chain + URL params + toast mounting (TASK-101, TASK-102, TASK-105)
- Day 2: Highlight animation + scroll/focus in catalog views (TASK-103 - catalog)
- Day 3: Highlight in data table + accessibility testing (TASK-103 - data, TASK-104)

---

# Phase 2 Context: Smart Rule Display Implementation

## Objective
Filter valuation tab to show only top 4 contributing rules with clear hierarchy sorted by impact.

## Architectural Decisions (ADR)

### ADR-005: Client-Side Rule Sorting with useMemo
**Decision:** Implement sorting logic in React component with memoization

**Rationale:**
- Sorting is presentation logic, belongs in UI layer
- useMemo prevents unnecessary recalculations on re-renders
- Dependency on adjustments array ensures proper updates
- No need for backend changes - API already provides all data

**Implementation:**
```tsx
const sortedAdjustments = useMemo(() => {
  return adjustments
    .filter((adj) => Math.abs(adj.adjustment_amount) > 0)
    .sort((a, b) => {
      const diff = Math.abs(b.adjustment_amount) - Math.abs(a.adjustment_amount);
      if (diff !== 0) return diff;
      return a.rule_name.localeCompare(b.rule_name);
    });
}, [adjustments]);
```

**Status:** Approved ✅

---

### ADR-006: Filter Zero-Value Adjustments
**Decision:** Filter out adjustments with zero values before sorting

**Rationale:**
- Zero-value adjustments don't contribute to price changes
- Reduces visual clutter
- Ensures "No active rules" state only shows when truly no contributors
- Improves user understanding of what affected the price

**Status:** Approved ✅

---

## Current Implementation Analysis

### Phase 2 Discovery
When analyzing the codebase for Phase 2 implementation, found that **most requirements were already met** from Phase 1 work:

**Already Implemented in Phase 1:**
- ✅ Display max 4 rules (line 333: `adjustments.slice(0, 4)`)
- ✅ Color-coding (lines 345-351: emerald for savings, red for premiums)
- ✅ Rule card layout with name, action count, adjustment amount
- ✅ "View breakdown" button with rule count
- ✅ Empty state for zero contributors (lines 363-367)
- ✅ Hidden rules indicator (lines 357-361)

**Missing from Phase 1:**
- ❌ Sorting by absolute adjustment amount (API order was used)

### Implementation Required

**File Modified:**
- `/apps/web/components/listings/listing-valuation-tab.tsx`

**Changes Made:**
1. Added `sortedAdjustments` memoized variable (lines 166-177)
2. Updated all references to use sorted list instead of raw adjustments
3. Ensured zero-value filtering happens before sorting

---

## Success Criteria

### Functional Requirements
- [x] Max 4 rules displayed in valuation tab
- [x] Rules sorted by absolute adjustment amount (descending)
- [x] Alphabetical tiebreaker for equal amounts
- [x] Zero-value adjustments filtered out
- [x] Color-coding: green (savings), red (premiums)
- [x] "View breakdown" button shows total rule count
- [x] Empty state for zero contributing rules
- [x] Hidden rules indicator when >4 contributors

### Performance Requirements
- [x] Sorting logic memoized with useMemo
- [x] Only recalculates when adjustments array changes
- [x] No unnecessary re-renders

---

## Implementation Notes

### Memoization Pattern
The sorting logic uses proper memoization:
```tsx
const sortedAdjustments = useMemo(() => {
  // ... sorting logic
}, [adjustments]);
```

Dependency array contains only `adjustments`, ensuring:
- Recalculation happens when data changes
- Stable reference when adjustments unchanged
- Performance optimization for large adjustment lists

### Sorting Algorithm
Two-level sort:
1. **Primary:** Absolute adjustment amount (descending)
2. **Secondary:** Rule name (alphabetical ascending)

This ensures:
- Most impactful rules appear first
- Deterministic ordering for equal amounts
- User-friendly presentation

---

## Time Estimate vs Actual

**Planned:** 2 days
**Actual:** <1 day (most work already complete from Phase 1)

**Efficiency Gain:** Phase 1 implementation was comprehensive and included most Phase 2 requirements proactively.
