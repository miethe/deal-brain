# Deal Builder Implementation Guide

## Overview

This guide translates the UX/UI specification into actionable technical implementation steps, leveraging your existing Deal Brain architecture.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  /builder/page.tsx (Main Builder)                          │
│  ├─ BuilderProvider (React Context)                        │
│  ├─ ComponentBuilder (Left Panel)                          │
│  │  ├─ ComponentCard (Repeatable)                          │
│  │  │  └─ ComponentSelector (Modal)                        │
│  │  └─ SavedBuildsSection                                  │
│  └─ ValuationPanel (Right Panel - Sticky)                  │
│     ├─ PriceDisplay                                        │
│     ├─ DealMeter                                           │
│     ├─ PerformanceMetrics                                  │
│     └─ ValuationBreakdown                                  │
│                                                             │
│  /builder/shared/[id]/page.tsx (Shared View)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ React Query
                              ├─ POST /v1/builder/calculate
                              ├─ POST /v1/builder/builds
                              └─ GET  /v1/builder/builds
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  apps/api/dealbrain_api/api/builder.py                     │
│  ├─ POST /v1/builder/calculate                             │
│  ├─ POST /v1/builder/builds                                │
│  ├─ GET  /v1/builder/builds                                │
│  ├─ GET  /v1/builder/builds/{id}                           │
│  └─ GET  /v1/builder/compare                               │
│                                                             │
│  apps/api/dealbrain_api/services/builder.py                │
│  ├─ calculate_build_valuation()                            │
│  ├─ calculate_build_metrics()                              │
│  ├─ save_build()                                           │
│  ├─ get_user_builds()                                      │
│  └─ compare_build_to_listings()                            │
│                                                             │
│  apps/api/dealbrain_api/models/core.py                     │
│  └─ SavedBuild (new table)                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Uses existing
                              ├─ valuation.py (core logic)
                              ├─ scoring.py (metrics)
                              └─ services/listings.py
```

## Database Schema

### New Table: `saved_builds`

```sql
CREATE TABLE saved_builds (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NULL,              -- Future: auth integration
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    tags TEXT[] DEFAULT '{}',
    visibility VARCHAR(20) DEFAULT 'private', -- 'private', 'public', 'unlisted'
    share_token VARCHAR(64) UNIQUE NOT NULL, -- For shareable URLs

    -- Component references (matches listing structure)
    cpu_id INTEGER REFERENCES cpus(id),
    gpu_id INTEGER REFERENCES gpus(id),
    ram_spec_id INTEGER REFERENCES ram_specs(id),
    primary_storage_profile_id INTEGER REFERENCES storage_profiles(id),
    secondary_storage_profile_id INTEGER REFERENCES storage_profiles(id),
    ports_profile_id INTEGER REFERENCES ports_profiles(id),

    -- Simplified storage for other components (JSON)
    other_components JSONB DEFAULT '{}',

    -- Pricing snapshot
    base_price_usd DECIMAL(10, 2) NOT NULL,
    adjusted_price_usd DECIMAL(10, 2) NOT NULL,
    component_prices JSONB DEFAULT '{}',     -- {"cpu": 189.00, "ram": 45.00, ...}

    -- Performance metrics snapshot
    dollar_per_cpu_mark_multi DECIMAL(10, 3),
    dollar_per_cpu_mark_single DECIMAL(10, 3),
    composite_score DECIMAL(5, 2),

    -- Valuation breakdown (full JSON)
    valuation_breakdown JSONB NOT NULL,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP NULL,

    -- Indexes
    INDEX idx_user_builds (user_id, deleted_at),
    INDEX idx_share_token (share_token),
    INDEX idx_visibility (visibility, deleted_at)
);

-- Alembic migration
-- File: apps/api/alembic/versions/XXXX_add_saved_builds_table.py
```

## Frontend Implementation

### Phase 1: Core Structure (Days 1-2)

#### 1.1 Page Route & Layout

**File**: `/apps/web/app/builder/page.tsx`

```typescript
import { BuilderProvider } from '@/components/builder/builder-provider';
import { ComponentBuilder } from '@/components/builder/component-builder';
import { ValuationPanel } from '@/components/builder/valuation-panel';
import { SavedBuildsSection } from '@/components/builder/saved-builds-section';

export default function BuilderPage() {
  return (
    <BuilderProvider>
      <div className="container mx-auto py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight">Build & Price</h1>
          <p className="text-muted-foreground">
            Create custom PC builds with real-time valuation and performance metrics
          </p>
        </div>

        {/* Main Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Component Builder */}
          <div className="lg:col-span-7">
            <ComponentBuilder />
          </div>

          {/* Right: Valuation Panel (Sticky) */}
          <div className="lg:col-span-5">
            <div className="lg:sticky lg:top-20">
              <ValuationPanel />
            </div>
          </div>
        </div>

        {/* Saved Builds */}
        <div className="mt-12">
          <SavedBuildsSection />
        </div>
      </div>
    </BuilderProvider>
  );
}
```

#### 1.2 State Management (React Context)

**File**: `/apps/web/components/builder/builder-provider.tsx`

```typescript
'use client';

import { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiFetch } from '@/lib/utils';
import { calculateBuildValuation } from '@/lib/builder-utils';

interface BuilderState {
  components: {
    cpu_id?: number;
    gpu_id?: number;
    ram_spec_id?: number;
    primary_storage_profile_id?: number;
    secondary_storage_profile_id?: number;
  };
  pricing: {
    base_price: number;
    adjusted_price: number;
    component_prices: Record<string, number>;
  };
  metrics: {
    dollar_per_cpu_mark_multi?: number;
    dollar_per_cpu_mark_single?: number;
    composite_score?: number;
  };
  valuation_breakdown?: any;
  isCalculating: boolean;
  editingBuildId?: number;
}

type BuilderAction =
  | { type: 'SET_COMPONENT'; componentType: string; componentId: number | null }
  | { type: 'REMOVE_COMPONENT'; componentType: string }
  | { type: 'SET_CALCULATION_RESULT'; payload: any }
  | { type: 'SET_CALCULATING'; isCalculating: boolean }
  | { type: 'LOAD_BUILD'; build: any }
  | { type: 'RESET' };

const initialState: BuilderState = {
  components: {},
  pricing: {
    base_price: 0,
    adjusted_price: 0,
    component_prices: {},
  },
  metrics: {},
  isCalculating: false,
};

const BuilderContext = createContext<{
  state: BuilderState;
  dispatch: React.Dispatch<BuilderAction>;
  selectComponent: (type: string, id: number) => void;
  removeComponent: (type: string) => void;
  loadBuild: (buildId: number) => void;
  resetBuild: () => void;
} | null>(null);

function builderReducer(state: BuilderState, action: BuilderAction): BuilderState {
  switch (action.type) {
    case 'SET_COMPONENT':
      return {
        ...state,
        components: {
          ...state.components,
          [action.componentType]: action.componentId,
        },
      };
    case 'REMOVE_COMPONENT':
      const { [action.componentType]: _, ...rest } = state.components;
      return {
        ...state,
        components: rest,
      };
    case 'SET_CALCULATION_RESULT':
      return {
        ...state,
        pricing: action.payload.pricing,
        metrics: action.payload.metrics,
        valuation_breakdown: action.payload.valuation_breakdown,
        isCalculating: false,
      };
    case 'SET_CALCULATING':
      return {
        ...state,
        isCalculating: action.isCalculating,
      };
    case 'LOAD_BUILD':
      return {
        ...state,
        components: action.build.components,
        pricing: action.build.pricing,
        metrics: action.build.metrics,
        valuation_breakdown: action.build.valuation_breakdown,
        editingBuildId: action.build.id,
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

export function BuilderProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(builderReducer, initialState);

  // Mutation for calculating build valuation
  const calculateMutation = useMutation({
    mutationFn: async (components: any) => {
      return apiFetch('/v1/builder/calculate', {
        method: 'POST',
        body: JSON.stringify({ components }),
      });
    },
    onSuccess: (data) => {
      dispatch({ type: 'SET_CALCULATION_RESULT', payload: data });
    },
  });

  // Trigger calculation when components change (debounced)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (Object.keys(state.components).length > 0) {
        dispatch({ type: 'SET_CALCULATING', isCalculating: true });
        calculateMutation.mutate(state.components);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [state.components]);

  const selectComponent = useCallback((type: string, id: number) => {
    dispatch({ type: 'SET_COMPONENT', componentType: type, componentId: id });
  }, []);

  const removeComponent = useCallback((type: string) => {
    dispatch({ type: 'REMOVE_COMPONENT', componentType: type });
  }, []);

  const loadBuild = useCallback((buildId: number) => {
    // Fetch build from API and load into state
    // Implementation depends on saved builds structure
  }, []);

  const resetBuild = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  return (
    <BuilderContext.Provider
      value={{
        state,
        dispatch,
        selectComponent,
        removeComponent,
        loadBuild,
        resetBuild,
      }}
    >
      {children}
    </BuilderContext.Provider>
  );
}

export function useBuilder() {
  const context = useContext(BuilderContext);
  if (!context) {
    throw new Error('useBuilder must be used within BuilderProvider');
  }
  return context;
}
```

#### 1.3 Component Card

**File**: `/apps/web/components/builder/component-card.tsx`

```typescript
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Cpu, MemoryStick, HardDrive, Monitor, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ComponentSelectorModal } from './component-selector-modal';

interface ComponentCardProps {
  type: 'cpu' | 'ram' | 'storage' | 'gpu';
  label: string;
  icon: React.ReactNode;
  required?: boolean;
  selectedComponent?: any;
  onSelect: (componentId: number) => void;
  onRemove: () => void;
}

const ICONS = {
  cpu: Cpu,
  ram: MemoryStick,
  storage: HardDrive,
  gpu: Monitor,
};

export function ComponentCard({
  type,
  label,
  required = false,
  selectedComponent,
  onSelect,
  onRemove,
}: ComponentCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const Icon = ICONS[type];
  const isSelected = !!selectedComponent;

  return (
    <>
      <Card
        className={cn(
          'transition-all duration-200',
          isSelected && 'border-primary border-2',
          required && !isSelected && 'border-amber-500/50 border-dashed bg-amber-50/50 dark:bg-amber-950/20'
        )}
      >
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className={cn('h-5 w-5', isSelected ? 'text-primary' : 'text-muted-foreground')} />
              <CardTitle className="text-lg">{label}</CardTitle>
              {required && !isSelected && (
                <Badge variant="outline" className="text-amber-600">
                  Recommended
                </Badge>
              )}
              {isSelected && <CheckCircle2 className="h-5 w-5 text-primary" />}
            </div>
            {isSelected && (
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => setIsModalOpen(true)}>
                  Edit
                </Button>
                <Button variant="ghost" size="sm" onClick={onRemove}>
                  ×
                </Button>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent>
          {!isSelected ? (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                {required ? 'Choose a component to continue' : 'Optional - Add if needed'}
              </p>
              <Button onClick={() => setIsModalOpen(true)} variant="outline" className="w-full">
                + Select {label}
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="font-medium">{selectedComponent.name}</div>
              <div className="text-sm text-muted-foreground">
                {/* Component-specific details */}
                {type === 'cpu' && (
                  <div>
                    {selectedComponent.cores}C/{selectedComponent.threads}T • {selectedComponent.tdp_w}W
                  </div>
                )}
                {type === 'ram' && (
                  <div>
                    {selectedComponent.total_capacity_gb}GB {selectedComponent.ddr_generation}
                  </div>
                )}
              </div>
              <div className="flex items-center justify-between pt-2 border-t">
                <span className="text-sm text-muted-foreground">Base Price:</span>
                <span className="font-semibold">${selectedComponent.estimated_price}</span>
              </div>
              {selectedComponent.adjusted_price && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Adjusted:</span>
                  <span className="font-semibold text-green-600">
                    ${selectedComponent.adjusted_price}
                  </span>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <ComponentSelectorModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        componentType={type}
        onSelect={(id) => {
          onSelect(id);
          setIsModalOpen(false);
        }}
      />
    </>
  );
}
```

### Phase 2: Valuation & Metrics (Days 3-4)

#### 2.1 Valuation Panel Component

**File**: `/apps/web/components/builder/valuation-panel.tsx`

```typescript
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useBuilder } from './builder-provider';
import { DealMeter } from './deal-meter';
import { ValuationBreakdown } from './valuation-breakdown';
import { formatCurrency } from '@/lib/valuation-utils';
import { useState } from 'react';

export function ValuationPanel() {
  const { state } = useBuilder();
  const [showBreakdown, setShowBreakdown] = useState(false);

  const hasComponents = Object.keys(state.components).length > 0;

  if (!hasComponents) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Your Build</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="text-6xl mb-4">🔧</div>
            <h3 className="text-lg font-semibold mb-2">Start Building!</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Select components to see real-time pricing and value calculations
            </p>
            <p className="text-sm text-primary mt-4">💡 Tip: Start with a CPU</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (state.isCalculating) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Your Build</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  const { pricing, metrics, valuation_breakdown } = state;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Build</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Pricing Display */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Total Price</span>
            <span className="text-2xl font-bold tabular-nums">
              {formatCurrency(pricing.base_price)}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Adjusted Value</span>
            <span className="text-lg font-semibold tabular-nums text-green-600">
              {formatCurrency(pricing.adjusted_price)}
            </span>
          </div>
        </div>

        {/* Deal Meter */}
        <DealMeter
          basePrice={pricing.base_price}
          adjustedPrice={pricing.adjusted_price}
        />

        {/* Performance Metrics */}
        {metrics.dollar_per_cpu_mark_multi && (
          <div className="space-y-3">
            <h4 className="font-semibold">Performance Metrics</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">$/CPU Mark (Multi)</span>
                <span className="font-semibold tabular-nums">
                  ${metrics.dollar_per_cpu_mark_multi.toFixed(3)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">$/CPU Mark (Single)</span>
                <span className="font-semibold tabular-nums">
                  ${metrics.dollar_per_cpu_mark_single?.toFixed(3)}
                </span>
              </div>
              {metrics.composite_score && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Composite Score</span>
                  <span className="font-semibold tabular-nums">
                    {metrics.composite_score.toFixed(1)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Breakdown Toggle */}
        <Button
          variant="outline"
          className="w-full"
          onClick={() => setShowBreakdown(!showBreakdown)}
        >
          {showBreakdown ? 'Hide' : 'View'} Breakdown {showBreakdown ? '▲' : '▼'}
        </Button>

        {showBreakdown && valuation_breakdown && (
          <ValuationBreakdown breakdown={valuation_breakdown} />
        )}

        {/* Action Buttons */}
        <div className="grid grid-cols-3 gap-2">
          <Button variant="default">Save</Button>
          <Button variant="outline">Share</Button>
          <Button variant="outline">Compare</Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### 2.2 Deal Meter Component

**File**: `/apps/web/components/builder/deal-meter.tsx`

```typescript
'use client';

import { Card } from '@/components/ui/card';
import { calculateDelta, formatCurrency } from '@/lib/valuation-utils';
import { useValuationThresholds } from '@/hooks/use-valuation-thresholds';
import { ArrowDown, ArrowUp, Flame } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DealMeterProps {
  basePrice: number;
  adjustedPrice: number;
}

export function DealMeter({ basePrice, adjustedPrice }: DealMeterProps) {
  const { data: thresholds } = useValuationThresholds();
  const { delta, deltaPercent } = calculateDelta(basePrice, adjustedPrice);

  if (!thresholds) return null;

  // Determine deal quality
  let quality: 'great' | 'good' | 'fair' | 'premium' | 'neutral';
  let icon: React.ReactNode;
  let bgClass: string;
  let textClass: string;

  if (deltaPercent >= thresholds.great_deal) {
    quality = 'great';
    icon = <Flame className="h-5 w-5" />;
    bgClass = 'bg-green-600 dark:bg-green-700';
    textClass = 'text-green-900 dark:text-green-50';
  } else if (deltaPercent >= thresholds.good_deal) {
    quality = 'good';
    icon = <ArrowDown className="h-5 w-5" />;
    bgClass = 'bg-green-500 dark:bg-green-600';
    textClass = 'text-green-900 dark:text-green-50';
  } else if (deltaPercent > 0) {
    quality = 'fair';
    icon = <ArrowDown className="h-4 w-4" />;
    bgClass = 'bg-green-100 dark:bg-green-900';
    textClass = 'text-green-800 dark:text-green-200';
  } else if (Math.abs(deltaPercent) >= thresholds.premium_warning) {
    quality = 'premium';
    icon = <ArrowUp className="h-5 w-5" />;
    bgClass = 'bg-red-500 dark:bg-red-600';
    textClass = 'text-red-900 dark:text-red-50';
  } else {
    quality = 'neutral';
    icon = null;
    bgClass = 'bg-gray-200 dark:bg-gray-700';
    textClass = 'text-gray-800 dark:text-gray-200';
  }

  const qualityLabels = {
    great: 'Great Deal!',
    good: 'Good Deal!',
    fair: 'Fair Deal',
    premium: 'Premium Price',
    neutral: 'Market Price',
  };

  const qualityEmojis = {
    great: '🔥',
    good: '💰',
    fair: '✓',
    premium: '⚠️',
    neutral: '—',
  };

  // Calculate meter position (0-100)
  const meterPosition = Math.min(100, Math.max(0, 50 + deltaPercent));

  return (
    <Card className={cn('p-4', bgClass, textClass)}>
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center gap-2">
          <span className="text-2xl">{qualityEmojis[quality]}</span>
          <h3 className="text-lg font-bold">{qualityLabels[quality]}</h3>
        </div>

        {/* Savings/Markup */}
        <div className="flex items-center gap-2 text-lg font-semibold">
          {icon}
          <span className="tabular-nums">
            {delta >= 0 ? '-' : '+'}{formatCurrency(Math.abs(delta))}
          </span>
          <span className="text-sm opacity-75">
            ({Math.abs(deltaPercent).toFixed(1)}%)
          </span>
        </div>

        {/* Visual Meter */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs opacity-75">
            <span>Premium</span>
            <span>Fair</span>
            <span>Good</span>
            <span>Great</span>
          </div>
          <div className="h-2 bg-white/30 rounded-full overflow-hidden">
            <div
              className="h-full bg-white/80 transition-all duration-500"
              style={{ width: `${meterPosition}%` }}
            />
          </div>
        </div>

        {/* Percentile */}
        {quality !== 'premium' && (
          <p className="text-sm opacity-90">
            Better than {Math.floor(meterPosition)}% of similar builds
          </p>
        )}

        {/* Tip */}
        {quality === 'premium' && (
          <p className="text-sm opacity-90">
            💡 Consider waiting or looking for alternatives
          </p>
        )}
        {quality === 'great' && (
          <p className="text-sm opacity-90">
            💡 Exceptional value - Build this!
          </p>
        )}
      </div>
    </Card>
  );
}
```

### Phase 3: Save & Share (Days 5-6)

#### 3.1 Save Build Modal

**File**: `/apps/web/components/builder/save-build-modal.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { apiFetch } from '@/lib/utils';
import { useBuilder } from './builder-provider';
import { useToast } from '@/components/ui/use-toast';

interface SaveBuildModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SaveBuildModal({ open, onOpenChange }: SaveBuildModalProps) {
  const { state } = useBuilder();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    tags: [] as string[],
    visibility: 'public' as 'private' | 'public' | 'unlisted',
    include_price_snapshot: true,
    track_price_changes: true,
  });

  const saveMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      return apiFetch('/v1/builder/builds', {
        method: 'POST',
        body: JSON.stringify({
          ...data,
          components: state.components,
          pricing: state.pricing,
          metrics: state.metrics,
          valuation_breakdown: state.valuation_breakdown,
        }),
      });
    },
    onSuccess: () => {
      toast({
        title: 'Build saved!',
        description: 'Your build has been saved successfully.',
      });
      queryClient.invalidateQueries({ queryKey: ['builds'] });
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to save',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name) {
      toast({
        title: 'Name required',
        description: 'Please enter a name for your build.',
        variant: 'destructive',
      });
      return;
    }
    saveMutation.mutate(formData);
  };

  const componentCount = Object.keys(state.components).length;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Save Build</DialogTitle>
          <DialogDescription>
            Save your build for later reference and price tracking.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Build Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Budget Gaming PC 2024"
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Balanced build for 1080p gaming..."
              rows={3}
            />
          </div>

          {/* Privacy */}
          <div className="space-y-2">
            <Label>Privacy</Label>
            <RadioGroup
              value={formData.visibility}
              onValueChange={(value: any) => setFormData({ ...formData, visibility: value })}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="private" id="private" />
                <Label htmlFor="private" className="font-normal">
                  Private (Only you can view)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="public" id="public" />
                <Label htmlFor="public" className="font-normal">
                  Public (Anyone with link can view)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="unlisted" id="unlisted" />
                <Label htmlFor="unlisted" className="font-normal">
                  Unlisted (Hidden from gallery)
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Options */}
          <div className="space-y-2">
            <Label>Options</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="snapshot"
                  checked={formData.include_price_snapshot}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, include_price_snapshot: checked as boolean })
                  }
                />
                <Label htmlFor="snapshot" className="font-normal">
                  Include price snapshot
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="track"
                  checked={formData.track_price_changes}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, track_price_changes: checked as boolean })
                  }
                />
                <Label htmlFor="track" className="font-normal">
                  Track price changes
                </Label>
              </div>
            </div>
          </div>

          {/* Summary */}
          <Card className="p-3 bg-muted">
            <div className="text-sm space-y-1">
              <p className="font-semibold">💾 Your build will be saved with:</p>
              <ul className="list-disc list-inside text-muted-foreground">
                <li>{componentCount} components</li>
                <li>Current pricing (${state.pricing.adjusted_price} adjusted)</li>
                <li>Performance metrics</li>
                <li>Valuation breakdown</li>
              </ul>
            </div>
          </Card>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'Saving...' : 'Save Build'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

## Backend Implementation

### Phase 1: API Endpoints (Days 3-4)

#### Router

**File**: `/apps/api/dealbrain_api/api/builder.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..db import get_db
from ..services import builder as builder_service
from ..schemas.builder import (
    BuildCalculationRequest,
    BuildCalculationResponse,
    SaveBuildRequest,
    SaveBuildResponse,
    BuildComparisonResponse,
)

router = APIRouter(prefix="/v1/builder", tags=["builder"])


@router.post("/calculate", response_model=BuildCalculationResponse)
async def calculate_build(
    request: BuildCalculationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Calculate valuation and metrics for a build configuration."""
    result = await builder_service.calculate_build_valuation(db, request.components)
    return result


@router.post("/builds", response_model=SaveBuildResponse)
async def save_build(
    request: SaveBuildRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save a build configuration."""
    build = await builder_service.save_build(db, request)
    return build


@router.get("/builds", response_model=List[SaveBuildResponse])
async def get_user_builds(
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all builds for a user (or all public builds if no user_id)."""
    builds = await builder_service.get_user_builds(db, user_id)
    return builds


@router.get("/builds/{build_id}", response_model=SaveBuildResponse)
async def get_build(
    build_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific build by ID."""
    build = await builder_service.get_build_by_id(db, build_id)
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return build


@router.get("/builds/shared/{share_token}", response_model=SaveBuildResponse)
async def get_shared_build(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a build by share token."""
    build = await builder_service.get_build_by_share_token(db, share_token)
    if not build:
        raise HTTPException(status_code=404, detail="Build not found")
    return build


@router.get("/compare", response_model=BuildComparisonResponse)
async def compare_build(
    cpu_id: int,
    ram_gb: int | None = None,
    storage_gb: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Compare a build configuration to similar listings."""
    comparisons = await builder_service.compare_build_to_listings(
        db, cpu_id, ram_gb, storage_gb
    )
    return comparisons
```

#### Service Layer

**File**: `/apps/api/dealbrain_api/services/builder.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from decimal import Decimal
import secrets

from ..models.core import SavedBuild, Listing, CPU
from ..schemas.builder import SaveBuildRequest
from dealbrain_core.valuation import apply_valuation_rules
from dealbrain_core.scoring import calculate_composite_score


async def calculate_build_valuation(
    db: AsyncSession, components: Dict[str, int]
) -> Dict[str, Any]:
    """
    Calculate valuation and metrics for a build configuration.

    This reuses the core valuation logic from packages/core.
    """
    # Fetch component data
    cpu = None
    if components.get("cpu_id"):
        result = await db.execute(
            select(CPU).where(CPU.id == components["cpu_id"])
        )
        cpu = result.scalar_one_or_none()

    # Build a pseudo-listing object for valuation
    # This matches the structure expected by valuation rules
    pseudo_listing = {
        "cpu_id": components.get("cpu_id"),
        "gpu_id": components.get("gpu_id"),
        "ram_spec_id": components.get("ram_spec_id"),
        "primary_storage_profile_id": components.get("primary_storage_profile_id"),
        "secondary_storage_profile_id": components.get("secondary_storage_profile_id"),
        # Add estimated base prices from catalog
        "price_usd": await _estimate_component_prices(db, components),
    }

    # Apply valuation rules (reuse existing logic)
    valuation_result = await apply_valuation_rules(db, pseudo_listing)

    # Calculate performance metrics if CPU is present
    metrics = {}
    if cpu and cpu.cpu_mark_multi:
        adjusted_price = valuation_result["adjusted_price"]
        metrics["dollar_per_cpu_mark_multi"] = float(
            adjusted_price / cpu.cpu_mark_multi
        )
        if cpu.cpu_mark_single:
            metrics["dollar_per_cpu_mark_single"] = float(
                adjusted_price / cpu.cpu_mark_single
            )

        # Calculate composite score (if profile is defined)
        # For now, use a default profile
        metrics["composite_score"] = calculate_composite_score(
            cpu_mark_multi=cpu.cpu_mark_multi,
            cpu_mark_single=cpu.cpu_mark_single,
            # Add other metrics as needed
        )

    return {
        "pricing": {
            "base_price": float(valuation_result["base_price"]),
            "adjusted_price": float(valuation_result["adjusted_price"]),
            "component_prices": valuation_result.get("component_prices", {}),
        },
        "metrics": metrics,
        "valuation_breakdown": valuation_result.get("breakdown", {}),
    }


async def save_build(
    db: AsyncSession, request: SaveBuildRequest
) -> SavedBuild:
    """Save a build configuration to the database."""
    # Generate unique share token
    share_token = secrets.token_urlsafe(32)

    build = SavedBuild(
        name=request.name,
        description=request.description,
        tags=request.tags or [],
        visibility=request.visibility,
        share_token=share_token,
        cpu_id=request.components.get("cpu_id"),
        gpu_id=request.components.get("gpu_id"),
        ram_spec_id=request.components.get("ram_spec_id"),
        primary_storage_profile_id=request.components.get("primary_storage_profile_id"),
        secondary_storage_profile_id=request.components.get("secondary_storage_profile_id"),
        base_price_usd=request.pricing["base_price"],
        adjusted_price_usd=request.pricing["adjusted_price"],
        component_prices=request.pricing.get("component_prices", {}),
        dollar_per_cpu_mark_multi=request.metrics.get("dollar_per_cpu_mark_multi"),
        dollar_per_cpu_mark_single=request.metrics.get("dollar_per_cpu_mark_single"),
        composite_score=request.metrics.get("composite_score"),
        valuation_breakdown=request.valuation_breakdown,
    )

    db.add(build)
    await db.commit()
    await db.refresh(build)

    return build


async def get_user_builds(
    db: AsyncSession, user_id: str | None = None
) -> list[SavedBuild]:
    """Get all builds for a user."""
    query = select(SavedBuild).where(SavedBuild.deleted_at.is_(None))

    if user_id:
        query = query.where(SavedBuild.user_id == user_id)
    else:
        # If no user_id, return only public builds
        query = query.where(SavedBuild.visibility == "public")

    query = query.order_by(SavedBuild.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


async def get_build_by_id(db: AsyncSession, build_id: int) -> SavedBuild | None:
    """Get a build by ID."""
    result = await db.execute(
        select(SavedBuild).where(
            SavedBuild.id == build_id,
            SavedBuild.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_build_by_share_token(
    db: AsyncSession, share_token: str
) -> SavedBuild | None:
    """Get a build by share token."""
    result = await db.execute(
        select(SavedBuild).where(
            SavedBuild.share_token == share_token,
            SavedBuild.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def compare_build_to_listings(
    db: AsyncSession, cpu_id: int, ram_gb: int | None, storage_gb: int | None
) -> Dict[str, Any]:
    """Find and compare similar listings to a build configuration."""
    # Query for listings with similar specs
    query = select(Listing).where(
        Listing.cpu_id == cpu_id,
        Listing.deleted_at.is_(None),
    )

    if ram_gb:
        # Allow some variance (±8GB)
        query = query.where(
            Listing.ram_gb.between(ram_gb - 8, ram_gb + 8)
        )

    if storage_gb:
        # Allow some variance (±256GB)
        query = query.where(
            Listing.primary_storage_gb.between(storage_gb - 256, storage_gb + 256)
        )

    query = query.order_by(Listing.adjusted_price_usd.asc()).limit(10)

    result = await db.execute(query)
    listings = result.scalars().all()

    # Format comparison data
    comparisons = []
    for listing in listings:
        comparisons.append({
            "id": listing.id,
            "title": listing.title,
            "price_usd": float(listing.price_usd),
            "adjusted_price_usd": float(listing.adjusted_price_usd or 0),
            "cpu_name": listing.cpu.name if listing.cpu else None,
            "ram_gb": listing.ram_gb,
            "storage_gb": listing.primary_storage_gb,
            "url": listing.listing_url,
        })

    return {
        "similar_listings": comparisons,
        "insights": _generate_comparison_insights(comparisons),
    }


async def _estimate_component_prices(
    db: AsyncSession, components: Dict[str, int]
) -> Decimal:
    """
    Estimate total base price from component IDs.

    This should query a pricing table or use historical data.
    For MVP, can use simple estimates.
    """
    # TODO: Implement proper price estimation
    # For now, return a placeholder
    return Decimal("500.00")


def _generate_comparison_insights(comparisons: list) -> list[str]:
    """Generate insights from listing comparisons."""
    insights = []

    if not comparisons:
        insights.append("No similar systems found in current listings")
        return insights

    avg_price = sum(c["adjusted_price_usd"] for c in comparisons) / len(comparisons)
    insights.append(
        f"Average price for similar systems: ${avg_price:.2f}"
    )

    cheaper_count = sum(1 for c in comparisons if c["adjusted_price_usd"] < avg_price)
    if cheaper_count > len(comparisons) / 2:
        insights.append(
            f"{cheaper_count} listings offer better value - worth considering"
        )

    return insights
```

## Testing Strategy

### Unit Tests

```python
# tests/test_builder_service.py

import pytest
from decimal import Decimal


@pytest.mark.asyncio
async def test_calculate_build_valuation(db_session):
    """Test build valuation calculation."""
    components = {
        "cpu_id": 1,
        "ram_spec_id": 1,
        "primary_storage_profile_id": 1,
    }

    result = await builder_service.calculate_build_valuation(
        db_session, components
    )

    assert "pricing" in result
    assert "metrics" in result
    assert result["pricing"]["adjusted_price"] > 0


@pytest.mark.asyncio
async def test_save_and_retrieve_build(db_session):
    """Test saving and retrieving builds."""
    build_data = SaveBuildRequest(
        name="Test Build",
        components={"cpu_id": 1},
        pricing={"base_price": 500, "adjusted_price": 450},
        metrics={},
        valuation_breakdown={},
        visibility="public",
    )

    # Save build
    saved = await builder_service.save_build(db_session, build_data)
    assert saved.id is not None
    assert saved.share_token is not None

    # Retrieve by ID
    retrieved = await builder_service.get_build_by_id(db_session, saved.id)
    assert retrieved.name == "Test Build"

    # Retrieve by share token
    shared = await builder_service.get_build_by_share_token(
        db_session, saved.share_token
    )
    assert shared.id == saved.id
```

### Integration Tests

```typescript
// apps/web/__tests__/builder.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BuilderPage } from '@/app/builder/page';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

describe('Builder Page', () => {
  it('shows empty state when no components selected', () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <BuilderPage />
      </QueryClientProvider>
    );

    expect(screen.getByText('Start Building!')).toBeInTheDocument();
    expect(screen.getByText(/Start with a CPU/i)).toBeInTheDocument();
  });

  it('opens component selector when clicking select button', async () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <BuilderPage />
      </QueryClientProvider>
    );

    const selectButton = screen.getByText('+ Select CPU');
    fireEvent.click(selectButton);

    await waitFor(() => {
      expect(screen.getByText('Select CPU')).toBeInTheDocument();
    });
  });

  it('updates valuation when component is selected', async () => {
    // Mock component selection
    // Verify valuation panel updates
    // Check calculations are triggered
  });
});
```

## Deployment Checklist

- [ ] Database migration created and tested (`saved_builds` table)
- [ ] Backend API endpoints implemented and documented
- [ ] Frontend components built and styled
- [ ] State management working correctly
- [ ] Calculations matching existing listing logic
- [ ] Save/load functionality tested
- [ ] Share URLs working
- [ ] Mobile responsiveness verified
- [ ] Accessibility tested (keyboard nav, screen readers)
- [ ] Performance optimized (memoization, debouncing)
- [ ] Error handling and edge cases covered
- [ ] Integration tests passing
- [ ] Documentation updated

## Performance Targets

- **Initial Page Load**: < 2s
- **Component Selection**: < 500ms
- **Calculation Update**: < 300ms (debounced)
- **Save Build**: < 1s
- **Load Saved Build**: < 500ms

## Future Enhancements

### Phase 2
- Component compatibility validation
- Price history tracking
- Automated price alerts

### Phase 3
- AI-powered component recommendations
- Build templates library
- Public build gallery with community voting
- Integration with purchase links

---

This implementation guide provides a clear roadmap from design to deployment, leveraging your existing architecture and patterns while introducing the new Deal Builder functionality.
