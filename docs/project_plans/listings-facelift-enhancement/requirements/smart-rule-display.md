# Feature Requirements: Smart Rule Display in Valuation Tab

**Status:** Draft
**Priority:** High
**Affects:** Valuation clarity, information architecture

---

## Overview

Intelligently filter and display only the most impactful valuation rules (max 4) in the modal valuation tab, reducing visual clutter while maintaining access to all rules via a "View Full Breakdown" link.

---

## User Story

As a Deal Brain user viewing a listing's valuation tab, I want to see only the rules that actually contributed to the price adjustment (up to 4 most significant), so that I can quickly understand what affected the price without visual clutter from inactive rules.

---

## Acceptance Criteria

### Rule Display Logic

1. Show maximum of 4 rules with non-zero adjustments
2. Sort by absolute adjustment amount (descending)
3. Display total count of hidden rules if more than 4 contributors exist
4. Show "No active rules" message if zero contributors

### Contributor Identification

1. Rule has non-zero `adjustment_amount` value
2. Display both positive (price increases) and negative (price decreases) adjustments
3. Color-code adjustments: green for savings (negative), red for premiums (positive)

### View All Option

1. "View Full Breakdown" button always visible
2. Opens `ValuationBreakdownModal` with all rules
3. Button shows count: "View Full Breakdown (12 rules)"

### Visual Design

1. Each rule card shows: name, adjustment amount, action count
2. Compact card layout optimized for 4-item display
3. Clear visual hierarchy (most impactful at top)
4. Consistent with existing modal design patterns

---

## UI/UX Specifications

### Rule Card Layout

- **Border:** rounded-md with border
- **Padding:** p-3
- **Font:** rule name (text-sm font-medium), amount (font-semibold)
- **Color:** adjustment amounts use semantic colors

### Sorting Priority

1. Absolute adjustment amount (highest first)
2. Rule name alphabetically (tiebreaker)

### Empty State

- Border-dashed card with muted text
- Message: "No rule-based adjustments were applied to this listing."
- No "View Full Breakdown" button if zero rules

---

## Technical Considerations

- Filter logic in `ListingValuationTab` component
- Memoize filtered/sorted results for performance
- Ensure adjustment amounts accurate (from API response)
- Handle null/undefined adjustment amounts gracefully

---

## Color Coding Reference

- **Great Deal (savings ≥ threshold):** `text-emerald-600` (green)
- **Good Deal (savings < threshold):** `text-blue-600` (blue)
- **Premium (price increase):** `text-red-600` (red)
- **Neutral (no change):** `text-muted-foreground` (gray)

---

## Mockup Reference

```
┌─────────────────────────────────────────┐
│ Current valuation                        │
│ Calculated using Ruleset Alpha.          │
│                                           │
│ ┌─────────────────────────────────────┐ │
│ │ Base Price    Adjusted    Savings   │ │
│ │ $450.00       $375.00     -$75.00   │ │
│ └─────────────────────────────────────┘ │
│                                           │
│ ⚡ 4 rules applied                        │
│ [View Full Breakdown (12 rules)]         │
│                                           │
│ ┌─────────────────────────────────────┐ │
│ │ RAM Deduction - 16GB                │ │
│ │ 2 actions              -$50.00      │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ CPU Age Adjustment                  │ │
│ │ 1 action               -$25.00      │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Condition Factor - Refurbished      │ │
│ │ 1 action               +$10.00      │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Form Factor Premium - Mini PC       │ │
│ │ 1 action               -$10.00      │ │
│ └─────────────────────────────────────┘ │
│                                           │
│ + 8 more rules in breakdown              │
└─────────────────────────────────────────┘
```

---

## Implementation Tasks

See [Implementation Plan - Phase 2: Smart Rule Display](../../IMPLEMENTATION_PLAN.md#phase-2-smart-rule-display-week-1-2) for detailed tasks and code changes.

**Key Tasks:**
- TASK-201: Implement rule filtering logic
- TASK-202: Update rule cards display with count indicator
- TASK-203: Add empty state for zero contributors
- TASK-204: Color-code adjustments (green/red)

---

## Success Criteria (QA)

- [ ] Max 4 rules displayed in modal valuation tab
- [ ] Rules sorted by absolute adjustment amount (descending)
- [ ] Color-coding applied: green (savings), red (premiums)
- [ ] "View Full Breakdown" button shows total rule count
- [ ] Empty state shown if zero contributing rules
- [ ] All rules still accessible via "View Full Breakdown"
- [ ] Performance: rule filtering completes in <50ms
- [ ] Works with 0, 1, 4, 10+, and 100+ rules

---

## Related Documentation

- **[Implementation Plan - Phase 2](../../IMPLEMENTATION_PLAN.md#phase-2-smart-rule-display-week-1-2)**
- **[Enhanced Valuation Breakdown Feature](./enhanced-breakdown.md)** - Related full breakdown display
- **[Data Model - API Contracts](./data-model.md)** - Adjustment schema details
