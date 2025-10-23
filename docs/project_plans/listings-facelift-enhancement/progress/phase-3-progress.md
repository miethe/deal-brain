# Phase 3 Progress: Enhanced Breakdown Modal

**Status:** In Progress
**Started:** 2025-10-23
**Phase Duration:** 5 days (estimate)

## Objective
Reorganize breakdown modal with contributors/inactive sections, clickable rules, RuleGroup badges, and rich navigation.

## Task Breakdown

### Backend Tasks

#### TASK-301: Enhance valuation breakdown endpoint ✅
**Status:** ANALYSIS COMPLETE - Implementation Ready
**Owner:** python-backend-engineer (to be delegated)
**Files:**
- `/apps/api/dealbrain_api/api/listings.py` (lines 344-440)
- `/apps/api/dealbrain_api/api/schemas/listings.py` (lines 99-108)

**Requirements:**
- Add `rule_description` field to ValuationAdjustmentDetail schema
- Add `rule_group_id` field to ValuationAdjustmentDetail schema
- Add `rule_group_name` field to ValuationAdjustmentDetail schema
- Include ALL rules (active with adjustments + inactive with zero adjustments)
- Return parent ruleset information (already implemented ✅)

**Current State:**
- Endpoint exists at `/v1/listings/{id}/valuation-breakdown`
- Returns adjustments from `listing.valuation_breakdown` JSON field
- Schema: `ValuationAdjustmentDetail` has `rule_id`, `rule_name`, `adjustment_amount`, `actions`
- Missing: `rule_description`, `rule_group_id`, `rule_group_name`
- Missing: inactive rules (zero-adjustment rules not included)

**Database Schema Available:**
- `ValuationRuleV2` model has:
  - `id`, `name`, `description` ✅
  - `group_id` (foreign key to ValuationRuleGroup) ✅
  - `is_active` flag ✅
- `ValuationRuleGroup` model has:
  - `id`, `name`, `category`, `description` ✅
  - `ruleset_id` (foreign key) ✅

**Implementation Approach:**
1. Update `ValuationAdjustmentDetail` Pydantic schema with new fields
2. Modify endpoint to eager-load rule and group data
3. Parse `valuation_breakdown` JSON and enrich with database lookups
4. Add logic to fetch inactive rules from same ruleset
5. Maintain backward compatibility (all new fields optional)

---

#### TASK-302: Eager-load rule metadata
**Status:** Pending (part of TASK-301)
**Owner:** python-backend-engineer
**Files:** Same as TASK-301

**Requirements:**
- Use SQLAlchemy eager loading (`.options(selectinload())`)
- Load `ValuationRuleV2.group` relationship
- Avoid N+1 query problems
- Keep response time < 500ms

---

### Frontend Tasks

#### TASK-303: Implement sorting logic ✅
**Status:** DESIGN COMPLETE - Ready for Implementation
**Owner:** ui-engineer (to be delegated)
**Files:** `/apps/web/components/listings/valuation-breakdown-modal.tsx`

**Requirements:**
- Contributors: Sort by `Math.abs(adjustment_amount)` descending
- Inactive: Sort alphabetically by `rule_name`
- Use `useMemo` for performance
- Dependency: adjustments array

**Implementation Pattern:**
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

---

#### TASK-304: Add section headers and separators
**Status:** Pending
**Owner:** ui-engineer
**Files:** `/apps/web/components/listings/valuation-breakdown-modal.tsx`

**Requirements:**
- Section 1 header: "ACTIVE CONTRIBUTORS (X)"
- Section 2 header: "INACTIVE RULES (Y)"
- Visual separator (Radix UI Separator) between sections
- Typography: `text-sm font-semibold uppercase tracking-wide text-muted-foreground`

---

#### TASK-305: Add RuleGroup badges
**Status:** Pending
**Owner:** ui-engineer
**Files:** `/apps/web/components/listings/valuation-breakdown-modal.tsx`

**Requirements:**
- Display `rule_group_name` as Badge component
- Badge variant: `outline`
- Placement: Near rule name in card header
- Handle null/undefined group names gracefully

---

#### TASK-306: Make rule names clickable
**Status:** Pending
**Owner:** ui-engineer
**Files:** `/apps/web/components/listings/valuation-breakdown-modal.tsx`

**Requirements:**
- Wrap rule name in Next.js `Link` component
- Navigate to: `/valuation/rules/{rule_id}`
- Styling: `text-primary hover:underline cursor-pointer`
- Accessibility: keyboard navigable, focus indicators

---

#### TASK-307: Implement collapsible inactive section
**Status:** Pending
**Owner:** ui-engineer
**Files:** `/apps/web/components/listings/valuation-breakdown-modal.tsx`

**Requirements:**
- Use Radix UI `Collapsible` primitive
- Default state: collapsed if >10 inactive rules
- Toggle button: "Show X inactive rules" / "Hide inactive rules"
- Smooth animation (height transition)

---

#### TASK-308: Add hover tooltips with rule descriptions
**Status:** Pending
**Owner:** ui-engineer
**Files:** `/apps/web/components/listings/valuation-breakdown-modal.tsx`

**Requirements:**
- Use Radix UI `HoverCard` primitive
- Trigger: rule name hover
- Content: `rule_description` from API
- Delay: 200ms before showing
- Handle null descriptions gracefully

---

## Success Criteria

### Backend
- [ ] API returns `rule_description`, `rule_group_id`, `rule_group_name` for all adjustments
- [ ] API includes inactive rules (zero adjustment) in response
- [ ] Endpoint response time remains < 500ms (p95)
- [ ] Backward compatibility maintained (new fields optional)

### Frontend
- [ ] Modal displays two distinct sections: Contributors and Inactive
- [ ] Contributors sorted by absolute adjustment amount (descending)
- [ ] Inactive rules sorted alphabetically
- [ ] Section headers show rule counts
- [ ] RuleGroup badges displayed on rule cards
- [ ] Rule names are clickable (navigate to rule detail)
- [ ] Inactive section is collapsible (if >10 rules)
- [ ] Hover tooltips show rule descriptions
- [ ] All interactive elements keyboard accessible
- [ ] ARIA labels present for screen readers
- [ ] Respects `prefers-reduced-motion`

### Quality
- [ ] No TypeScript errors
- [ ] No console warnings
- [ ] React Query cache working correctly
- [ ] Performance: no jank in animations
- [ ] Cross-browser tested (Chrome, Firefox, Safari)
- [ ] Accessibility audit passing (axe-core)

---

## Blockers & Risks

### Current Blockers
- None

### Risks
1. **Performance Risk:** Eager-loading rules could slow down endpoint
   - **Mitigation:** Use selectinload, add caching if needed
2. **Data Availability:** Some listings may not have rule metadata in JSON
   - **Mitigation:** Handle null/undefined gracefully, provide fallbacks
3. **Inactive Rules:** Logic to fetch all inactive rules needs careful design
   - **Mitigation:** Query rules from same ruleset, filter by rule_id in adjustments

---

## Timeline

| Day | Tasks | Status |
|-----|-------|--------|
| Day 1 | TASK-301, TASK-302 (Backend) | Pending |
| Day 2 | TASK-303, TASK-304 (Sorting + Headers) | Pending |
| Day 3 | TASK-305, TASK-306 (Badges + Links) | Pending |
| Day 4 | TASK-307, TASK-308 (Collapsible + Tooltips) | Pending |
| Day 5 | Testing, accessibility audit, polish | Pending |

---

## Notes

### Architectural Decisions Made
- **ADR-007:** Client-side sorting for contributors/inactive (presentation logic)
- **ADR-008:** Enrich API response with database lookups (not just JSON parsing)
- **ADR-009:** Use Radix UI primitives (Collapsible, HoverCard) for consistency

### Dependencies
- Backend changes must complete before frontend work can begin
- Frontend can prototype with mock data if needed

### Related Context
- See `/docs/project_plans/listings-facelift-enhancement/context/listings-facelift-context.md` for full project context
- Phase 1 & 2 already completed (auto-close modal, smart rule display)
