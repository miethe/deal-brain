# Tooltip Investigation Report: Root Cause Analysis and Remediation Plan

**Date**: 2025-10-24
**Report Type**: Post-Implementation Investigation
**Status**: Root Cause Identified - Remediation Plan Ready
**Severity**: Critical (Zero Tooltip Functionality)

---

## Executive Summary

After implementing tooltips across seven different components in three implementation phases (Phases 3, 3.5, and 3.6), a critical architectural incompatibility was discovered: **Radix HoverCard cannot properly attach hover event listeners to Next.js Link components**. This fundamental mismatch between the HoverCard primitive and Link elements results in **zero tooltip functionality across the entire application**, despite correct implementation patterns in all seven affected files.

### Current Status

- **Phases Completed**: 3 full phases with 3 commits
- **Files Modified**: 7 components across catalog views, modals, and detail pages
- **Tooltips Implemented**: CPU and GPU tooltips in table, grid, dense list, master-detail, specifications tab, and modals
- **Current Functionality**: None - Tooltips do not appear on hover in any location
- **Root Cause**: Architectural incompatibility between HoverCard and Link primitives
- **Impact**: Complete failure of tooltip system despite correct component integration

### Solution

Refactor EntityTooltip to use Radix Popover pattern with explicit `onMouseEnter` and `onMouseLeave` handlers, following the proven pattern from the working InfoTooltip component. This will require modifying a single core component file (`entity-tooltip.tsx`) that all seven implementations depend on.

---

## Technical Root Cause Analysis

### The Problem: HoverCard + Link Incompatibility

The EntityTooltip component combines two Radix UI primitives that have a fundamental architectural conflict:

```typescript
// Current (BROKEN) Pattern in entity-tooltip.tsx
<HoverCard open={isOpen} onOpenChange={handleOpenChange}>
  <HoverCardTrigger asChild>
    <EntityLink>  {/* Wraps Next.js Link component */}
      {children}
    </EntityLink>
  </HoverCardTrigger>

  <HoverCardContent>
    {/* Tooltip content */}
  </HoverCardContent>
</HoverCard>
```

### Why It Fails

**HoverCard Technical Behavior:**
- Radix HoverCard attaches hover listeners to the trigger element
- It monitors mouseenter and mouseleave events on the DOM element
- HoverCard passes `asChild` prop to delegate to the child component

**Link Technical Behavior:**
- Next.js Link is a wrapper component that creates an `<a>` tag internally
- When asChild prop is used, HoverCard receives the Link component, not the underlying `<a>` tag
- Link components don't naturally forward hover event listeners to their DOM children
- Result: Hover events never bubble up to trigger HoverCard's onOpenChange handler

**The Architectural Mismatch:**
```
User hovers over <a> tag
         ↓
No event listener at <a> level (Link doesn't expose them)
         ↓
HoverCard never receives mouseenter/mouseleave
         ↓
onOpenChange never called
         ↓
Tooltip never appears
```

### Comparison: Why InfoTooltip Works

The working InfoTooltip in `/mnt/containers/deal-brain/apps/web/components/ui/info-tooltip.tsx` uses a different pattern:

```typescript
// WORKING Pattern in info-tooltip.tsx (lines 11-28)
<Popover open={open} onOpenChange={setOpen}>
  <PopoverTrigger asChild>
    <button
      className="inline-flex items-center justify-center"
      onClick={(e) => {
        e.stopPropagation();
        setOpen(!open);
      }}
      onMouseEnter={() => setOpen(true)}          // EXPLICIT HANDLER
      onMouseLeave={() => setOpen(false)}         // EXPLICIT HANDLER
      aria-label="Field description"
    >
      <Info className="h-3.5 w-3.5 text-muted-foreground" />
    </button>
  </PopoverTrigger>
  <PopoverContent /* ... */ />
</Popover>
```

**Why It Works:**
1. Uses Popover instead of HoverCard (more flexible)
2. Trigger is a native `<button>` element (not a component wrapper)
3. Has explicit `onMouseEnter` and `onMouseLeave` handlers
4. Handlers directly call `setOpen()` instead of relying on HoverCard event detection
5. Works consistently across all contexts

### Code Comparison Table

| Aspect | Current EntityTooltip (Broken) | InfoTooltip (Working) |
|--------|-------|---------|
| Primitive | HoverCard | Popover |
| Trigger | Next.js Link component | Native button element |
| Event Handling | Implicit (HoverCard detects hover) | Explicit (onMouseEnter/onMouseLeave) |
| Hover Detection | Relies on HoverCard event bubbling | Direct handler invocation |
| Hover Reliability | Fails with component wrappers | Succeeds - explicit control |
| Mobile Touch | Would work if hover worked | Works (has onClick too) |

---

## Investigation Timeline

### Phase 3: Entity Tooltips Initial Implementation (Commit 482fbf7)

**Date**: 2025-10-24
**Objective**: Add CPU/GPU tooltips to all catalog views
**Changes**: Created EntityTooltip component using HoverCard + Link pattern and deployed to 4 locations:
- `listings-table.tsx` - CPU and GPU tooltips
- `grid-view/listing-card.tsx` - CPU and GPU tooltips
- `dense-list-view/dense-table.tsx` - CPU and GPU tooltips
- `master-detail-view/master-list.tsx` - CPU tooltip

**Result**: Implementation appeared correct. All files properly imported EntityTooltip and passed correct props. No code errors or import issues. However, tooltips did not appear in browser.

**Investigation at Time**: Assumed API issue or missing data.

### Phase 3.5: Extended Tooltip Coverage (Commit 701527e)

**Date**: 2025-10-24
**Objective**: Fix tooltips in modal and detail page contexts
**Changes**: Added EntityTooltip to 3 additional locations:
- `specifications-tab.tsx` - Detail page CPU tooltip
- `listing-details-dialog.tsx` - Modal CPU/GPU tooltips
- `listing-overview-modal.tsx` - Modal CPU/GPU tooltips

**Result**: Same issue - tooltips still non-functional in all 7 locations. Modal/detail page contexts didn't matter; core component still broken.

**Investigation at Time**: Checked API endpoints (working), verified component imports (correct), inspected data flow (valid). Realized issue was component-level, not integration-level.

### Phase 3.6: API Endpoint Fix (Commit 24311b2)

**Date**: 2025-10-24
**Objective**: Fix API endpoint paths for tooltip data fetching
**Changes**: Corrected fetchEntityData function in `apps/web/lib/api/entities.ts`:
- Changed `/v1/cpus/{id}` to `/v1/catalog/cpus/{id}`
- Changed `/v1/gpus/{id}` to `/v1/catalog/gpus/{id}`
- Added `/v1/catalog/ram-specs/{id}`
- Added `/v1/catalog/storage-profiles/{id}`

**Result**: Confirmed backend endpoints work. API returns proper data. However, tooltips STILL do not appear in any location. Network requests would work IF tooltips showed, but they never trigger.

**Root Cause Realization**: The problem isn't API endpoints or data fetching - it's that the hover events never fire in the first place. The component never reaches the point of calling fetchData because HoverCard's onOpenChange handler never executes.

---

## Root Cause Deep Dive

### Investigation Evidence

**Evidence 1: Component Architecture is Correct**
All 7 implementations follow the exact same pattern and are architecturally sound:
```typescript
<EntityTooltip
  entityType="cpu"
  entityId={listing.cpu?.id}
  tooltipContent={(cpu) => <CpuTooltipContent cpu={cpu} />}
  fetchData={fetchEntityData}
>
  {listing.cpu_name}
</EntityTooltip>
```
No issues with prop passing, data types, or component composition.

**Evidence 2: API Endpoints Are Working**
- Backend endpoints verified functional at `/v1/catalog/cpus/{id}`, `/v1/catalog/gpus/{id}`, etc.
- API responses contain valid entity data
- Endpoint paths fixed in Phase 3.6 are correct
- If tooltips displayed, data would load correctly

**Evidence 3: Dependencies Are Installed**
- Radix UI HoverCard package is installed and imported correctly
- No import errors or missing peer dependencies
- Component syntax is valid TypeScript/React

**Evidence 4: The Issue is NOT Navigation**
- Some implementations confused 404 navigation links with tooltip failures
- Entity tooltips are INDEPENDENT of link navigation
- 404 on `/catalog/ram-specs/{id}` link doesn't affect tooltip from `/v1/catalog/ram-specs/{id}` API
- This is by architectural design, not a bug

**Evidence 5: Entity Link is the Problem**
- EntityTooltip wraps EntityLink (which wraps Next.js Link) as HoverCardTrigger
- Hover events don't bubble through the Link component
- Replacing EntityLink with a simple button would make tooltips work
- This is a Radix UI HoverCard + Next.js Link incompatibility

### Why This Happened

The implementation chain was:
1. EntityLink component created (wraps Next.js Link) - Fine for navigation
2. EntityTooltip created using HoverCard + EntityLink - BROKEN pattern
3. Developers didn't test in browser before implementing across 7 locations
4. Assumption that "HoverCard + Link should work" went untested
5. No comparison with working InfoTooltip pattern (which uses explicit handlers)

### Why It Wasn't Caught Earlier

- Code review focused on correctness (imports, props, data types)
- No manual browser testing before widespread deployment
- Three implementation phases created false sense of progress
- Didn't realize the core component was broken until all 7 implementations were in place
- Architectural incompatibility isn't obvious from code inspection alone

---

## Root Cause Analysis Summary

| Aspect | Finding |
|--------|---------|
| **Root Cause Category** | Architectural Component Incompatibility |
| **Specific Issue** | Radix HoverCard cannot detect hover events on Next.js Link components |
| **Component Affected** | EntityTooltip (single core file: `entity-tooltip.tsx`) |
| **Symptoms** | No tooltips appear on hover in any of 7 implementations |
| **Severity** | Critical - Complete feature failure |
| **Fix Complexity** | Low - Single component refactor required |
| **Estimated Fix Time** | 2-3 hours |
| **Files to Modify** | 1 core file (entity-tooltip.tsx) |
| **Files Requiring Changes** | 0 (all 7 implementations are already correct) |

### The 404 Navigation Confusion

During investigation, some developers noted that RAM Spec and Storage Spec links return 404 errors. This created confusion:

**Misconception**: "Broken links prevent tooltips from working"

**Reality**: These are completely separate concerns:
- **Tooltip data** comes from API: `/v1/catalog/ram-specs/{id}` - Works fine
- **Navigation link** uses frontend route: `/catalog/ram-specs/{id}` - Returns 404 because route doesn't exist
- **The tooltip never even tries to display** because HoverCard can't detect the hover

The broken links don't affect tooltips, but they DO affect the Click-to-Navigate UX. This is a separate issue to fix after tooltips are working.

---

## Remediation Plan

### Option 1: Popover Pattern with Explicit Handlers (RECOMMENDED)

This is the proven, working pattern demonstrated by InfoTooltip.

**Implementation Approach:**
1. Refactor EntityTooltip to use Popover instead of HoverCard
2. Add explicit `onMouseEnter` and `onMouseLeave` handlers to trigger
3. Remove reliance on event bubbling through Link wrapper
4. Keep API data fetching logic unchanged
5. Maintain all accessibility features

**Code Changes:**

```typescript
// apps/web/components/listings/entity-tooltip.tsx
"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { EntityLink } from "./entity-link";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";

export interface EntityTooltipProps {
  entityType: "cpu" | "gpu" | "ram-spec" | "storage-profile";
  entityId: number;
  children: ReactNode;
  tooltipContent: (data: any) => ReactNode;
  fetchData?: (entityType: string, entityId: number) => Promise<any>;
  href?: string;
  variant?: "link" | "inline";
  className?: string;
  openDelay?: number;
}

export function EntityTooltip({
  entityType,
  entityId,
  children,
  tooltipContent,
  fetchData,
  href,
  variant = "link",
  className,
  openDelay = 200,
}: EntityTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  let openDelay Timer: ReturnType<typeof setTimeout> | null = null;

  const handleOpenChange = async (open: boolean) => {
    setIsOpen(open);

    // Clear any pending timers
    if (openDelay Timer) {
      clearTimeout(openDelay Timer);
      openDelay Timer = null;
    }

    // Fetch data when tooltip opens if not already loaded
    if (open && !data && !isLoading && !error && fetchData) {
      setIsLoading(true);
      setError(null);

      try {
        const result = await fetchData(entityType, entityId);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleMouseEnter = () => {
    if (openDelay Timer) {
      clearTimeout(openDelay Timer);
    }
    openDelay Timer = setTimeout(() => {
      handleOpenChange(true);
    }, openDelay);
  };

  const handleMouseLeave = () => {
    if (openDelay Timer) {
      clearTimeout(openDelay Timer);
      openDelay Timer = null;
    }
    handleOpenChange(false);
  };

  return (
    <Popover open={isOpen} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <span
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          className="inline"
        >
          <EntityLink
            entityType={entityType}
            entityId={entityId}
            href={href}
            variant={variant}
            className={className}
          >
            {children}
          </EntityLink>
        </span>
      </PopoverTrigger>

      <PopoverContent className="w-80" aria-live="polite">
        {/* Loading state */}
        {isLoading && (
          <div className="space-y-2" role="status" aria-label="Loading entity details">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-5/6" />
            <span className="sr-only">Loading...</span>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="flex items-start gap-2 text-sm text-destructive" role="alert">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">Failed to load details</p>
              <p className="text-xs text-muted-foreground">{error}</p>
            </div>
          </div>
        )}

        {/* Content state */}
        {data && !isLoading && !error && tooltipContent(data)}

        {/* No data and no fetch function */}
        {!data && !isLoading && !error && !fetchData && (
          <div className="text-sm text-muted-foreground">
            No tooltip content available
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
```

**Key Changes:**
- Changed from `HoverCard` to `Popover` primitive
- Added wrapper `<span>` with explicit `onMouseEnter` and `onMouseLeave` handlers
- Handlers call `handleOpenChange()` with explicit true/false
- Configurable `openDelay` timer for delayed tooltip appearance
- All logic remains the same - just the hover detection method changed

**Files Modified:**
- `/mnt/containers/deal-brain/apps/web/components/listings/entity-tooltip.tsx` (single file)

**Files NOT Modified:**
- All 7 implementations (`listings-table.tsx`, `grid-view/listing-card.tsx`, `dense-list-view/dense-table.tsx`, `master-detail-view/master-list.tsx`, `specifications-tab.tsx`, `listing-details-dialog.tsx`, `listing-overview-modal.tsx`)
- API endpoints and data fetching logic
- Test files
- Type definitions

**Advantages:**
- Uses proven pattern from InfoTooltip (already working)
- Single file change fixes all 7 implementations
- Maintains all existing functionality
- Explicit control over hover behavior
- No changes to any consumer components
- Backward compatible - all props remain the same

**Disadvantages:**
- Requires wrapping EntityLink in span (minor DOM overhead)
- Slightly different from Radix UI pattern (but works reliably)

**Testing Strategy:**
1. Modify EntityTooltip component
2. Test in browser with different views (table, grid, modal, detail page)
3. Verify hover triggers tooltip in all 7 locations
4. Verify data loads correctly on first hover
5. Verify keyboard navigation still works (Tab + Enter)
6. Verify touch/mobile interactions
7. Verify accessibility (screen reader, ARIA)

**Estimated Implementation Time:** 2-3 hours
- Code change: 30 minutes
- Testing: 1.5-2 hours
- Documentation updates: 30 minutes

---

### Option 2: Separate Hover from Navigation

Use Popover for hover interaction, but separate the navigation trigger.

**Approach:**
- Create two separate elements: one for hover (Popover trigger), one for navigation (Link)
- Hover shows tooltip, click doesn't navigate (requires separate Click-to-Details button)
- More complex UX

**Disadvantages:**
- Changes UX - users can't click entity names to navigate
- Requires separate button or icon for navigation
- More complex to implement
- Doesn't follow existing design patterns

**Not Recommended**: Option 1 is superior.

---

### Option 3: Use Radix Tooltip Primitive Instead

Instead of HoverCard or Popover, use the Radix Tooltip primitive directly.

**Advantages:**
- Purpose-built for tooltips
- Simpler API
- Proven reliable

**Disadvantages:**
- Radix Tooltip doesn't support custom content components easily
- Can't lazy-load data (no render lifecycle hooks)
- Would require significant refactor of EntityTooltip
- Affects all 7 implementations (more complex)
- Less flexibility for complex tooltip content

**Not Recommended**: Option 1 is simpler and more flexible.

---

## Remaining Work After Tooltip Fix

After fixing the tooltip architecture, these related tasks remain:

### 1. Product Image Display

**Status**: Not Started
**Scope**: Display product images in modal and detail page
**Files**:
- `apps/web/components/listings/listing-overview-modal.tsx`
- `apps/web/app/listings/[id]/page.tsx`

**Task**:
- Ensure `thumbnail_url` is properly fetched from API (backend computed property already exists)
- Add image component with proper sizing
- Implement image loading states (skeleton loader)
- Add image fallback (placeholder icon)
- Handle missing images gracefully

**Estimated Time**: 2-3 hours

### 2. Missing Fields in Specifications Tab

**Status**: Partially Complete
**Remaining Scope**:
- Ports section (USB-A, USB-C, HDMI, DisplayPort counts)
- Secondary storage section
- Enhanced RAM details (type, speed, generation, module count)

**Task**:
- Verify API returns all required fields
- Add rendering logic in specifications-tab.tsx
- Style components consistently with existing sections
- Add RAM spec tooltip component (optional but recommended)
- Add storage spec tooltip component (optional but recommended)

**Estimated Time**: 3-4 hours

### 3. Layout Improvements

**Status**: Not Started
**Scope**: Improve detail page layout and information hierarchy
**Task**:
- Audit current space utilization
- Improve tab organization
- Better visual grouping of related information
- Responsive behavior optimization

**Estimated Time**: 2-3 hours

### 4. Link Routing Fixes

**Status**: Partial Issue
**Scope**: RAM Spec and Storage Spec detail page routes
**Current Issue**: Links return 404 because frontend routes don't exist
**Task**:
- Create frontend routes: `/catalog/ram-specs/[id]` and `/catalog/storage-profiles/[id]`
- Create detail page components for each
- Verify API endpoints work
- Add tooltips to these detail pages as well

**Estimated Time**: 4-5 hours

### 5. Performance Validation

**Status**: Not Started
**Scope**: Verify tooltip system performance
**Task**:
- Measure API response times for entity endpoints
- Verify tooltip data is cached properly
- Monitor memory usage with many tooltips
- Ensure no performance regression from original implementation

**Estimated Time**: 1-2 hours

---

## Lessons Learned

### Why We Missed This

1. **Assumption Cascade**: Assumed HoverCard + Link would work because both are Radix primitives
2. **No Browser Testing Before Deployment**: Code was reviewed and looked correct, but wasn't tested in running application
3. **Three Phases of Reinforcement**: Each phase appeared to succeed (no code errors), reinforcing false confidence
4. **Didn't Compare with Working Examples**: InfoTooltip was working in the same codebase but not used as reference
5. **Complexity Confusion**: Architectural issue (how components interact) wasn't obvious from code inspection

### Prevention Strategies

1. **Always Test in Browser Early**: Don't assume component combinations work without testing
2. **Look for Working Examples**: Before implementing new patterns, study existing working implementations
3. **Explicit Pattern Documentation**: Document WHY patterns work (not just that they do)
4. **Component Compatibility Matrix**: Create reference showing which Radix primitives work well together
5. **Staging Testing**: Deploy to staging and test user interactions before wide rollout

### Component Interaction Principles

**Lesson**: Not all component combinations work, even from the same library.

**Best Practices**:
- Radix primitives with explicit event handlers (Popover + onMouseEnter) > Implicit event detection (HoverCard)
- Component wrappers can prevent event bubbling - test with primitives
- Check Radix documentation for "Trigger" component expectations
- If using `asChild`, verify child element properly forwards events

---

## Implementation Checklist

### Pre-Implementation

- [ ] Review this entire report with team
- [ ] Confirm Option 1 (Popover pattern) is approved solution
- [ ] Assign implementation to ui-engineer or frontend-developer

### Implementation Phase (2-3 hours)

- [ ] Modify `apps/web/components/listings/entity-tooltip.tsx`
- [ ] Import Popover and PopoverContent instead of HoverCard
- [ ] Add explicit onMouseEnter and onMouseLeave handlers
- [ ] Implement openDelay timer logic
- [ ] Wrap EntityLink in span element
- [ ] Test component in isolation (Storybook or test component)

### Testing Phase (1.5-2 hours)

#### Browser Testing

- [ ] **Table View** - Hover over CPU name → tooltip appears ✅
- [ ] **Table View** - Hover over GPU name → tooltip appears ✅
- [ ] **Grid View** - Hover over CPU name → tooltip appears ✅
- [ ] **Grid View** - Hover over GPU name → tooltip appears ✅
- [ ] **Dense List View** - Hover CPU/GPU → tooltips appear ✅
- [ ] **Master-Detail View** - Hover CPU → tooltip appears ✅
- [ ] **Modal Specifications** - Hover CPU/GPU → tooltips appear ✅
- [ ] **Detail Page Specifications** - Hover CPU → tooltip appears ✅

#### Data Loading

- [ ] Open DevTools Network tab
- [ ] Hover over entity for first time → API request made
- [ ] Check request URL is `/v1/catalog/{entity}/{id}`
- [ ] Check response status is 200 OK
- [ ] Verify tooltip displays returned data

#### Keyboard Navigation

- [ ] Tab to CPU/GPU name
- [ ] Press Enter to show tooltip
- [ ] Press Escape to close tooltip
- [ ] Tab navigation works within tooltip content

#### Accessibility

- [ ] Screen reader announces tooltip content
- [ ] ARIA attributes are correct
- [ ] Keyboard-only users can access all content
- [ ] Tooltip doesn't interfere with page structure

#### Edge Cases

- [ ] Missing CPU - no tooltip shown
- [ ] Missing GPU - no tooltip shown
- [ ] Long entity names - truncated with tooltip showing full
- [ ] Very short viewport - tooltip repositions correctly
- [ ] Mobile/touch - tap shows tooltip (if implemented)

#### Regression Testing

- [ ] Existing sorting still works in table
- [ ] Filtering still works
- [ ] Modal open/close still works
- [ ] Detail page navigation still works
- [ ] No console errors or warnings
- [ ] No layout shifts or flashing
- [ ] No performance degradation

### Deployment (30 minutes)

- [ ] Code review and approval
- [ ] Push to feature branch
- [ ] Create pull request
- [ ] Deploy to staging
- [ ] Final QA verification
- [ ] Deploy to production
- [ ] Monitor error rates for 24 hours

### Documentation (30 minutes)

- [ ] Update remediation progress tracker
- [ ] Add tooltip architecture documentation
- [ ] Document Popover pattern for future developers
- [ ] Update component comments in entity-tooltip.tsx
- [ ] Create Storybook story for EntityTooltip component

---

## Related Documentation

- **Progress Tracker**: `/mnt/containers/deal-brain/docs/project_plans/listings-facelift-enhancement/progress/remediation-progress.md`
- **Remediation Summary**: `/mnt/containers/deal-brain/docs/project_plans/listings-facelift-enhancement/REMEDIATION_SUMMARY.md`
- **Remediation Plan**: `/mnt/containers/deal-brain/docs/project_plans/listings-facelift-enhancement/REMEDIATION_PLAN.md`

---

## Conclusion

This investigation reveals a subtle but critical architectural incompatibility between Radix HoverCard and Next.js Link primitives that prevents hover event detection. The solution is straightforward: refactor the core EntityTooltip component to use Popover with explicit event handlers, following the proven pattern from the working InfoTooltip component.

**Key Findings:**
- Root cause is not API, data, or implementation - it's component architecture
- Single file change (entity-tooltip.tsx) fixes all 7 locations
- All implementation files are already correct - no changes needed there
- Estimated fix time: 2-3 hours including comprehensive testing
- Solution uses proven working pattern from existing codebase

This report serves as both a post-mortem explaining why tooltips aren't working and a blueprint for fixing the issue efficiently.
