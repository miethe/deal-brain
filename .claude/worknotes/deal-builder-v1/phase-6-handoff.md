# Phase 6 Handoff: Real-time Calculations & Valuation Panel

**Previous Phase**: Phase 5 (Frontend Component Structure) - COMPLETE ✅
**Current Phase**: Phase 6 (Real-time Calculations & Valuation Panel)

---

## What's Already Built (Phase 5)

### Component Structure
- ✅ BuilderProvider with React Context
- ✅ ComponentBuilder main layout
- ✅ ComponentCard for each component type
- ✅ ComponentSelectorModal for selection
- ✅ Builder page route at `/builder`
- ✅ API client functions in `lib/api/builder.ts`

### State Management
- ✅ React Context with useReducer
- ✅ Component selection state
- ✅ Placeholder for valuation/metrics
- ✅ Error handling structure

### Mock Data
- ✅ Mock components for all 6 types (CPU, GPU, RAM, Storage, PSU, Case)
- ✅ Search and filtering working locally
- ✅ Component selection flow working

---

## Phase 6 Requirements

### 1. Real Component Catalog Integration

**Replace Mock Data with API Calls:**

```typescript
// Current (Phase 5): Mock data in component-builder.tsx
const mockComponents = { cpu_id: [...], gpu_id: [...] }

// Phase 6: Fetch from catalog APIs
useQuery({
  queryKey: ['cpus'],
  queryFn: () => apiFetch<CPU[]>('/v1/catalog/cpus'),
  staleTime: 5 * 60 * 1000, // 5 minutes
})
```

**Catalog Endpoints to Use:**
- `/v1/catalog/cpus` - CPU list
- `/v1/catalog/gpus` - GPU list
- Other component types TBD (RAM, Storage, PSU, Case specs)

**Data Transformation:**
```typescript
// Transform API response to ComponentItem interface
const transformCPU = (cpu: CpuResponse): ComponentItem => ({
  id: cpu.id,
  name: cpu.name,
  manufacturer: cpu.manufacturer,
  specs: `${cpu.cpu_mark_multi} PassMark, ${cpu.tdp_w}W TDP`,
  price: undefined, // Estimated in calculation
})
```

### 2. Real-time Calculations Hook

**Create: `apps/web/hooks/use-builder-calculations.ts`**

```typescript
import { useMutation } from '@tanstack/react-query';
import { useBuilder } from '@/components/builder';
import { calculateBuild } from '@/lib/api/builder';
import { useDebounce } from '@/hooks/use-debounce'; // Create if needed

export function useBuilderCalculations() {
  const { state, dispatch } = useBuilder();

  // Debounce component changes by 300ms
  const debouncedComponents = useDebounce(state.components, 300);

  const mutation = useMutation({
    mutationFn: calculateBuild,
    onMutate: () => {
      dispatch({ type: 'SET_CALCULATING', payload: true });
    },
    onSuccess: (data) => {
      dispatch({
        type: 'SET_CALCULATIONS',
        payload: {
          valuation: data.valuation,
          metrics: data.metrics,
        },
      });
    },
    onError: (error) => {
      dispatch({
        type: 'SET_ERROR',
        payload: error.message || 'Calculation failed',
      });
    },
  });

  // Trigger calculation when components change (debounced)
  useEffect(() => {
    if (debouncedComponents.cpu_id) {
      mutation.mutate({
        cpu_id: debouncedComponents.cpu_id,
        gpu_id: debouncedComponents.gpu_id,
        ram_spec_id: debouncedComponents.ram_spec_id,
        storage_spec_id: debouncedComponents.storage_spec_id,
        psu_spec_id: debouncedComponents.psu_spec_id,
        case_spec_id: debouncedComponents.case_spec_id,
      });
    }
  }, [debouncedComponents]);

  return {
    isCalculating: state.isCalculating,
    valuation: state.valuation,
    metrics: state.metrics,
    error: state.error,
    recalculate: () => mutation.mutate(state.components),
  };
}
```

**Debounce Utility (if not exists):**
```typescript
// apps/web/hooks/use-debounce.ts
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}
```

### 3. ValuationPanel Component

**Create: `apps/web/components/builder/valuation-panel.tsx`**

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DealMeter } from './deal-meter';
import { PerformanceMetrics } from './performance-metrics';
import { useBuilderCalculations } from '@/hooks/use-builder-calculations';
import { Loader2 } from 'lucide-react';

export function ValuationPanel() {
  const { isCalculating, valuation, metrics, error } = useBuilderCalculations();

  if (!valuation) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Valuation Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            Select a CPU to begin calculating pricing
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Valuation Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isCalculating && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Calculating...
          </div>
        )}

        {error && (
          <div className="text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Base Price */}
        <div>
          <p className="text-sm text-muted-foreground">Base Price</p>
          <p className="text-2xl font-bold">
            ${valuation.base_price.toFixed(2)}
          </p>
        </div>

        {/* Adjusted Price */}
        <div>
          <p className="text-sm text-muted-foreground">Adjusted Price</p>
          <p className="text-2xl font-bold">
            ${valuation.adjusted_price.toFixed(2)}
          </p>
          {valuation.delta_percentage !== 0 && (
            <p className={`text-sm ${
              valuation.delta_percentage > 0 ? 'text-red-500' : 'text-green-500'
            }`}>
              {valuation.delta_percentage > 0 ? '+' : ''}
              {valuation.delta_percentage.toFixed(1)}%
              (${Math.abs(valuation.delta_amount).toFixed(2)})
            </p>
          )}
        </div>

        {/* Deal Meter */}
        <DealMeter valuation={valuation} />

        {/* Performance Metrics */}
        {metrics && <PerformanceMetrics metrics={metrics} />}

        {/* Actions */}
        <div className="space-y-2">
          <Button className="w-full">
            Save Build
          </Button>
          <Button variant="outline" className="w-full">
            View Breakdown
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

### 4. DealMeter Component

**Create: `apps/web/components/builder/deal-meter.tsx`**

```typescript
import { cn } from '@/lib/utils';
import type { ValuationBreakdown } from '@/lib/api/builder';

interface DealMeterProps {
  valuation: ValuationBreakdown;
}

export function DealMeter({ valuation }: DealMeterProps) {
  const getDealLevel = () => {
    const delta = valuation.delta_percentage;
    if (delta >= 10) return { level: 'premium', color: 'red', label: 'Premium Price' };
    if (delta >= 5) return { level: 'fair', color: 'yellow', label: 'Fair Price' };
    if (delta >= -5) return { level: 'good', color: 'green', label: 'Good Deal' };
    return { level: 'great', color: 'green', label: 'Great Deal' };
  };

  const deal = getDealLevel();

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Deal Rating</p>
      <div className="flex items-center gap-2">
        <div className={cn(
          'flex-1 h-2 rounded-full',
          deal.color === 'red' && 'bg-red-500',
          deal.color === 'yellow' && 'bg-yellow-500',
          deal.color === 'green' && 'bg-green-500',
        )} />
        <span className={cn(
          'text-sm font-medium',
          deal.color === 'red' && 'text-red-500',
          deal.color === 'yellow' && 'text-yellow-500',
          deal.color === 'green' && 'text-green-500',
        )}>
          {deal.label}
        </span>
      </div>
    </div>
  );
}
```

### 5. PerformanceMetrics Component

**Create: `apps/web/components/builder/performance-metrics.tsx`**

```typescript
import type { BuildMetrics } from '@/lib/api/builder';

interface PerformanceMetricsProps {
  metrics: BuildMetrics;
}

export function PerformanceMetrics({ metrics }: PerformanceMetricsProps) {
  const formatMetric = (value: number | null) => {
    if (value === null) return 'N/A';
    return `$${value.toFixed(3)}`;
  };

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">Performance Metrics</p>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <p className="text-muted-foreground">$/CPU Mark (Multi)</p>
          <p className="font-medium">{formatMetric(metrics.dollar_per_cpu_mark_multi)}</p>
        </div>

        <div>
          <p className="text-muted-foreground">$/CPU Mark (Single)</p>
          <p className="font-medium">{formatMetric(metrics.dollar_per_cpu_mark_single)}</p>
        </div>
      </div>

      {metrics.composite_score && (
        <div>
          <p className="text-muted-foreground">Composite Score</p>
          <p className="text-lg font-bold">{metrics.composite_score}</p>
        </div>
      )}
    </div>
  );
}
```

### 6. Update ComponentBuilder

**Modify: `apps/web/components/builder/component-builder.tsx`**

Remove mock data and replace with React Query:

```typescript
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/lib/utils';

// Inside ComponentBuilder component:
const { data: cpus = [] } = useQuery({
  queryKey: ['cpus'],
  queryFn: () => apiFetch<CpuResponse[]>('/v1/catalog/cpus'),
  staleTime: 5 * 60 * 1000,
});

const { data: gpus = [] } = useQuery({
  queryKey: ['gpus'],
  queryFn: () => apiFetch<GpuResponse[]>('/v1/catalog/gpus'),
  staleTime: 5 * 60 * 1000,
});

// Transform to ComponentItem format
const componentCatalog: Record<string, ComponentItem[]> = {
  cpu_id: cpus.map(transformCPU),
  gpu_id: gpus.map(transformGPU),
  // ... other types
};
```

### 7. Update Builder Page

**Modify: `apps/web/app/builder/page.tsx`**

Replace placeholder with ValuationPanel:

```typescript
import { ValuationPanel } from '@/components/builder/valuation-panel';

// In JSX:
<div className="lg:col-span-1">
  <div className="lg:sticky lg:top-6">
    <ValuationPanel />
  </div>
</div>
```

---

## Testing Checklist

### Manual Testing
- [ ] Component catalog loads from API
- [ ] CPU selection triggers calculation
- [ ] Debouncing works (300ms delay)
- [ ] Valuation displays correctly
- [ ] Metrics display correctly
- [ ] DealMeter shows correct color
- [ ] Loading states work
- [ ] Error states work
- [ ] Mobile layout responsive
- [ ] Desktop sticky panel works

### Integration Testing
- [ ] Calculation API integration
- [ ] Catalog API integration
- [ ] State updates correctly
- [ ] Error handling works
- [ ] Network errors handled

---

## Performance Targets

- Initial page load: <2s
- Component catalog load: <500ms
- Calculation response: <300ms
- Debounce delay: 300ms
- Re-render optimization: Memoization where needed

---

## Known Limitations to Address

1. Mock component catalog for RAM, Storage, PSU, Case (APIs don't exist yet)
2. No save functionality (Phase 7)
3. No breakdown modal (Phase 7)
4. No build comparison (Phase 7)
5. No authentication (future enhancement)

---

## Files to Create (Phase 6)

1. `apps/web/hooks/use-builder-calculations.ts`
2. `apps/web/hooks/use-debounce.ts` (if not exists)
3. `apps/web/components/builder/valuation-panel.tsx`
4. `apps/web/components/builder/deal-meter.tsx`
5. `apps/web/components/builder/performance-metrics.tsx`

## Files to Modify (Phase 6)

1. `apps/web/components/builder/component-builder.tsx` - Replace mock data
2. `apps/web/app/builder/page.tsx` - Add ValuationPanel
3. `apps/web/components/builder/index.ts` - Export new components

---

## Success Criteria

Phase 6 is complete when:
- [ ] Real-time calculations working
- [ ] Debouncing implemented (300ms)
- [ ] ValuationPanel displays pricing
- [ ] DealMeter shows color-coded rating
- [ ] PerformanceMetrics displays CPU metrics
- [ ] Component catalog loads from APIs
- [ ] Loading states implemented
- [ ] Error handling implemented
- [ ] Mobile responsive
- [ ] Performance targets met

---

## Next Phase (Phase 7)

Phase 7 will add:
- Save build functionality
- Valuation breakdown modal
- Build list view
- Build comparison
- Share functionality
