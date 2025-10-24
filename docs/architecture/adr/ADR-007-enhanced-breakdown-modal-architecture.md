# ADR-007: Enhanced Breakdown Modal Architecture

**Status:** Accepted
**Date:** 2025-10-23
**Decision Makers:** Lead Architect
**Related Phase:** Phase 3 - Enhanced Breakdown Modal

---

## Context

The valuation breakdown modal currently displays a flat list of all rule adjustments applied to a listing. Users need better organization to understand which rules contributed to price changes vs. which rules were evaluated but didn't apply. Additionally, users want navigation to rule detail pages and contextual information about rule organization (RuleGroups).

**Current State:**
- Flat list of all adjustments from `listing.valuation_breakdown` JSON
- No distinction between contributors (non-zero) and inactive (zero)
- No rule metadata beyond name and ID
- No navigation or tooltips

**Desired State:**
- Two sections: "Active Contributors" and "Inactive Rules"
- Sorted by impact within each section
- RuleGroup badges for organizational context
- Clickable rule names for navigation
- Hover tooltips with rule descriptions
- Collapsible inactive section for large rulesets

---

## Decision

We will implement the enhanced breakdown modal using a three-part architectural approach:

### 1. Backend API Enhancement (ADR-008)
**Enrich valuation breakdown endpoint with database rule metadata**

- Parse `listing.valuation_breakdown` JSON for adjustment data
- Query `ValuationRuleV2` table to enrich with current metadata
- Eager-load `ValuationRuleGroup` relationship (avoid N+1)
- Include inactive rules from same ruleset
- Return enhanced schema with optional new fields

### 2. Client-Side Sorting (ADR-007)
**Implement sorting logic in React component with memoization**

- Sort contributors by absolute adjustment amount (descending)
- Sort inactive rules alphabetically
- Use `useMemo` to optimize performance
- Keep logic in presentation layer (UI concern)

### 3. Radix UI Primitives (ADR-009)
**Use `Collapsible` and `HoverCard` for interactions**

- `Collapsible` for inactive section (accessible, animated)
- `HoverCard` for rule description tooltips
- Maintain consistency with Deal Brain UI patterns
- Ensure WCAG 2.1 AA compliance

---

## Rationale

### Why Enrich API Response with Database Lookups?

**Alternatives Considered:**
1. **Store everything in JSON at valuation time**
   - Bloats JSON field size
   - Requires migration to add new metadata
   - Loses connection to current rule state

2. **Separate endpoint for rule metadata**
   - Requires multiple API calls from frontend
   - Complex client-side data merging
   - Poor performance (N+1 from frontend)

3. **Enrich endpoint with database lookups (CHOSEN)**
   - Single API call from frontend
   - Backend controls query optimization
   - Maintains historical adjustment data + current rule metadata
   - Flexible for future metadata additions

**Key Benefits:**
- Users see current rule descriptions (helpful if rules updated)
- Navigation links go to current rule detail pages
- Backend can optimize queries (eager loading, caching)
- Frontend stays simple (just render what API returns)

### Why Client-Side Sorting?

**Alternatives Considered:**
1. **Backend sorts adjustments**
   - API imposes presentation logic
   - Limits frontend flexibility
   - Harder to add future sort options

2. **Client-side sorting with memoization (CHOSEN)**
   - Presentation logic stays in presentation layer
   - Easy to add UI controls for sort order
   - `useMemo` ensures performance
   - Backend returns raw data, frontend decides presentation

**Key Benefits:**
- Separation of concerns (data vs. presentation)
- Frontend can easily add user-controlled sorting
- Backend stays focused on data retrieval
- Performance equivalent with proper memoization

### Why Radix UI Primitives?

**Alternatives Considered:**
1. **Custom collapsible/tooltip implementation**
   - Reinventing the wheel
   - Accessibility issues
   - Animation complexity

2. **Different UI library (Headless UI, Ark UI)**
   - Inconsistent with existing Deal Brain patterns
   - Different accessibility patterns
   - Additional bundle size

3. **Radix UI primitives (CHOSEN)**
   - Already used throughout Deal Brain
   - WCAG 2.1 AA compliant out of the box
   - Unstyled (full control over appearance)
   - Proven reliability

**Key Benefits:**
- Consistency with existing UI components
- Accessibility handled automatically
- Smooth animations with reduced motion support
- Battle-tested primitives

---

## Consequences

### Positive
- Users can distinguish between contributing and inactive rules
- Organized view reduces cognitive load
- Navigation to rule details improves workflow
- Tooltips provide contextual help
- Collapsible section handles large rulesets gracefully
- Accessible to keyboard and screen reader users
- Backend performance remains good (<500ms)

### Negative
- Backend complexity increases (database queries + enrichment logic)
- Frontend component becomes more complex
- Need to install Radix UI components if missing
- TypeScript types need updating
- More test coverage required

### Risks & Mitigations
1. **Risk:** Endpoint performance degrades with many rules
   - **Mitigation:** Use `selectinload()` for eager loading, add caching if needed

2. **Risk:** Some listings have malformed `valuation_breakdown` JSON
   - **Mitigation:** Robust null/undefined handling, fallback to basic display

3. **Risk:** Rules deleted after valuation can't be enriched
   - **Mitigation:** Show adjustment with name from JSON, handle missing rule_id

---

## Implementation Notes

### Backend Schema Extension

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

### Frontend Sorting Pattern

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

### Radix UI Component Usage

```tsx
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"

// Collapsible inactive section
<Collapsible open={inactiveOpen} onOpenChange={setInactiveOpen}>
  <CollapsibleTrigger>
    {inactiveOpen ? "Hide" : "Show"} {inactive.length} inactive rules
  </CollapsibleTrigger>
  <CollapsibleContent>
    {/* Inactive rule cards */}
  </CollapsibleContent>
</Collapsible>

// Hover tooltip
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

---

## Related Decisions

- **ADR-005:** Client-Side Rule Sorting with useMemo (Phase 2)
- **ADR-006:** Filter Zero-Value Adjustments (Phase 2)

---

## References

- [Phase 3 Implementation Plan](../project_plans/listings-facelift-enhancement/listings-facelift-implementation-plan.md#phase-3-enhanced-breakdown-modal-week-2-3)
- [Enhanced Breakdown Requirements](../project_plans/listings-facelift-enhancement/requirements/enhanced-breakdown.md)
- [Phase 3 Progress Tracker](../project_plans/listings-facelift-enhancement/progress/phase-3-progress.md)
- [Radix UI Collapsible Documentation](https://www.radix-ui.com/primitives/docs/components/collapsible)
- [Radix UI Hover Card Documentation](https://www.radix-ui.com/primitives/docs/components/hover-card)

---

**Version History:**
- v1.0 (2025-10-23): Initial decision document for Phase 3
