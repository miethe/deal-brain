# ADR-006: CPU Performance Metrics Threshold System

## Status
Accepted

## Context

Phase 3 of the Listings Enhancements v3 project introduces color-coded CPU performance metrics ($/CPU Mark) to help users quickly assess value efficiency when evaluating PC listings. Users need an intuitive way to understand if they're getting good value based on performance metrics.

The system needs to:
1. Display both single-thread and multi-thread CPU Mark efficiency metrics
2. Show base and adjusted values (reflecting valuation adjustments)
3. Provide visual indicators (color coding) for value assessment
4. Be configurable for different market conditions
5. Maintain consistency with existing valuation threshold patterns

## Decision

### 1. Threshold Structure

Store CPU Mark thresholds in the existing `ApplicationSettings` table with key `cpu_mark_thresholds`:

```json
{
  "excellent": 20.0,
  "good": 10.0,
  "fair": 5.0,
  "neutral": 0.0,
  "poor": -10.0,
  "premium": -20.0
}
```

**Values represent percentage improvement** from base to adjusted $/CPU Mark:
- **Excellent** (≥20% improvement): Best value, significant savings
- **Good** (10-20% improvement): Good value, moderate savings
- **Fair** (5-10% improvement): Fair value, modest savings
- **Neutral** (0-5% improvement): Neutral, minimal change
- **Poor** (-10-0% degradation): Poor value, minimal degradation
- **Premium** (<-10% degradation): Premium priced, significant degradation

**Rationale**: Percentage-based thresholds adapt to different price ranges and CPU mark values, providing consistent value assessment across all listing types.

### 2. Display Layout

**Desktop (≥768px)**:
- 2-column grid layout
- Left column: CPU Mark Score
- Right column: $/CPU Mark (base → adjusted with color coding)

**Mobile (<768px)**:
- Stacked vertical layout
- Score above $/Mark metrics
- Full width for readability

**Both layouts show**:
```
Single-Thread Score: 3,500
$/Single-Thread Mark: $0.0040 → $0.0028 (↓30%, Excellent)

Multi-Thread Score: 25,000
$/Multi-Thread Mark: $0.0050 → $0.0035 (↓30%, Excellent)
```

**Rationale**: Side-by-side pairing creates visual association between score and efficiency. Showing delta percentage makes improvement immediately clear.

### 3. Color Coding System

CSS variables enable theme-aware color coding:

| Threshold | Background | Foreground | Use Case |
|-----------|------------|------------|----------|
| Excellent | `--cpu-mark-excellent-bg` (dark green) | `--cpu-mark-excellent-fg` (white) | ≥20% improvement |
| Good | `--cpu-mark-good-bg` (medium green) | `--cpu-mark-good-fg` (dark green) | 10-20% improvement |
| Fair | `--cpu-mark-fair-bg` (light green) | `--cpu-mark-fair-fg` (dark green) | 5-10% improvement |
| Neutral | `--cpu-mark-neutral-bg` (gray) | `--cpu-mark-neutral-fg` (dark gray) | 0-5% change |
| Poor | `--cpu-mark-poor-bg` (light red) | `--cpu-mark-poor-fg` (dark red) | -10-0% degradation |
| Premium | `--cpu-mark-premium-bg` (dark red) | `--cpu-mark-premium-fg` (white) | <-10% degradation |

**Accessibility Requirements**:
- All color combinations meet WCAG 2.1 AA contrast ratio (4.5:1)
- Color is supplemented with text labels ("Excellent", "Good", etc.)
- Delta indicators use both color and symbols (↓/↑)
- Screen reader labels provide full context

**Rationale**: CSS variables enable dark mode support and theme customization. Multi-signal approach (color + text + symbols) ensures accessibility.

### 4. Storage and API Pattern

**Reuse existing infrastructure**:
- Table: `ApplicationSettings` (already exists)
- Service: `SettingsService.get_cpu_mark_thresholds()` (new method)
- Endpoint: `GET /settings/cpu_mark_thresholds` (uses existing `/settings/{key}` pattern)
- Schema: `CpuMarkThresholdsResponse` (Pydantic model)

**Seed defaults on first run**:
```python
# apps/api/dealbrain_api/seeds/cpu_mark_thresholds_seed.py
DEFAULT_CPU_MARK_THRESHOLDS = {
    "excellent": 20.0,
    "good": 10.0,
    "fair": 5.0,
    "neutral": 0.0,
    "poor": -10.0,
    "premium": -20.0
}
```

**No database migration required**: ApplicationSettings table already supports JSONB values.

**Rationale**: Consistency with valuation thresholds pattern. Minimal new infrastructure. Easy to modify without schema changes.

### 5. Component Architecture

**Follow ValuationTooltip pattern**:

```
PerformanceMetricDisplay component
├── Props: label, score, baseValue, adjustedValue, showColorCoding
├── Hook: useCpuMarkThresholds() (React Query)
├── Utilities: cpu-mark-utils.ts
│   ├── getCpuMarkStyle(improvement, thresholds) → color class
│   ├── calculateImprovement(base, adjusted) → percentage
│   └── formatCpuMark(value) → formatted string
└── Memoization: React.memo() + useMemo() for calculations
```

**Performance optimization**:
- Memoize component with `React.memo()`
- Use `useMemo()` for threshold calculations
- Cache threshold API response for 5 minutes

**Rationale**: Proven pattern from Phase 2. Consistent developer experience. Performance-optimized for table rendering.

## Consequences

### Positive

1. **Consistency**: Follows established valuation threshold pattern
2. **Flexibility**: Thresholds configurable via ApplicationSettings
3. **Performance**: Memoization prevents unnecessary re-renders
4. **Accessibility**: Multi-signal approach (color + text + icons) ensures WCAG 2.1 AA compliance
5. **Maintainability**: Reuses existing infrastructure, no new migrations
6. **Theme Support**: CSS variables enable dark mode and customization
7. **User Experience**: Visual indicators make value assessment intuitive

### Negative

1. **Threshold Tuning**: May require market analysis to validate default values
2. **Color Proliferation**: 6 color levels may be overwhelming (could simplify to 3-4)
3. **Desktop Real Estate**: Side-by-side layout uses more horizontal space
4. **Threshold Complexity**: Percentage-based thresholds may be less intuitive than absolute $/mark values

### Mitigation Strategies

1. **Threshold Validation**: Monitor user feedback and adjust defaults based on real market data
2. **Color Simplification**: Future iteration could consolidate to 4 levels (excellent, good, neutral, poor)
3. **Responsive Design**: Mobile stacked layout addresses space concerns on small screens
4. **User Education**: Tooltips explain calculation methodology and threshold meanings

## Alternatives Considered

### Alternative 1: Absolute $/Mark Thresholds

```json
{
  "excellent": 0.002,
  "good": 0.004,
  "fair": 0.006,
  "poor": 0.008
}
```

**Rejected because**:
- Doesn't adapt to different price ranges (high-end vs budget PCs)
- Requires manual adjustment as market changes
- Less intuitive for users (what does $0.004/mark mean?)

### Alternative 2: Database Table for Thresholds

Create dedicated `cpu_mark_thresholds` table.

**Rejected because**:
- ApplicationSettings already supports JSONB
- Adds unnecessary complexity
- Inconsistent with valuation thresholds pattern
- Requires migration and additional service code

### Alternative 3: Show Only Adjusted Value

Hide base value, show only adjusted $/Mark with tooltip for base.

**Rejected because**:
- Users lose context of actual improvement
- Delta percentage is key value indicator
- Transparency important for trust

### Alternative 4: 3-Color System

Simplify to just: Good (green), Neutral (gray), Poor (red)

**Partially adopted**: We use 6 levels but could consolidate in future based on user feedback. Current approach provides more granularity for initial launch.

## References

- **Phase 3 Plan**: `docs/project_plans/listings-enhancements-v3/PHASE_3_CPU_METRICS.md`
- **Valuation Thresholds Pattern**: `apps/api/dealbrain_api/services/settings.py` (existing)
- **ValuationTooltip Component**: `apps/web/components/listings/valuation-tooltip.tsx` (reference)
- **WCAG 2.1 AA Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/
- **CPU Mark Data**: `apps/api/dealbrain_api/models/core.py` (Listing model fields)

## Implementation Tasks

1. ✅ ADR approved and documented
2. ⏳ METRICS-001: Backend threshold management (python-backend-engineer)
3. ⏳ METRICS-002: PerformanceMetricDisplay component (ui-engineer)
4. ⏳ METRICS-003: Specifications tab integration (ui-engineer)
5. ⏳ Testing and validation
6. ⏳ Documentation

## Approval

- **Architect**: Approved (2025-11-01)
- **Product Owner**: (Pending)
- **Engineering Lead**: (Pending)

---

**Note**: This ADR can be amended based on user feedback and market data analysis after initial launch.
