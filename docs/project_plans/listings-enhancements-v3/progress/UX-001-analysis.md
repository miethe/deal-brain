# UX-001: Global Find-and-Replace Analysis

**Task:** Replace "Adjusted Price" with "Adjusted Value" across frontend
**Effort:** 4 hours
**Status:** Analysis Complete, Ready for Implementation

---

## Occurrences Found

### Case-Sensitive "Adjusted Price" (3 files)
1. `/mnt/containers/deal-brain/apps/web/components/listings/valuation-mode-toggle.tsx:48` - Label text
2. `/mnt/containers/deal-brain/apps/web/components/listings/detail-page-hero.tsx:108` - Title prop
3. `/mnt/containers/deal-brain/apps/web/app/listings/_components/master-detail-view/detail-panel.tsx:117` - Label prop

### Case-Insensitive "adjusted price" (14 occurrences total)

**UI Labels and Text (High Priority):**
1. `apps/web/app/listings/page.tsx:95` - Description text
2. `apps/web/app/admin/page.tsx:357` - Description text
3. `apps/web/components/listings/valuation-mode-toggle.tsx:38` - aria-label
4. `apps/web/components/listings/valuation-mode-toggle.tsx:48` - Button label
5. `apps/web/app/listings/_components/master-detail-view/detail-panel.tsx:117` - Label
6. `apps/web/components/listings/detail-page-hero.tsx:108` - Title
7. `apps/web/components/listings/valuation-breakdown-modal.tsx:232` - Label
8. `apps/web/components/listings/valuation-breakdown-modal.tsx:329` - Label text
9. `apps/web/components/listings/listing-valuation-tab.tsx:330` - Label
10. `apps/web/components/dashboard/dashboard-summary.tsx:61` - Description

**Comments and Tooltips (Medium Priority):**
11. `apps/web/app/listings/_components/grid-view/listing-card.tsx:24` - Comment
12. `apps/web/app/listings/_components/grid-view/performance-badges.tsx:95` - Tooltip text
13. `apps/web/app/listings/_components/grid-view/performance-badges.tsx:116` - Tooltip text
14. `apps/web/components/listings/listings-table.tsx:599` - Tooltip text

### Props and Variable Names (DO NOT CHANGE)

**TypeScript files with `adjustedPrice` prop/variable (6 files):**
- `components/listings/listings-table.tsx`
- `components/listings/listing-overview-modal.tsx`
- `components/listings/listing-valuation-tab.tsx`
- `components/listings/valuation-breakdown-modal.tsx`
- `lib/valuation-utils.ts`
- `components/listings/valuation-cell.tsx`

**Decision:** Keep all `adjustedPrice` prop/variable names unchanged (no breaking changes)

---

## Implementation Strategy

### Phase 1: Update UI Labels (Priority 1)
Change these 10 user-visible strings from "Adjusted Price" → "Adjusted Value":
- valuation-mode-toggle.tsx (label + aria-label)
- detail-page-hero.tsx (title)
- detail-panel.tsx (label)
- valuation-breakdown-modal.tsx (2 labels)
- listing-valuation-tab.tsx (label)
- dashboard-summary.tsx (description)
- app/listings/page.tsx (description)
- app/admin/page.tsx (description)

### Phase 2: Update Comments and Tooltips (Priority 2)
Change these 4 developer-facing strings:
- listing-card.tsx (comment)
- performance-badges.tsx (2 tooltips)
- listings-table.tsx (tooltip)

### Phase 3: Verification
- Search for any remaining "adjusted price" (should be zero in text)
- Verify `adjustedPrice` props/variables still exist (should be unchanged)
- Visual regression test all affected pages

---

## No Breaking Changes

**API Contract Preserved:**
- Backend API still returns `adjusted_price_usd`
- Frontend props still named `adjustedPrice`
- Only UI display labels changed

**Risk Assessment:** LOW
- Cosmetic changes only
- No TypeScript recompilation needed
- No API changes required

---

## Testing Requirements

**Visual Tests:**
- [ ] Data Tab: Column header shows "Adjusted Value"
- [ ] Detail Page: Hero section shows "Adjusted Value"
- [ ] Valuation Modal: Breakdown shows "Adjusted Value"
- [ ] Dashboard: Summary card shows "Adjusted Value"
- [ ] Valuation Toggle: Button shows "Adjusted Value"

**Functional Tests:**
- [ ] All existing tests still pass
- [ ] No TypeScript compilation errors
- [ ] No console warnings

**Accessibility Tests:**
- [ ] aria-label updated correctly
- [ ] Screen reader announces "Adjusted Value"

---

## Files to Modify

1. `/mnt/containers/deal-brain/apps/web/components/listings/valuation-mode-toggle.tsx`
2. `/mnt/containers/deal-brain/apps/web/components/listings/detail-page-hero.tsx`
3. `/mnt/containers/deal-brain/apps/web/app/listings/_components/master-detail-view/detail-panel.tsx`
4. `/mnt/containers/deal-brain/apps/web/app/listings/page.tsx`
5. `/mnt/containers/deal-brain/apps/web/app/admin/page.tsx`
6. `/mnt/containers/deal-brain/apps/web/app/listings/_components/grid-view/listing-card.tsx`
7. `/mnt/containers/deal-brain/apps/web/app/listings/_components/grid-view/performance-badges.tsx`
8. `/mnt/containers/deal-brain/apps/web/components/listings/listings-table.tsx`
9. `/mnt/containers/deal-brain/apps/web/components/listings/valuation-breakdown-modal.tsx`
10. `/mnt/containers/deal-brain/apps/web/components/listings/listing-valuation-tab.tsx`
11. `/mnt/containers/deal-brain/apps/web/components/dashboard/dashboard-summary.tsx`

**Total:** 11 files to update

---

## Next Steps

1. Delegate to frontend-developer for systematic replacement
2. Verify all changes with grep search
3. Run TypeScript compiler check
4. Visual spot-check key pages
5. Update progress tracker
