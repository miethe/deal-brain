---
title: "Deal Builder - Phase 5-7: Frontend Components & Features"
description: "React component architecture, state management, real-time calculations, save/share workflows. Covers BuilderProvider, component selection, valuation display, and shareable URLs."
audience: [ai-agents, developers]
tags: [implementation, frontend, react, components, state-management, phases-5-7]
created: 2025-11-12
updated: 2025-11-12
category: "product-planning"
status: draft
related:
  - /home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1.md
  - /home/user/deal-brain/docs/design/deal-builder-ux-specification.md
  - /home/user/deal-brain/docs/design/deal-builder-implementation-guide.md
---

# Phase 5-7: Frontend Components & Features

## Overview

Phases 5-7 implement the React frontend with component selection, real-time calculations, and save/share functionality. These phases can run in parallel with Phase 4 API development - start with mocked APIs.

**Timeline**: Days 10-17 (approximately 3 weeks)
**Effort**: 13 story points
**Agents**: ui-engineer-enhanced, frontend-developer, react-performance-optimizer

---

## Phase 5: Frontend Component Structure (Days 10-11, 3 story points)

### Task 5.1: Create BuilderProvider Context & Page Layout

**Assigned to**: ui-engineer-enhanced

**Description**: Set up React Context for builder state management and page structure.

**Technical Details**:

```typescript
// apps/web/components/builder/builder-context.tsx

import { createContext, useContext, useReducer, useCallback, useEffect } from 'react';

export interface BuilderState {
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
  lastCalculated?: number;
  editingBuildId?: number;
  error?: string;
}

export type BuilderAction =
  | { type: 'SET_COMPONENT'; componentType: string; componentId: number | null }
  | { type: 'REMOVE_COMPONENT'; componentType: string }
  | { type: 'SET_CALCULATION_RESULT'; payload: any }
  | { type: 'SET_CALCULATING'; isCalculating: boolean }
  | { type: 'SET_ERROR'; error?: string }
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
      return { ...state, components: rest };
    case 'SET_CALCULATION_RESULT':
      return {
        ...state,
        pricing: action.payload.pricing,
        metrics: action.payload.metrics,
        valuation_breakdown: action.payload.valuation_breakdown,
        isCalculating: false,
        error: undefined,
        lastCalculated: Date.now(),
      };
    case 'SET_CALCULATING':
      return { ...state, isCalculating: action.isCalculating };
    case 'SET_ERROR':
      return { ...state, error: action.error, isCalculating: false };
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

const BuilderContext = createContext<{
  state: BuilderState;
  dispatch: React.Dispatch<BuilderAction>;
  selectComponent: (type: string, id: number) => void;
  removeComponent: (type: string) => void;
  loadBuild: (build: any) => void;
  resetBuild: () => void;
} | null>(null);

export function BuilderProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(builderReducer, initialState);

  const selectComponent = useCallback((type: string, id: number) => {
    dispatch({ type: 'SET_COMPONENT', componentType: type, componentId: id });
  }, []);

  const removeComponent = useCallback((type: string) => {
    dispatch({ type: 'REMOVE_COMPONENT', componentType: type });
  }, []);

  const loadBuild = useCallback((build: any) => {
    dispatch({ type: 'LOAD_BUILD', build });
  }, []);

  const resetBuild = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  return (
    <BuilderContext.Provider
      value={{ state, dispatch, selectComponent, removeComponent, loadBuild, resetBuild }}
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

**Page Layout**:
```typescript
// apps/web/app/builder/page.tsx

import { BuilderProvider } from '@/components/builder/builder-provider';
import { ComponentBuilder } from '@/components/builder/component-builder';
import { ValuationPanel } from '@/components/builder/valuation-panel';
import { SavedBuildsSection } from '@/components/builder/saved-builds-section';

export default function BuilderPage() {
  return (
    <BuilderProvider>
      <div className="container mx-auto py-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Build & Price</h1>
          <p className="text-muted-foreground mt-2">
            Create custom PC builds with real-time valuation and performance metrics
          </p>
        </div>

        {/* Main Layout: Two-column on desktop, stack on mobile */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-12">
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
        <SavedBuildsSection />
      </div>
    </BuilderProvider>
  );
}
```

**Acceptance Criteria**:
- Context provider working with reducer
- All dispatch actions handled correctly
- Page layout matches design (2-column desktop, 1-column mobile)
- Sticky panel behavior on desktop
- No state loss on re-render
- Type safety for actions and state

**Files Created**:
- `apps/web/components/builder/builder-context.tsx`
- `apps/web/app/builder/page.tsx`

**Effort**: 1.5 story points

---

### Task 5.2: Implement ComponentCard & ComponentSelectorModal

**Assigned to**: frontend-developer

**Description**: Create component selection UI with search and filtering.

**Technical Details**:

```typescript
// apps/web/components/builder/component-card.tsx

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Cpu, MemoryStick, HardDrive, Monitor, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ComponentSelectorModal } from './component-selector-modal';
import { useBuilder } from './builder-context';

interface ComponentCardProps {
  type: 'cpu' | 'ram' | 'primary_storage' | 'secondary_storage' | 'gpu';
  label: string;
  required?: boolean;
}

const ICONS = {
  cpu: Cpu,
  ram: MemoryStick,
  primary_storage: HardDrive,
  secondary_storage: HardDrive,
  gpu: Monitor,
};

export function ComponentCard({ type, label, required = false }: ComponentCardProps) {
  const { state, selectComponent, removeComponent } = useBuilder();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const typeKey = `${type}_id`;
  const componentId = state.components[typeKey as keyof typeof state.components];
  const isSelected = !!componentId;
  const Icon = ICONS[type];

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
            </div>
            {isSelected && (
              <div className="flex gap-2">
                <CheckCircle2 className="h-5 w-5 text-primary" />
                <Button variant="ghost" size="sm" onClick={() => setIsModalOpen(true)}>
                  Edit
                </Button>
                <Button variant="ghost" size="sm" onClick={() => removeComponent(typeKey)}>
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
              <p className="font-medium">Component selected (ID: {componentId})</p>
              <p className="text-sm text-muted-foreground">
                Integration with real component data in Phase 5.2
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <ComponentSelectorModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        componentType={type}
        onSelect={(id) => {
          selectComponent(typeKey, id);
          setIsModalOpen(false);
        }}
      />
    </>
  );
}
```

```typescript
// apps/web/components/builder/component-selector-modal.tsx

import { useState, useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/lib/utils';

interface ComponentSelectorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  componentType: string;
  onSelect: (id: number) => void;
}

export function ComponentSelectorModal({
  open,
  onOpenChange,
  componentType,
  onSelect,
}: ComponentSelectorModalProps) {
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // Fetch components (TODO: Replace with real API endpoint)
  const { data: components = [], isLoading } = useQuery({
    queryKey: ['components', componentType],
    queryFn: async () => {
      // Mock data for now
      return [
        { id: 1, name: 'Intel Core i5-12400', specs: '6C/12T • 65W' },
        { id: 2, name: 'Intel Core i7-12700', specs: '12C/20T • 65W' },
      ];
    },
    enabled: open,
  });

  const filtered = useMemo(() => {
    if (!search) return components;
    return components.filter((c) =>
      c.name.toLowerCase().includes(search.toLowerCase())
    );
  }, [components, search]);

  const handleSelect = () => {
    if (selectedId) {
      onSelect(selectedId);
      setSearch('');
      setSelectedId(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[70vh]">
        <DialogHeader>
          <DialogTitle>Select {componentType}</DialogTitle>
          <DialogDescription>
            Search and select a component for your build
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search */}
          <Input
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />

          {/* Component List */}
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {isLoading ? (
              <p className="text-sm text-muted-foreground">Loading...</p>
            ) : filtered.length === 0 ? (
              <p className="text-sm text-muted-foreground">No components found</p>
            ) : (
              filtered.map((component) => (
                <button
                  key={component.id}
                  onClick={() => setSelectedId(component.id)}
                  className={cn(
                    'w-full p-3 text-left rounded-lg border transition-colors',
                    selectedId === component.id
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:bg-accent'
                  )}
                >
                  <div className="font-medium">{component.name}</div>
                  <div className="text-sm text-muted-foreground">{component.specs}</div>
                </button>
              ))
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSelect}
              disabled={!selectedId}
            >
              Select Component
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

**Acceptance Criteria**:
- Component cards render correctly (empty and selected states)
- Modal opens/closes properly
- Search filters results
- Selection updates context correctly
- Icons display correctly
- Mobile responsive (full-screen modal on small screens)

**Files Created**:
- `apps/web/components/builder/component-card.tsx`
- `apps/web/components/builder/component-selector-modal.tsx`

**Effort**: 1.5 story points

---

### Task 5.3: Create ComponentBuilder Layout

**Assigned to**: frontend-developer

**Description**: Container component arranging component cards in proper order.

**Technical Details**:

```typescript
// apps/web/components/builder/component-builder.tsx

import { ComponentCard } from './component-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function ComponentBuilder() {
  return (
    <div className="space-y-6">
      {/* Essential Components */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Essential Components</h2>
        <div className="space-y-4">
          <ComponentCard
            type="cpu"
            label="Processor (CPU)"
            required={true}
          />
        </div>
      </div>

      {/* Recommended Components */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Recommended Components</h2>
        <div className="space-y-4">
          <ComponentCard type="ram" label="Memory (RAM)" required={true} />
          <ComponentCard type="primary_storage" label="Primary Storage" required={true} />
        </div>
      </div>

      {/* Optional Components */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Optional Components</h2>
        <div className="space-y-4">
          <ComponentCard type="gpu" label="Graphics Card (GPU)" />
          <ComponentCard type="secondary_storage" label="Secondary Storage" />
        </div>
      </div>

      {/* Tips */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <CardContent className="pt-6">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            💡 <strong>Tip:</strong> Start by selecting a CPU - it's required for performance metrics.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Acceptance Criteria**:
- Components arrange in correct order (essential → recommended → optional)
- Sections labeled clearly
- Responsive on mobile (all cards full width)
- Helper tip visible
- Integration with ComponentCard working

**Files Created**:
- `apps/web/components/builder/component-builder.tsx`

**Effort**: 0.5 story points

---

## Phase 6: Valuation Display & Real-time Calculations (Days 12-14, 5 story points)

### Task 6.1: Create ValuationPanel & DealMeter Components

**Assigned to**: frontend-developer

**Description**: Build sticky valuation display panel with deal quality indicator.

**Technical Details**: See existing design-builder-implementation-guide.md for DealMeter implementation. Key points:
- Sticky positioning on desktop (lg:sticky)
- Floating drawer on mobile
- Real-time updates with loading state
- Color-coded deal quality indicators

**Implementation Outline**:

```typescript
// apps/web/components/builder/valuation-panel.tsx

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useBuilder } from './builder-context';
import { DealMeter } from './deal-meter';
import { PerformanceMetrics } from './performance-metrics';
import { useState } from 'react';

export function ValuationPanel() {
  const { state } = useBuilder();
  const [showBreakdown, setShowBreakdown] = useState(false);

  const hasComponents = Object.keys(state.components).length > 0;

  if (!hasComponents) {
    return <EmptyState />;
  }

  if (state.isCalculating) {
    return <LoadingState />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Build</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Pricing */}
        <PricingDisplay pricing={state.pricing} />

        {/* Deal Meter */}
        <DealMeter
          basePrice={state.pricing.base_price}
          adjustedPrice={state.pricing.adjusted_price}
        />

        {/* Metrics */}
        {state.metrics && <PerformanceMetrics metrics={state.metrics} />}

        {/* Breakdown */}
        <Button
          variant="outline"
          className="w-full"
          onClick={() => setShowBreakdown(!showBreakdown)}
        >
          {showBreakdown ? 'Hide' : 'View'} Breakdown {showBreakdown ? '▲' : '▼'}
        </Button>

        {showBreakdown && state.valuation_breakdown && (
          <ValuationBreakdown breakdown={state.valuation_breakdown} />
        )}

        {/* Action Buttons */}
        <ActionButtons />
      </CardContent>
    </Card>
  );
}
```

**Acceptance Criteria**:
- Panel sticky on desktop (lg:sticky)
- Displays pricing correctly (base + adjusted)
- Deal meter shows correct color/message
- Performance metrics display with correct labels
- Loading state shown during calculation
- Error state handled gracefully
- Mobile responsive (drawer or modal)

**Files Created/Modified**:
- `apps/web/components/builder/valuation-panel.tsx`
- `apps/web/components/builder/deal-meter.tsx`
- `apps/web/components/builder/performance-metrics.tsx`
- `apps/web/components/builder/valuation-breakdown.tsx`

**Effort**: 2.5 story points

---

### Task 6.2: Integrate Real-time API Calculations with Debouncing

**Assigned to**: react-performance-optimizer

**Description**: Connect component selection to live API calls with 300ms debounce.

**Technical Details**:

```typescript
// apps/web/hooks/use-builder-calculation.ts

import { useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useBuilder } from '@/components/builder/builder-context';
import { apiFetch } from '@/lib/utils';

export function useBuilderCalculation() {
  const { state, dispatch } = useBuilder();

  const calculateMutation = useMutation({
    mutationFn: async (components: any) => {
      return apiFetch('/v1/builder/calculate', {
        method: 'POST',
        body: JSON.stringify({ components }),
      });
    },
    onSuccess: (data) => {
      dispatch({
        type: 'SET_CALCULATION_RESULT',
        payload: data,
      });
    },
    onError: (error: any) => {
      dispatch({
        type: 'SET_ERROR',
        error: error.message || 'Calculation failed',
      });
    },
  });

  // Debounced calculation trigger
  useEffect(() => {
    // Don't calculate if no CPU selected
    if (!state.components.cpu_id) {
      return;
    }

    dispatch({ type: 'SET_CALCULATING', isCalculating: true });

    const timer = setTimeout(() => {
      calculateMutation.mutate(state.components);
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [state.components]);

  return {
    isCalculating: state.isCalculating,
    error: state.error,
  };
}
```

**Integration in Page**:
```typescript
// apps/web/app/builder/page.tsx (modify)

export default function BuilderPage() {
  return (
    <BuilderProvider>
      <BuilderCalculationSync />
      {/* ... rest of page ... */}
    </BuilderProvider>
  );
}

function BuilderCalculationSync() {
  useBuilderCalculation(); // Triggers calculations
  return null;
}
```

**Acceptance Criteria**:
- API calls trigger on component selection
- 300ms debounce prevents excessive requests
- Loading state shows during calculation
- Success updates UI correctly
- Errors displayed to user
- Calculation doesn't trigger without CPU

**Files Created**:
- `apps/web/hooks/use-builder-calculation.ts`

**Effort**: 2.5 story points

---

## Phase 7: Save/Share Features (Days 15-17, 5 story points)

### Task 7.1: SaveBuildModal & Save Functionality

**Assigned to**: ui-engineer-enhanced

**Description**: Modal for saving builds with persistence to database.

**Acceptance Criteria**:
- Modal opens from ValuationPanel "Save" button
- Form validation (name required)
- Save creates build with snapshot
- Success toast notification
- Saved builds appear in SavedBuildsSection
- Database persistence working
- Share token generated and returned

**Files to Create**:
- `apps/web/components/builder/save-build-modal.tsx`
- `apps/web/hooks/use-save-build.ts`

**Effort**: 1.5 story points

---

### Task 7.2: SavedBuildsSection & Build Management

**Assigned to**: frontend-developer

**Description**: Gallery of user's saved builds with load/edit/delete actions.

**Key Features**:
- Grid layout (3 cols desktop, 1 col mobile)
- Build cards show name, price delta, deal quality
- Load action populates builder
- Edit action opens form
- Delete requires confirmation
- Pagination for many builds

**Files to Create**:
- `apps/web/components/builder/saved-builds-section.tsx`
- `apps/web/components/builder/saved-build-card.tsx`
- `apps/web/hooks/use-saved-builds.ts`

**Effort**: 1.5 story points

---

### Task 7.3: Share Functionality & Shared Build View

**Assigned to**: frontend-developer

**Description**: Share modal and read-only shared build page.

**Key Features**:
- Share button opens modal with copy link
- Share token in URL (`/builder/shared/[token]`)
- Shared page shows read-only build
- "Build Your Own" button to load into editor
- Price update banner if prices changed

**Files to Create**:
- `apps/web/components/builder/share-modal.tsx`
- `apps/web/app/builder/shared/[token]/page.tsx`
- `apps/web/hooks/use-shared-build.ts`

**Effort**: 1.5 story points

---

## Summary: Phase 5-7 Deliverables

| Phase | Component | File | Status |
|-------|-----------|------|--------|
| 5 | BuilderProvider | `builder-context.tsx` | Core |
| 5 | ComponentCard | `component-card.tsx` | Core |
| 5 | ComponentSelector | `component-selector-modal.tsx` | Core |
| 5 | ComponentBuilder | `component-builder.tsx` | Layout |
| 6 | ValuationPanel | `valuation-panel.tsx` | Core |
| 6 | DealMeter | `deal-meter.tsx` | Display |
| 6 | PerformanceMetrics | `performance-metrics.tsx` | Display |
| 6 | Calculation Hook | `use-builder-calculation.ts` | Integration |
| 7 | SaveBuildModal | `save-build-modal.tsx` | Core |
| 7 | SavedBuildsSection | `saved-builds-section.tsx` | Core |
| 7 | SavedBuildCard | `saved-build-card.tsx` | Display |
| 7 | ShareModal | `share-modal.tsx` | Core |
| 7 | SharedBuildPage | `app/builder/shared/[token]/page.tsx` | Page |

## Quality Gates for Phase 5-7 Completion

Before proceeding to Phase 8 (Testing):

- [ ] All components render without errors
- [ ] Context state management working
- [ ] Component selection updates calculation
- [ ] Valuation panel updates in real-time
- [ ] Save workflow end-to-end working
- [ ] Saved builds display and load correctly
- [ ] Share URLs accessible and functional
- [ ] Shared view shows read-only build
- [ ] Mobile layout verified on real devices
- [ ] No console errors or warnings

---

**Total Effort**: 13 story points
**Timeline**: Days 10-17 (~1.5 weeks each for Phases 5 and 6-7)
**Agents**: ui-engineer-enhanced (5pts), frontend-developer (6pts), react-performance-optimizer (2pts)

Next phase: [Phase 8: Testing, Mobile & Deployment](./phase-8-validation.md)
