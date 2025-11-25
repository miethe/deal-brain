# Phase 2: Adjusted Value Renaming & Tooltips

**Objectives:**
- Rename "Adjusted Price" to "Adjusted Value" across application
- Add hover tooltips explaining valuation calculation
- Ensure accessibility (keyboard, screen readers)

**Prerequisites:**
- None (independent phase)

**Estimated Duration:** 3-4 days

---

## UX-001: Global Find-and-Replace for "Adjusted Price"

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 4 hours
**Dependencies:** None

**Acceptance Criteria:**
- [ ] All UI labels changed to "Adjusted Value"
- [ ] Code comments updated
- [ ] No breaking changes to API or props

**Implementation Steps:**

1. **Find all occurrences:**
   ```bash
   cd apps/web
   grep -r "Adjusted Price" --include="*.tsx" --include="*.ts"
   ```

2. **Update component files:**
   - `apps/web/components/listings/detail-page-layout.tsx`
   - `apps/web/components/listings/specifications-tab.tsx`
   - `apps/web/components/listings/valuation-tab.tsx`
   - `apps/web/components/listings/listings-table.tsx`
   - `apps/web/components/listings/catalog-card.tsx`

3. **Update type definitions:**
   - Keep `adjustedPrice` prop names (no breaking changes)
   - Update comments and labels only

4. **Verify no missed instances:**
   ```bash
   grep -r "Adjusted Price" apps/web
   # Should return zero results
   ```

**Testing Requirements:**
- [ ] Visual regression test: All pages display "Adjusted Value"
- [ ] E2E test: Verify terminology in all views

---

## UX-002: Create Valuation Tooltip Component

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 8 hours
**Dependencies:** UX-001

**Acceptance Criteria:**
- [ ] Reusable ValuationTooltip component
- [ ] Shows calculation summary (list price, adjustments, adjusted value)
- [ ] Lists top 3-5 rules by impact
- [ ] Link to full breakdown modal
- [ ] Accessible (keyboard, screen reader)

**Implementation Steps:**

1. **Create component** (`apps/web/components/listings/valuation-tooltip.tsx`):

```typescript
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { InfoIcon } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';

interface ValuationTooltipProps {
  listPrice: number;
  adjustedValue: number;
  valuationBreakdown?: any; // ValuationBreakdown type
  onViewDetails?: () => void;
  children?: React.ReactNode;
}

export function ValuationTooltip({
  listPrice,
  adjustedValue,
  valuationBreakdown,
  onViewDetails,
  children,
}: ValuationTooltipProps) {
  const delta = listPrice - adjustedValue;
  const deltaPercent = (delta / listPrice) * 100;

  // Extract top rules by absolute impact
  const topRules = useMemo(() => {
    if (!valuationBreakdown?.matched_rules) return [];
    return valuationBreakdown.matched_rules
      .sort((a, b) => Math.abs(b.adjustment) - Math.abs(a.adjustment))
      .slice(0, 5);
  }, [valuationBreakdown]);

  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          {children || (
            <button
              className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground"
              aria-label="View valuation details"
            >
              <InfoIcon className="h-4 w-4" />
            </button>
          )}
        </TooltipTrigger>
        <TooltipContent
          side="top"
          className="max-w-[320px] p-3"
          aria-label="Valuation calculation details"
        >
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Adjusted Value Calculation</h4>

            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">List Price:</span>
                <span className="font-medium">{formatCurrency(listPrice)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Adjustments:</span>
                <span className={delta > 0 ? 'text-green-600' : 'text-red-600'}>
                  {delta > 0 ? '-' : '+'}{formatCurrency(Math.abs(delta))}
                </span>
              </div>
              <div className="flex justify-between border-t pt-1">
                <span className="font-medium">Adjusted Value:</span>
                <span className="font-semibold">{formatCurrency(adjustedValue)}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                ({deltaPercent > 0 ? '' : '+'}{deltaPercent.toFixed(1)}% {deltaPercent > 0 ? 'savings' : 'premium'})
              </div>
            </div>

            {topRules.length > 0 && (
              <div className="space-y-1 border-t pt-2">
                <p className="text-xs text-muted-foreground">
                  Applied {valuationBreakdown.matched_rules_count} valuation rules:
                </p>
                <ul className="space-y-1 text-xs">
                  {topRules.map((rule) => (
                    <li key={rule.rule_id} className="flex justify-between">
                      <span className="truncate mr-2">• {rule.rule_name}</span>
                      <span className={rule.adjustment < 0 ? 'text-green-600' : 'text-red-600'}>
                        {rule.adjustment < 0 ? '' : '+'}{formatCurrency(rule.adjustment)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {onViewDetails && (
              <button
                onClick={onViewDetails}
                className="w-full mt-2 text-xs text-primary hover:underline flex items-center justify-center gap-1"
              >
                View Full Breakdown →
              </button>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
```

2. **Add keyboard accessibility:**
   - Tooltip triggers on focus (Tab key)
   - Dismisses on Escape key
   - Link is keyboard navigable

3. **Add screen reader support:**
   - Use `aria-label` and `aria-describedby`
   - Announce tooltip content

**Testing Requirements:**
- [ ] Unit test: Tooltip renders with correct content
- [ ] Unit test: Top rules sorted by impact
- [ ] A11y test: Keyboard navigation works
- [ ] A11y test: Screen reader announces content

---

## UX-003: Integrate Tooltip in Detail Page

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 4 hours
**Dependencies:** UX-002

**Acceptance Criteria:**
- [ ] Tooltip appears on "Adjusted Value" in hero section
- [ ] Tooltip links to existing breakdown modal
- [ ] Styling consistent with design system

**Implementation Steps:**

1. **Update DetailPageLayout** (`apps/web/components/listings/detail-page-layout.tsx`):

```typescript
import { ValuationTooltip } from './valuation-tooltip';

export function DetailPageLayout({ listing }: DetailPageLayoutProps) {
  const [showBreakdownModal, setShowBreakdownModal] = useState(false);

  return (
    <div>
      {/* Hero section */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <span className="text-sm text-muted-foreground">List Price</span>
          <p className="text-2xl font-bold">{formatCurrency(listing.price_usd)}</p>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Adjusted Value</span>
            <ValuationTooltip
              listPrice={listing.price_usd}
              adjustedValue={listing.adjusted_price_usd}
              valuationBreakdown={listing.valuation_breakdown}
              onViewDetails={() => setShowBreakdownModal(true)}
            />
          </div>
          <p className="text-2xl font-bold">{formatCurrency(listing.adjusted_price_usd)}</p>
        </div>
      </div>

      {/* Breakdown modal */}
      <ValuationBreakdownModal
        open={showBreakdownModal}
        onOpenChange={setShowBreakdownModal}
        listing={listing}
      />
    </div>
  );
}
```

**Testing Requirements:**
- [ ] E2E test: Tooltip appears on hover
- [ ] E2E test: Clicking link opens modal
- [ ] Visual test: Styling matches design

---

**Phase 2 Summary:**

| Task | Type | Effort | Status |
|------|------|--------|--------|
| UX-001 | Frontend | 4h | Pending |
| UX-002 | Frontend | 8h | Pending |
| UX-003 | Frontend | 4h | Pending |
| Testing | All | 8h | Pending |
| **Total** | | **28h** | |
