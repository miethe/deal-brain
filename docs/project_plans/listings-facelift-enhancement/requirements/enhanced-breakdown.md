# Feature Requirements: Enhanced Valuation Breakdown Modal

**Status:** Draft
**Priority:** High
**Affects:** Valuation visibility, rule navigation, information architecture

---

## Overview

Transform the valuation breakdown modal from a flat list into an organized, navigable interface that separates contributing rules from inactive ones, provides organizational context (RuleGroups), and enables direct navigation to rule details.

---

## User Story

As a Deal Brain user viewing the full valuation breakdown, I want to see all rules organized with contributors at the top and inactive rules below, with clear labels for RuleGroups/Rulesets and clickable rule names, so that I can fully understand the pricing logic and navigate to rule details.

---

## Acceptance Criteria

### Rule Organization

1. **Section 1: Contributors** - Rules with non-zero adjustments, sorted by absolute amount (descending)
2. **Section 2: Inactive Rules** - Rules with zero adjustment, sorted alphabetically by name
3. Section headers clearly label each category
4. Separator between sections

### Rule Card Enhancements

1. Display RuleGroup name (if rule belongs to a group): small badge/label
2. Display parent Ruleset name: contextual label or breadcrumb
3. Rule name is clickable (navigates to rule detail or edit page)
4. Hover state for clickable rule names
5. Tooltip on hover showing rule description (if available)

### Visual Indicators

1. Contributors: bold card border, prominent adjustment display
2. Inactive: muted border, gray text, collapsible (optional)
3. RuleGroup badge: subtle background, small text
4. Ruleset context: displayed in header or per-rule

### Interaction Design

1. Click rule name → navigate to `/valuation/rules/[id]`
2. Hover rule name → show tooltip with description
3. Click RuleGroup badge → filter to show only rules in that group (future)
4. Collapsible inactive section (expand/collapse toggle)

### Accessibility

1. All clickable elements keyboard accessible
2. Clear focus indicators on interactive elements
3. Screen reader announces section headers
4. ARIA labels for badges and interactive elements

---

## UI/UX Specifications

### Section Headers

- Typography: `text-sm font-semibold uppercase tracking-wide text-muted-foreground`
- Margin: `mt-6 mb-3` for section separation
- Format: "ACTIVE CONTRIBUTORS (4)", "INACTIVE RULES (8)"

### Rule Cards

- Contributor cards: `border-2` (thicker), `hover:bg-accent/5`
- Inactive cards: `border` (standard), `text-muted-foreground`
- RuleGroup badge: Badge `variant="outline"` with small text
- Ruleset: displayed in modal header ("Calculated using [Ruleset Name]")

### Clickable Rule Names

- Color: `text-primary` (inherit link color)
- Hover: `underline`, `cursor-pointer`
- Font: `font-semibold` for contributors, `font-medium` for inactive

### Collapsible Inactive Section

- Default state: collapsed if >10 inactive rules
- Toggle: "Show 8 inactive rules" / "Hide inactive rules"
- Animated expansion with smooth height transition

---

## Technical Considerations

### API Requirements

Extend `ValuationBreakdownModal` component and backend:

```python
# Enhanced ValuationAdjustment interface
class ValuationAdjustment(BaseModel):
    rule_id: int | None = None
    rule_name: str
    rule_description: str | None = None          # NEW
    rule_group_id: int | None = None             # NEW
    rule_group_name: str | None = None           # NEW
    adjustment_amount: Decimal
    actions: list[ValuationAdjustmentAction]
```

### Implementation Details

- Fetch rule metadata (group, ruleset) from API if not already included
- Modify `/v1/listings/{id}/valuation-breakdown` endpoint to include rule metadata
- Use Next.js `Link` component for navigation
- Memoize sorting logic for performance
- Implement collapsible section with Radix UI Collapsible primitive

---

## Sorting Logic

### Contributors (Active Rules)

1. Primary sort: `Math.abs(adjustment_amount)` descending (highest impact first)
2. Secondary sort: `rule_name` alphabetically (tiebreaker)

### Inactive Rules

1. Primary sort: `rule_name` alphabetically (A-Z)
2. No secondary sort needed

---

## Mockup Reference

```
┌─────────────────────────────────────────────────────┐
│ Valuation Breakdown                                  │
│ Calculated using Ruleset: Production Rules v2        │
├─────────────────────────────────────────────────────┤
│                                                       │
│ [Image] Title: Intel NUC i7-1165G7 16GB              │
│         Listing ID #1234                             │
│         Base: $450 → Adjusted: $375 (-$75)           │
│                                                       │
├─────────────────────────────────────────────────────┤
│ ACTIVE CONTRIBUTORS (4)                              │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 RAM Deduction - 16GB    [Hardware] -$50.00│   │
│ │    Ruleset: Production Rules v2                │   │
│ │    • Deduct $25 per 8GB RAM                    │   │
│ │    • Apply condition multiplier                │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 CPU Age Adjustment      [Time-based] -$25.00│   │
│ │    Ruleset: Production Rules v2                │   │
│ │    • Deduct $5 per year since release         │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 Form Factor Premium     [Metadata]  -$10.00│   │
│ │    Ruleset: Production Rules v2                │   │
│ │    • Add premium for Mini PC form factor      │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 Condition Factor        [Quality]   +$10.00│   │
│ │    Ruleset: Production Rules v2                │   │
│ │    • Refurbished: 102% of base               │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
├─────────────────────────────────────────────────────┤
│ ▼ INACTIVE RULES (8)                                 │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 Brand Premium Rule      [Metadata]    $0.00│   │
│ │    Did not match: manufacturer != 'Intel'     │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
│ [... 7 more collapsed ...]                           │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Tasks

See [Implementation Plan - Phase 3: Enhanced Breakdown Modal](../../IMPLEMENTATION_PLAN.md#phase-3-enhanced-breakdown-modal-week-2-3) for detailed tasks and code changes.

**Key Tasks:**
- TASK-301: Backend - Enhance valuation breakdown endpoint
- TASK-302: Backend - Eager-load rule metadata
- TASK-303: Frontend - Implement sorting logic
- TASK-304: Frontend - Add section headers and separators
- TASK-305: Frontend - Add RuleGroup badges
- TASK-306: Frontend - Make rule names clickable
- TASK-307: Frontend - Implement collapsible section
- TASK-308: Frontend - Add hover tooltips

---

## Success Criteria (QA)

- [ ] Backend returns `rule_description`, `rule_group_id`, `rule_group_name` for all adjustments
- [ ] Backend includes inactive rules (zero adjustment) in response
- [ ] Modal displays two sections: "Active Contributors" and "Inactive Rules"
- [ ] Contributors sorted by absolute amount descending
- [ ] Inactive rules sorted alphabetically
- [ ] RuleGroup badges visible on rule cards
- [ ] Rule names are clickable and navigate to rule detail page
- [ ] Hover tooltips show rule descriptions
- [ ] Inactive section is collapsible if >10 rules
- [ ] All interactive elements keyboard accessible
- [ ] Section headers announced by screen readers
- [ ] ARIA labels present on all badges and interactive elements

---

## Related Documentation

- **[Implementation Plan - Phase 3](../../IMPLEMENTATION_PLAN.md#phase-3-enhanced-breakdown-modal-week-2-3)**
- **[Smart Rule Display Feature](./smart-rule-display.md)** - Related filtered display
- **[Data Model - API Contracts](./data-model.md)** - Enhanced adjustment schema
- **[Design - UI/UX Specs](../design/ui-ux.md)** - Component styling details
