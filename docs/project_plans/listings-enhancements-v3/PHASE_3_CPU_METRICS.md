# Phase 3: CPU Performance Metrics Layout

**Objectives:**
- Pair related CPU metrics (Score with $/Mark)
- Display base and adjusted values side-by-side
- Add color coding based on thresholds
- Add tooltips for adjusted values

**Prerequisites:**
- UX-002 completed (ValuationTooltip component)

**Estimated Duration:** 5-6 days

---

## METRICS-001: Create CPU Mark Thresholds Setting

**Type:** Backend
**Priority:** P0-Critical
**Effort:** 4 hours
**Dependencies:** None

**Acceptance Criteria:**
- [ ] Database migration adds default thresholds
- [ ] API endpoint returns thresholds
- [ ] Settings service manages thresholds

**Implementation Steps:**

1. **Create migration** (`apps/api/alembic/versions/xxx_add_cpu_mark_thresholds.py`):

```python
"""Add CPU mark thresholds to application settings

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-31
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.execute("""
        INSERT INTO application_settings (key, value, description, created_at, updated_at)
        VALUES (
            'cpu_mark_thresholds',
            '{"excellent": 20.0, "good": 10.0, "fair": 5.0, "neutral": 0.0, "poor": -10.0, "premium": -20.0}'::jsonb,
            'Thresholds for color-coding CPU performance metrics (percentage improvement)',
            NOW(),
            NOW()
        )
        ON CONFLICT (key) DO NOTHING;
    """)

def downgrade():
    op.execute("""
        DELETE FROM application_settings WHERE key = 'cpu_mark_thresholds';
    """)
```

2. **Add API endpoint** (`apps/api/dealbrain_api/api/settings.py`):

```python
@router.get("/settings/cpu_mark_thresholds", response_model=CpuMarkThresholds)
async def get_cpu_mark_thresholds(
    session: AsyncSession = Depends(get_session),
):
    """Get CPU Mark color-coding thresholds."""
    thresholds = await settings_service.get_cpu_mark_thresholds(session)
    return thresholds
```

3. **Add service method** (`apps/api/dealbrain_api/services/settings.py`):

```python
async def get_cpu_mark_thresholds(self, session: AsyncSession) -> dict:
    """Get CPU Mark thresholds from settings."""
    setting = await self.get_setting(session, "cpu_mark_thresholds")
    if not setting:
        return {
            "excellent": 20.0,
            "good": 10.0,
            "fair": 5.0,
            "neutral": 0.0,
            "poor": -10.0,
            "premium": -20.0,
        }
    return setting
```

4. **Add schema** (`apps/api/dealbrain_api/schemas/settings.py`):

```python
from pydantic import BaseModel

class CpuMarkThresholds(BaseModel):
    excellent: float
    good: float
    fair: float
    neutral: float
    poor: float
    premium: float
```

**Testing Requirements:**
- [ ] Unit test: Migration runs successfully
- [ ] Unit test: Endpoint returns default thresholds
- [ ] Integration test: Thresholds persist in database

---

## METRICS-002: Create Performance Metric Display Component

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 12 hours
**Dependencies:** METRICS-001, UX-002

**Acceptance Criteria:**
- [ ] Component displays base and adjusted values
- [ ] Color coding based on improvement percentage
- [ ] Tooltip explains calculation
- [ ] Responsive layout

**Implementation Steps:**

1. **Create component** (`apps/web/components/listings/performance-metric-display.tsx`):

```typescript
import { useCpuMarkThresholds } from '@/hooks/use-cpu-mark-thresholds';
import { ValuationTooltip } from './valuation-tooltip';
import { formatCurrency } from '@/lib/utils';

interface PerformanceMetricDisplayProps {
  label: string;
  score?: number;
  baseValue?: number;
  adjustedValue?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  showColorCoding?: boolean;
  listPrice?: number;
  adjustedPrice?: number;
  cpuMark?: number;
}

export function PerformanceMetricDisplay({
  label,
  score,
  baseValue,
  adjustedValue,
  prefix = '$',
  decimals = 3,
  showColorCoding = false,
  listPrice,
  adjustedPrice,
  cpuMark,
}: PerformanceMetricDisplayProps) {
  const { data: thresholds } = useCpuMarkThresholds();

  const improvement = useMemo(() => {
    if (!baseValue || !adjustedValue) return 0;
    return ((baseValue - adjustedValue) / baseValue) * 100;
  }, [baseValue, adjustedValue]);

  const colorStyle = useMemo(() => {
    if (!showColorCoding || !thresholds) return null;
    return getCpuMarkColorStyle(improvement, thresholds);
  }, [improvement, showColorCoding, thresholds]);

  return (
    <div className="space-y-1">
      <dt className="text-sm font-medium text-muted-foreground">{label}</dt>
      <dd className="flex items-baseline gap-2">
        {score !== undefined && (
          <span className="text-lg font-semibold">{score.toLocaleString()}</span>
        )}
        {baseValue !== undefined && adjustedValue !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {prefix}{baseValue.toFixed(decimals)}
            </span>
            <span className="text-muted-foreground">→</span>
            <div className="flex items-center gap-1">
              <span
                className={cn(
                  'text-sm font-semibold',
                  colorStyle && `text-[${colorStyle.fg}] bg-[${colorStyle.bg}] px-2 py-0.5 rounded`
                )}
              >
                {prefix}{adjustedValue.toFixed(decimals)}
              </span>
              {improvement !== 0 && (
                <span className={cn(
                  'text-xs',
                  improvement > 0 ? 'text-green-600' : 'text-red-600'
                )}>
                  ({improvement > 0 ? '↓' : '↑'}{Math.abs(improvement).toFixed(1)}%)
                </span>
              )}
              <ValuationTooltip
                listPrice={listPrice || 0}
                adjustedValue={adjustedPrice || 0}
                valuationBreakdown={{
                  listing_price: listPrice,
                  adjusted_price: adjustedPrice,
                  cpu_mark: cpuMark,
                  base_metric: baseValue,
                  adjusted_metric: adjustedValue,
                }}
              />
            </div>
          </div>
        )}
      </dd>
    </div>
  );
}
```

2. **Add color utility** (`apps/web/lib/cpu-mark-utils.ts`):

```typescript
export function getCpuMarkColorStyle(improvement: number, thresholds: CpuMarkThresholds) {
  if (improvement >= thresholds.excellent) {
    return { bg: 'hsl(var(--cpu-mark-excellent-bg))', fg: 'hsl(var(--cpu-mark-excellent-fg))' };
  } else if (improvement >= thresholds.good) {
    return { bg: 'hsl(var(--cpu-mark-good-bg))', fg: 'hsl(var(--cpu-mark-good-fg))' };
  } else if (improvement >= thresholds.fair) {
    return { bg: 'hsl(var(--cpu-mark-fair-bg))', fg: 'hsl(var(--cpu-mark-fair-fg))' };
  } else if (improvement >= thresholds.neutral) {
    return { bg: 'hsl(var(--cpu-mark-neutral-bg))', fg: 'hsl(var(--cpu-mark-neutral-fg))' };
  } else if (improvement >= thresholds.poor) {
    return { bg: 'hsl(var(--cpu-mark-poor-bg))', fg: 'hsl(var(--cpu-mark-poor-fg))' };
  } else {
    return { bg: 'hsl(var(--cpu-mark-premium-bg))', fg: 'hsl(var(--cpu-mark-premium-fg))' };
  }
}
```

3. **Add CSS variables** (`apps/web/styles/globals.css`):

```css
:root {
  --cpu-mark-excellent-bg: 142 71% 25%;
  --cpu-mark-excellent-fg: 0 0% 100%;
  --cpu-mark-good-bg: 142 71% 45%;
  --cpu-mark-good-fg: 142 71% 15%;
  --cpu-mark-fair-bg: 142 71% 85%;
  --cpu-mark-fair-fg: 142 71% 25%;
  --cpu-mark-neutral-bg: 0 0% 90%;
  --cpu-mark-neutral-fg: 0 0% 20%;
  --cpu-mark-poor-bg: 0 84% 85%;
  --cpu-mark-poor-fg: 0 84% 25%;
  --cpu-mark-premium-bg: 0 84% 40%;
  --cpu-mark-premium-fg: 0 0% 100%;
}
```

**Testing Requirements:**
- [ ] Unit test: Color selection based on improvement
- [ ] Unit test: Percentage calculation
- [ ] Visual test: Color coding matches design
- [ ] A11y test: Contrast ratios meet WCAG AA

---

## METRICS-003: Update Specifications Tab Layout

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 8 hours
**Dependencies:** METRICS-002

**Acceptance Criteria:**
- [ ] CPU metrics paired (Score next to $/Mark)
- [ ] Both single-thread and multi-thread shown
- [ ] Layout responsive (mobile stacks vertically)

**Implementation Steps:**

1. **Update SpecificationsTab** (`apps/web/components/listings/specifications-tab.tsx`):

```typescript
import { PerformanceMetricDisplay } from './performance-metric-display';

export function SpecificationsTab({ listing }: SpecificationsTabProps) {
  // Calculate base $/CPU Mark values
  const baseSingleThreadMark = listing.price_usd / (listing.cpu?.cpu_mark_single || 1);
  const baseMultiThreadMark = listing.price_usd / (listing.cpu?.cpu_mark_multi || 1);

  const adjustedSingleThreadMark = listing.adjusted_price_usd / (listing.cpu?.cpu_mark_single || 1);
  const adjustedMultiThreadMark = listing.adjusted_price_usd / (listing.cpu?.cpu_mark_multi || 1);

  return (
    <div className="space-y-6">
      {/* Compute Section */}
      <Card>
        <CardHeader>
          <CardTitle>Compute</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* CPU */}
          <dl className="grid grid-cols-1 gap-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">CPU</dt>
              <dd>{listing.cpu?.name || 'Not specified'}</dd>
            </div>
            {listing.gpu && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">GPU</dt>
                <dd>{listing.gpu.name}</dd>
              </div>
            )}
          </dl>

          {/* Performance Metrics - Paired Layout */}
          <div className="border-t pt-4 space-y-3">
            <h4 className="text-sm font-semibold">Performance Metrics</h4>

            {/* Single-Thread */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-3 bg-muted/50 rounded-lg">
              <PerformanceMetricDisplay
                label="Single-Thread Score"
                score={listing.cpu?.cpu_mark_single}
              />
              <PerformanceMetricDisplay
                label="$/Single-Thread Mark"
                baseValue={baseSingleThreadMark}
                adjustedValue={adjustedSingleThreadMark}
                showColorCoding
                listPrice={listing.price_usd}
                adjustedPrice={listing.adjusted_price_usd}
                cpuMark={listing.cpu?.cpu_mark_single}
              />
            </div>

            {/* Multi-Thread */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-3 bg-muted/50 rounded-lg">
              <PerformanceMetricDisplay
                label="Multi-Thread Score"
                score={listing.cpu?.cpu_mark_multi}
              />
              <PerformanceMetricDisplay
                label="$/Multi-Thread Mark"
                baseValue={baseMultiThreadMark}
                adjustedValue={adjustedMultiThreadMark}
                showColorCoding
                listPrice={listing.price_usd}
                adjustedPrice={listing.adjusted_price_usd}
                cpuMark={listing.cpu?.cpu_mark_multi}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Other sections... */}
    </div>
  );
}
```

**Testing Requirements:**
- [ ] E2E test: Metrics display correctly
- [ ] E2E test: Responsive layout on mobile
- [ ] Visual test: Pairing is clear and readable

---

**Phase 3 Summary:**

| Task | Type | Effort | Status |
|------|------|--------|--------|
| METRICS-001 | Backend | 4h | Pending |
| METRICS-002 | Frontend | 12h | Pending |
| METRICS-003 | Frontend | 8h | Pending |
| Testing | All | 12h | Pending |
| **Total** | | **44h** | |
