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

---

# Phase 3 Context: Enhanced Breakdown Modal Implementation

## Objective
Reorganize breakdown modal with contributors/inactive sections, clickable rules, RuleGroup badges, and enhanced navigation capabilities.

## Architectural Decisions (ADR)

### ADR-007: Client-Side Sorting for Contributors/Inactive
**Decision:** Implement sorting logic in React component with memoization

**Rationale:**
- Sorting is presentation logic, belongs in UI layer
- API returns all rules, UI decides how to organize them
- Allows flexible re-sorting without backend changes
- `useMemo` prevents unnecessary recalculations on re-renders
- Dependency on adjustments array ensures proper updates

**Implementation:**
```tsx
const { contributors, inactive } = useMemo(() => {
  const contrib = adjustments
    .filter(adj => Math.abs(adj.adjustment_amount) > 0)
    .sort((a, b) => {
      const diff = Math.abs(b.adjustment_amount) - Math.abs(a.adjustment_amount);
      return diff !== 0 ? diff : a.rule_name.localeCompare(b.rule_name);
    });

  const inact = adjustments
    .filter(adj => Math.abs(adj.adjustment_amount) === 0)
    .sort((a, b) => a.rule_name.localeCompare(b.rule_name));

  return { contributors: contrib, inactive: inact };
}, [adjustments]);
```

**Status:** Approved ✅

---

### ADR-008: Enrich API Response with Database Lookups
**Decision:** Enhance valuation breakdown endpoint to include rule metadata from database, not just JSON

**Rationale:**
- `listing.valuation_breakdown` JSON field stores snapshot at valuation time
- Rule metadata (description, group) may have changed since valuation
- Need both historical adjustment data AND current rule metadata
- Provides richer context for users viewing breakdown
- Enables navigation to current rule detail pages

**Implementation Approach:**
1. Parse `valuation_breakdown` JSON for adjustment data (amounts, actions)
2. For each adjustment with `rule_id`, query `ValuationRuleV2` table
3. Eager-load `ValuationRuleV2.group` relationship (avoid N+1)
4. Enrich response with `rule_description`, `rule_group_id`, `rule_group_name`
5. For inactive rules, query all rules from same ruleset, filter by missing IDs

**Backend Schema Extensions:**
```python
class ValuationAdjustmentDetail(BaseModel):
    rule_id: int | None = Field(None, description="Identifier of the valuation rule")
    rule_name: str = Field(..., description="Display name of the rule")
    rule_description: str | None = Field(None, description="Rule description for tooltips")  # NEW
    rule_group_id: int | None = Field(None, description="Rule group identifier")  # NEW
    rule_group_name: str | None = Field(None, description="Rule group name for badges")  # NEW
    adjustment_amount: float = Field(..., description="Net price adjustment in USD")
    actions: list[ValuationAdjustmentAction] = Field(default_factory=list)
```

**Database Queries:**
```python
# Get rules for enrichment
rule_ids = [adj["rule_id"] for adj in adjustments_payload if adj.get("rule_id")]
rules = await session.execute(
    select(ValuationRuleV2)
    .options(selectinload(ValuationRuleV2.group))
    .where(ValuationRuleV2.id.in_(rule_ids))
)
rules_by_id = {rule.id: rule for rule in rules.scalars()}

# Get inactive rules from same ruleset
if ruleset_id:
    all_rules = await session.execute(
        select(ValuationRuleV2)
        .options(selectinload(ValuationRuleV2.group))
        .join(ValuationRuleGroup)
        .where(ValuationRuleGroup.ruleset_id == ruleset_id)
        .where(ValuationRuleV2.is_active == True)
    )
    inactive_rules = [r for r in all_rules.scalars() if r.id not in rule_ids]
```

**Status:** Approved ✅

---

### ADR-009: Use Radix UI Primitives for Consistency
**Decision:** Use Radix UI `Collapsible` and `HoverCard` primitives for interactive features

**Rationale:**
- Radix UI is Deal Brain's standard for accessible, unstyled components
- `Collapsible` provides smooth animations and ARIA attributes
- `HoverCard` handles focus/hover states and positioning automatically
- Maintains consistency with rest of application
- Ensures WCAG 2.1 AA compliance out of the box

**Implementation:**
```tsx
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"

// Collapsible inactive section
const [inactiveOpen, setInactiveOpen] = useState(inactive.length <= 10)

<Collapsible open={inactiveOpen} onOpenChange={setInactiveOpen}>
  <CollapsibleTrigger>
    {inactiveOpen ? "Hide" : "Show"} {inactive.length} inactive rules
  </CollapsibleTrigger>
  <CollapsibleContent>
    {/* Inactive rule cards */}
  </CollapsibleContent>
</Collapsible>

// Hover tooltip with rule description
<HoverCard openDelay={200}>
  <HoverCardTrigger asChild>
    <Link href={`/valuation/rules/${adjustment.rule_id}`}>
      {adjustment.rule_name}
    </Link>
  </HoverCardTrigger>
  <HoverCardContent>
    {adjustment.rule_description || "No description available"}
  </HoverCardContent>
</HoverCard>
```

**Status:** Approved ✅

---

## Current Implementation Analysis

### Existing Backend Endpoint

**File:** `/apps/api/dealbrain_api/api/listings.py` (lines 344-440)

**Current State:**
- ✅ Endpoint exists: `GET /v1/listings/{id}/valuation-breakdown`
- ✅ Returns 404 if listing not found
- ✅ Parses `listing.valuation_breakdown` JSON field
- ✅ Constructs `ValuationAdjustmentDetail` objects with:
  - `rule_id`, `rule_name`, `adjustment_amount`, `actions`
- ✅ Returns ruleset information: `ruleset_id`, `ruleset_name`
- ✅ Handles legacy component deductions (backward compatibility)
- ❌ Does NOT enrich with database rule metadata
- ❌ Does NOT include inactive rules (zero adjustments)

**What Needs to Change:**
1. Update `ValuationAdjustmentDetail` schema with optional fields
2. Query `ValuationRuleV2` table for rule metadata
3. Eager-load `ValuationRuleV2.group` relationship
4. Query inactive rules from same ruleset
5. Enrich response with metadata from database

### Existing Frontend Modal

**File:** `/apps/web/components/listings/valuation-breakdown-modal.tsx`

**Current State:**
- ✅ Displays listing info with thumbnail
- ✅ Shows base/adjusted prices and total adjustment
- ✅ Lists all adjustments in flat structure
- ✅ Rule cards show name, adjustment amount, actions
- ✅ Color-codes adjustments (green=savings, red=premiums)
- ✅ Handles legacy component deductions
- ✅ Empty state for zero adjustments
- ❌ No separation between contributors and inactive
- ❌ No sorting by impact
- ❌ Rule names NOT clickable
- ❌ No RuleGroup badges
- ❌ No collapsible section
- ❌ No hover tooltips with descriptions

**What Needs to Change:**
1. Add sorting logic with `useMemo`
2. Split adjustments into contributors/inactive sections
3. Add section headers with counts
4. Add `Separator` between sections
5. Add RuleGroup badges to rule cards
6. Wrap rule names in `Link` component
7. Add `Collapsible` for inactive section
8. Add `HoverCard` for rule description tooltips

---

## Database Schema Reference

### ValuationRuleV2 Model
**Table:** `valuation_rule_v2`
**File:** `/apps/api/dealbrain_api/models/core.py` (lines 207-235)

**Relevant Fields:**
```python
class ValuationRuleV2(Base, TimestampMixin):
    id: Mapped[int]
    group_id: Mapped[int]  # FK to valuation_rule_group
    name: Mapped[str]
    description: Mapped[str | None]
    priority: Mapped[int]
    is_active: Mapped[bool]
    evaluation_order: Mapped[int]
    metadata_json: Mapped[dict[str, Any]]

    # Relationships
    group: Mapped[ValuationRuleGroup] = relationship(back_populates="rules")
    conditions: Mapped[list[ValuationRuleCondition]] = relationship(...)
    actions: Mapped[list[ValuationRuleAction]] = relationship(...)
```

### ValuationRuleGroup Model
**Table:** `valuation_rule_group`
**File:** `/apps/api/dealbrain_api/models/core.py` (lines 187-205)

**Relevant Fields:**
```python
class ValuationRuleGroup(Base, TimestampMixin):
    id: Mapped[int]
    ruleset_id: Mapped[int]  # FK to valuation_ruleset
    name: Mapped[str]
    category: Mapped[str]
    description: Mapped[str | None]
    display_order: Mapped[int]
    weight: Mapped[float]
    is_active: Mapped[bool]
    metadata_json: Mapped[dict[str, Any]]

    # Relationships
    ruleset: Mapped[ValuationRuleset] = relationship(back_populates="rule_groups")
    rules: Mapped[list[ValuationRuleV2]] = relationship(back_populates="group")
```

### Listing Model - valuation_breakdown Field
**Table:** `listing`
**Field:** `valuation_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON)`

**Structure (as stored in JSON):**
```python
{
    "ruleset": {
        "id": 1,
        "name": "Production Rules v2"
    },
    "matched_rules_count": 4,
    "total_adjustment": -75.0,
    "adjustments": [
        {
            "rule_id": 10,
            "rule_name": "RAM Deduction - 16GB",
            "adjustment_usd": -50.0,
            "actions": [
                {
                    "action_type": "component_deduction",
                    "metric": "ram_capacity_gb",
                    "value": -50.0,
                    "details": {"multiplier": 1.0}
                }
            ]
        },
        # ... more adjustments
    ],
    "legacy_lines": [...]  # Backward compatibility
}
```

**Note:** This JSON does NOT include `rule_description`, `rule_group_id`, or `rule_group_name`. These must be fetched from database.

---

## Success Criteria

### Backend Requirements
- [ ] `ValuationAdjustmentDetail` schema updated with new optional fields
- [ ] Endpoint enriches adjustments with rule metadata from database
- [ ] Endpoint includes inactive rules (zero adjustments) from same ruleset
- [ ] Eager loading prevents N+1 query problems
- [ ] Response time remains < 500ms (p95)
- [ ] Backward compatibility maintained (all new fields optional)
- [ ] Returns 404 if listing not found (already implemented ✅)

### Frontend Requirements
- [ ] Modal displays two sections: "ACTIVE CONTRIBUTORS" and "INACTIVE RULES"
- [ ] Contributors sorted by absolute adjustment amount (descending)
- [ ] Inactive rules sorted alphabetically by name
- [ ] Section headers show rule counts dynamically
- [ ] RuleGroup badges displayed on rule cards (if rule has group)
- [ ] Rule names are clickable `Link` components
- [ ] Rule name links navigate to `/valuation/rules/{rule_id}`
- [ ] Inactive section is collapsible (default: open if ≤10 rules)
- [ ] Hover tooltips show rule descriptions (200ms delay)
- [ ] All interactive elements keyboard accessible (Tab, Enter, Space)
- [ ] Focus indicators visible on all interactive elements
- [ ] ARIA labels present for screen readers
- [ ] Respects `prefers-reduced-motion` for animations

### Quality Requirements
- [ ] No TypeScript errors in frontend code
- [ ] No Python type errors in backend code
- [ ] No console warnings in browser
- [ ] React Query cache invalidation working correctly
- [ ] Performance: no jank in animations
- [ ] Cross-browser tested (Chrome, Firefox, Safari)
- [ ] Accessibility audit passing (axe-core)
- [ ] Manual keyboard navigation testing complete

---

## Implementation Notes

### Backend Performance Considerations

**Eager Loading Strategy:**
```python
# Use selectinload to avoid N+1 queries
rules = await session.execute(
    select(ValuationRuleV2)
    .options(selectinload(ValuationRuleV2.group))
    .where(ValuationRuleV2.id.in_(rule_ids))
)
```

**Why selectinload vs joinedload:**
- `selectinload`: Separate query, more efficient for one-to-many
- `joinedload`: Single query with JOIN, better for many-to-one
- Rule → Group is many-to-one, but we're loading multiple rules
- `selectinload` avoids cartesian product issues

**Caching Consideration:**
- If performance becomes issue, consider Redis caching
- Cache key: `valuation_breakdown:{listing_id}:{updated_at}`
- TTL: 1 hour or until listing updated
- Invalidate on rule changes (future enhancement)

### Frontend TypeScript Types

**Need to update types:**
```typescript
// apps/web/types/listings.ts
interface ValuationAdjustment {
  rule_id: number | null;
  rule_name: string;
  rule_description?: string | null;  // NEW
  rule_group_id?: number | null;  // NEW
  rule_group_name?: string | null;  // NEW
  adjustment_amount: number;
  actions: ValuationAdjustmentAction[];
}
```

### Radix UI Component Installation

**Check if components exist:**
- `Collapsible`: Check `/apps/web/components/ui/collapsible.tsx`
- `HoverCard`: Check `/apps/web/components/ui/hover-card.tsx`

**If missing, install via shadcn/ui CLI:**
```bash
npx shadcn-ui@latest add collapsible
npx shadcn-ui@latest add hover-card
```

---

## Testing Strategy

### Backend Testing
1. **Unit Tests** (to be added):
   - Test schema validation with new optional fields
   - Test enrichment logic with mock database
   - Test handling of missing rule IDs
   - Test inactive rules query logic

2. **Integration Tests** (to be added):
   - Test full endpoint with real database
   - Verify eager loading works correctly
   - Test performance with large rulesets (>50 rules)
   - Test backward compatibility (old data format)

3. **Manual Testing:**
   - Call endpoint via curl/Postman
   - Verify response includes new fields
   - Check response time with query profiling
   - Test with listings having no rules

### Frontend Testing
1. **Unit Tests** (to be added):
   - Test sorting logic with various adjustment amounts
   - Test section separation logic
   - Test collapsible state management
   - Test hover card trigger timing

2. **Integration Tests** (to be added):
   - Test modal open/close with React Query data
   - Test navigation to rule detail pages
   - Test keyboard navigation through interactive elements
   - Test empty states (no contributors, no inactive)

3. **Accessibility Testing:**
   - Run axe-core in browser DevTools
   - Test keyboard navigation (Tab, Enter, Space, Escape)
   - Test screen reader announcements (NVDA/JAWS/VoiceOver)
   - Test focus management on modal open/close
   - Test reduced motion preference

4. **Manual Testing:**
   - Open breakdown modal for various listings
   - Verify contributors/inactive sections appear correctly
   - Click rule names and verify navigation
   - Hover over rule names and verify tooltips
   - Toggle inactive section collapse
   - Test with >10 inactive rules (default collapsed)
   - Test with <10 inactive rules (default open)

---

## Time Estimate
**Total:** 5 days (as per original plan)

**Breakdown:**
- Day 1: Backend endpoint enhancement (TASK-301, TASK-302)
- Day 2: Frontend sorting + section headers (TASK-303, TASK-304)
- Day 3: RuleGroup badges + clickable links (TASK-305, TASK-306)
- Day 4: Collapsible section + hover tooltips (TASK-307, TASK-308)
- Day 5: Testing, accessibility audit, polish

**Estimated Completion:** 2025-10-28

---

## Dependencies

### Backend Dependencies
- SQLAlchemy 2.0+ (async support) ✅
- Pydantic v2 (schema validation) ✅
- FastAPI (endpoint framework) ✅

### Frontend Dependencies
- React 18+ ✅
- Next.js 14+ ✅
- React Query v5 ✅
- Radix UI primitives:
  - `@radix-ui/react-collapsible` (check if installed)
  - `@radix-ui/react-hover-card` (check if installed)
- Tailwind CSS 3+ ✅

### Coordination Dependencies
- Backend must complete before frontend can integrate
- Frontend can prototype with mock data if backend delayed
- Both teams should coordinate on schema shape early

---
