---
title: "ADR-011: State Management Pattern for Deal Builder Feature"
description: "Architecture decision for managing complex build configuration state with real-time valuation calculations. Recommends React Context + useReducer with strategic memoization."
audience: [ai-agents, developers, architects]
tags: [adr, architecture, state-management, react, deal-builder, performance]
created: 2025-11-12
updated: 2025-11-12
category: "architecture-design"
status: proposed
related:
  - /home/user/deal-brain/docs/project_plans/PRDs/features/deal-builder-v1.md
  - /home/user/deal-brain/docs/design/deal-builder-implementation-guide.md
  - /home/user/deal-brain/apps/web/components/builder/builder-provider.tsx
  - /home/user/deal-brain/packages/core/dealbrain_core/valuation.py
  - /home/user/deal-brain/apps/api/dealbrain_api/services/listings.py
---

# ADR-011: State Management Pattern for Deal Builder Feature

## Status

**Proposed**

## Context

### Problem Statement

The Deal Builder feature requires managing complex, interdependent state across multiple React components:

1. **Component Selection State**: CPU, GPU, RAM, Storage selections across 6+ component types with search/filtering
2. **Real-Time Valuation Calculations**: Triggered by component changes, debounced API calls, calculated metrics
3. **Deal Quality Indicators**: Color-coded display requiring thresholds comparison from `ApplicationSettings`
4. **Performance Metrics**: Dollar-per-CPU-Mark calculations that depend on CPU selection
5. **UI State**: Modal open/close, loading states, error states for 6+ selection modals
6. **Persistence Layer**: Save/share functionality requiring serializable state structure
7. **Form Validation**: Component-level validation with accumulated error state

### Architectural Constraints

- **Existing Patterns**: Deal Brain uses React Query for API state (listings page), no Zustand/Redux currently
- **Performance Requirements**:
  - Valuation calculation API response: <300ms (stated in PRD)
  - Component selection modal search: 200ms debounce
  - Page load: <2s
  - No layout shifts (CLS) during calculation updates
- **Team Familiarity**: All developers know React Context, useReducer patterns; no Zustand/Redux expertise currently available
- **Dependencies**: Minimal additional dependencies preferred (already using React Query, shadcn/ui)
- **Frontend Stack**: Next.js 14 App Router, TypeScript, React 18+, React Query v5

### Example State Complexity

Consider a simple component selection scenario:
```
User selects CPU → Triggers metrics calculation → Updates valuation → Shows deal meter
↓
User selects RAM → Re-validates storage compatibility → Updates pricing → Recalculates metrics
↓
User removes GPU → Removes GPU cost from pricing → Resets GPU-dependent metrics → Hides GPU metrics UI
```

This requires coordinated updates across multiple parts of state, each potentially triggering side effects (API calls, derived calculations).

## Decision

**We will use React Context + useReducer for Deal Builder state management** with strategic performance optimizations using React.memo, useMemo, and debouncing.

### Chosen Pattern: Reducer-Based Context

```typescript
// File: /home/user/deal-brain/apps/web/components/builder/builder-provider.tsx
'use client';

import { createContext, useContext, useReducer, useCallback, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';

// ─────────────────────────────────────────────────────────────
// Types - Serializable and AI-Agent Friendly
// ─────────────────────────────────────────────────────────────

interface ComponentSelection {
  cpu_id?: number;
  gpu_id?: number;
  ram_spec_id?: number;
  primary_storage_profile_id?: number;
  secondary_storage_profile_id?: number;
  ports_profile_id?: number;
  psu_id?: number;
  cooling_id?: number;
  case_id?: number;
  motherboard_id?: number;
  // Other components as JSON for flexibility
  other_components?: Record<string, unknown>;
}

interface PricingState {
  base_price: number;           // Sum of component prices
  adjusted_price: number;       // After valuation rules applied
  component_prices: Record<string, number>; // {"cpu": 189.00, "ram": 45.00}
  currency: 'USD' | 'EUR' | 'GBP';
}

interface MetricsState {
  dollar_per_cpu_mark_multi?: number;
  dollar_per_cpu_mark_single?: number;
  composite_score?: number;
  cpu_mark_multi?: number;
  cpu_mark_single?: number;
}

interface UIState {
  isCalculating: boolean;              // During valuation API call
  isSaving: boolean;                   // During save/share mutation
  calculationError?: string;
  selectedComponentType?: string;      // 'cpu' | 'gpu' | etc
  openModals: Record<string, boolean>; // { cpu: true, ram: false }
}

interface BuilderState {
  components: ComponentSelection;
  pricing: PricingState;
  metrics: MetricsState;
  valuation_breakdown?: Record<string, unknown>; // Full breakdown from API
  ui: UIState;
  editingBuildId?: number;             // When editing existing build
  buildName?: string;
  buildDescription?: string;
  lastCalculationTimestamp?: number;   // For cache invalidation
}

// ─────────────────────────────────────────────────────────────
// Reducer Actions - Pure Functions
// ─────────────────────────────────────────────────────────────

type BuilderAction =
  | { type: 'SELECT_COMPONENT'; payload: { type: string; id: number } }
  | { type: 'REMOVE_COMPONENT'; payload: { type: string } }
  | { type: 'START_CALCULATION' }
  | { type: 'SET_CALCULATION_RESULT'; payload: {
      pricing: PricingState;
      metrics: MetricsState;
      valuation_breakdown: Record<string, unknown>;
    } }
  | { type: 'SET_CALCULATION_ERROR'; payload: string }
  | { type: 'START_SAVING' }
  | { type: 'SET_SAVE_SUCCESS'; payload: { buildId: number } }
  | { type: 'TOGGLE_MODAL'; payload: { type: string; open: boolean } }
  | { type: 'SET_BUILD_NAME'; payload: string }
  | { type: 'SET_BUILD_DESCRIPTION'; payload: string }
  | { type: 'LOAD_BUILD'; payload: BuilderState }
  | { type: 'RESET_BUILD' }
  | { type: 'SET_EDITING_BUILD'; payload: number };

function builderReducer(state: BuilderState, action: BuilderAction): BuilderState {
  switch (action.type) {
    case 'SELECT_COMPONENT': {
      const { type, id } = action.payload;
      return {
        ...state,
        components: {
          ...state.components,
          [type === 'primary_storage' ? 'primary_storage_profile_id' : `${type}_id`]: id,
        },
        ui: { ...state.ui, isCalculating: true },
      };
    }

    case 'REMOVE_COMPONENT': {
      const { type } = action.payload;
      const key = type === 'primary_storage' ? 'primary_storage_profile_id' : `${type}_id`;
      const { [key]: _, ...rest } = state.components;
      return {
        ...state,
        components: rest,
        ui: { ...state.ui, isCalculating: true },
      };
    }

    case 'START_CALCULATION':
      return {
        ...state,
        ui: { ...state.ui, isCalculating: true, calculationError: undefined },
      };

    case 'SET_CALCULATION_RESULT':
      return {
        ...state,
        pricing: action.payload.pricing,
        metrics: action.payload.metrics,
        valuation_breakdown: action.payload.valuation_breakdown,
        ui: { ...state.ui, isCalculating: false },
        lastCalculationTimestamp: Date.now(),
      };

    case 'SET_CALCULATION_ERROR':
      return {
        ...state,
        ui: { ...state.ui, isCalculating: false, calculationError: action.payload },
      };

    case 'START_SAVING':
      return {
        ...state,
        ui: { ...state.ui, isSaving: true },
      };

    case 'SET_SAVE_SUCCESS':
      return {
        ...state,
        editingBuildId: action.payload.buildId,
        ui: { ...state.ui, isSaving: false },
      };

    case 'TOGGLE_MODAL':
      return {
        ...state,
        ui: {
          ...state.ui,
          openModals: {
            ...state.ui.openModals,
            [action.payload.type]: action.payload.open,
          },
        },
      };

    case 'SET_BUILD_NAME':
      return { ...state, buildName: action.payload };

    case 'SET_BUILD_DESCRIPTION':
      return { ...state, buildDescription: action.payload };

    case 'LOAD_BUILD':
      return action.payload;

    case 'RESET_BUILD':
      return getInitialState();

    default:
      return state;
  }
}

function getInitialState(): BuilderState {
  return {
    components: {},
    pricing: { base_price: 0, adjusted_price: 0, component_prices: {}, currency: 'USD' },
    metrics: {},
    ui: {
      isCalculating: false,
      isSaving: false,
      openModals: {},
    },
  };
}

// ─────────────────────────────────────────────────────────────
// Context and Provider
// ─────────────────────────────────────────────────────────────

interface BuilderContextValue {
  state: BuilderState;
  dispatch: React.Dispatch<BuilderAction>;
  selectComponent: (type: string, id: number) => void;
  removeComponent: (type: string) => void;
  setBuildName: (name: string) => void;
  setBuildDescription: (description: string) => void;
  resetBuild: () => void;
  loadBuild: (state: BuilderState) => void;
  toggleModal: (type: string, open: boolean) => void;
}

const BuilderContext = createContext<BuilderContextValue | undefined>(undefined);

export function BuilderProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(builderReducer, getInitialState());

  // ─────────────────────────────────────────────────────────────
  // Derived State: Memoized Calculations
  // ─────────────────────────────────────────────────────────────

  // Memoize derived state to prevent unnecessary recalculations
  const derivedState = useMemo(() => {
    const hasAllRequiredComponents = state.components.cpu_id !== undefined;
    const totalPrice = state.pricing.adjusted_price || 0;
    const savingsAmount = (state.pricing.base_price || 0) - totalPrice;
    const savingsPercent = state.pricing.base_price
      ? (savingsAmount / state.pricing.base_price) * 100
      : 0;

    return { hasAllRequiredComponents, savingsAmount, savingsPercent };
  }, [state.components, state.pricing]);

  // ─────────────────────────────────────────────────────────────
  // API Integration: Debounced Valuation Calculation
  // ─────────────────────────────────────────────────────────────

  // Mutation for valuation calculation (debounced client-side)
  const calculateBuildMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v1/builder/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state.components),
      });

      if (!response.ok) {
        throw new Error(`Calculation failed: ${response.statusText}`);
      }

      return response.json();
    },
    onSuccess: (data) => {
      dispatch({
        type: 'SET_CALCULATION_RESULT',
        payload: {
          pricing: data.pricing,
          metrics: data.metrics,
          valuation_breakdown: data.valuation_breakdown,
        },
      });
    },
    onError: (error) => {
      dispatch({
        type: 'SET_CALCULATION_ERROR',
        payload: error instanceof Error ? error.message : 'Calculation failed',
      });
    },
  });

  // ─────────────────────────────────────────────────────────────
  // Debounced Calculation Trigger (Optimization)
  // ─────────────────────────────────────────────────────────────

  // Use useEffect with debouncing to avoid excessive API calls
  // Debounce duration: 300ms (from PRD specification)
  const debounceTimerRef = React.useRef<NodeJS.Timeout>();

  React.useEffect(() => {
    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Skip calculation if no CPU selected (CPU is required)
    if (!state.components.cpu_id) {
      return;
    }

    // Set new timer for debounced calculation
    debounceTimerRef.current = setTimeout(() => {
      dispatch({ type: 'START_CALCULATION' });
      calculateBuildMutation.mutate();
    }, 300); // 300ms debounce from requirements

    // Cleanup on unmount
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [state.components, calculateBuildMutation]);

  // ─────────────────────────────────────────────────────────────
  // Memoized Callback Functions
  // ─────────────────────────────────────────────────────────────

  const selectComponent = useCallback((type: string, id: number) => {
    dispatch({ type: 'SELECT_COMPONENT', payload: { type, id } });
  }, []);

  const removeComponent = useCallback((type: string) => {
    dispatch({ type: 'REMOVE_COMPONENT', payload: { type } });
  }, []);

  const setBuildName = useCallback((name: string) => {
    dispatch({ type: 'SET_BUILD_NAME', payload: name });
  }, []);

  const setBuildDescription = useCallback((description: string) => {
    dispatch({ type: 'SET_BUILD_DESCRIPTION', payload: description });
  }, []);

  const resetBuild = useCallback(() => {
    dispatch({ type: 'RESET_BUILD' });
  }, []);

  const loadBuild = useCallback((buildState: BuilderState) => {
    dispatch({ type: 'LOAD_BUILD', payload: buildState });
  }, []);

  const toggleModal = useCallback((type: string, open: boolean) => {
    dispatch({ type: 'TOGGLE_MODAL', payload: { type, open } });
  }, []);

  // ─────────────────────────────────────────────────────────────
  // Context Value with Memoization
  // ─────────────────────────────────────────────────────────────

  const contextValue = useMemo<BuilderContextValue>(
    () => ({
      state,
      dispatch,
      selectComponent,
      removeComponent,
      setBuildName,
      setBuildDescription,
      resetBuild,
      loadBuild,
      toggleModal,
    }),
    [state, selectComponent, removeComponent, setBuildName, setBuildDescription, resetBuild, loadBuild, toggleModal]
  );

  return <BuilderContext.Provider value={contextValue}>{children}</BuilderContext.Provider>;
}

export function useBuilder() {
  const context = useContext(BuilderContext);
  if (!context) {
    throw new Error('useBuilder must be used within BuilderProvider');
  }
  return context;
}
```

## Rationale

### 1. Alignment with Existing Patterns

Deal Brain already uses React Query for API state management (listings page, component search). Adding Zustand or Redux introduces new mental models and dependencies. React Context + useReducer uses standard React patterns familiar to all team members.

**Evidence**:
- `/home/user/deal-brain/apps/web/hooks/useFieldOptions.ts` uses React Query for component lookups
- `/home/user/deal-brain/apps/web/components/listings/` uses Context for filter state with hooks pattern

### 2. Predictable State Transitions

The reducer pattern enforces explicit state transitions via typed actions, making it easier to reason about state changes and debug issues.

**Example**:
```typescript
// Clear intent: explicit action type
dispatch({ type: 'SELECT_COMPONENT', payload: { type: 'cpu', id: 42 } });

// Reducer handles all implications:
// 1. Updates components.cpu_id
// 2. Triggers isCalculating = true
// 3. Debounce handles API call (separate concern)
```

This is superior to scattered state updates via `setState` calls across multiple components.

### 3. Serialization for Persistence

The state structure is intentionally flat and serializable (no functions, no Date objects except timestamps) for easy persistence to `saved_builds` table.

**Save flow**:
```typescript
// State → Database (serializable)
const buildSnapshot = {
  components: state.components,
  pricing: state.pricing,
  metrics: state.metrics,
  valuation_breakdown: state.valuation_breakdown,
  buildName: state.buildName,
  buildDescription: state.buildDescription,
};

// Database → State (deserialize directly)
dispatch({ type: 'LOAD_BUILD', payload: buildSnapshot });
```

### 4. Performance Optimization Strategy

React Context re-renders all consumers when context value changes. We mitigate this with three techniques:

#### a) Memoized Callback Functions
All dispatch functions wrapped in `useCallback` to prevent child component re-renders:

```typescript
const selectComponent = useCallback((type: string, id: number) => {
  dispatch({ type: 'SELECT_COMPONENT', payload: { type, id } });
}, []); // Empty dependency: function never changes
```

#### b) Memoized Context Value
Context value itself is memoized to only change when state/functions actually change:

```typescript
const contextValue = useMemo<BuilderContextValue>(
  () => ({ state, dispatch, selectComponent, ... }),
  [state, selectComponent, ...]
);
```

#### c) Child Component Memoization
ComponentCard and ValuationPanel wrapped in `React.memo`:

```typescript
// File: /home/user/deal-brain/apps/web/components/builder/component-card.tsx
export const ComponentCard = React.memo(({ type, value }: Props) => {
  return (
    <div>
      {/* Memoized: only re-renders when type/value props change */}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom equality check if needed for complex props
  return prevProps.type === nextProps.type && prevProps.value === nextProps.value;
});
```

### 5. Debouncing Implementation

Debouncing at the provider level (via useEffect + setTimeout) is more reliable than attempting to debounce within components:

```typescript
// Debounce trigger: triggers recalculation after 300ms of no changes
React.useEffect(() => {
  if (debounceTimerRef.current) {
    clearTimeout(debounceTimerRef.current);
  }

  if (!state.components.cpu_id) return; // Skip if no CPU

  debounceTimerRef.current = setTimeout(() => {
    dispatch({ type: 'START_CALCULATION' });
    calculateBuildMutation.mutate();
  }, 300); // 300ms from requirements

  return () => clearTimeout(debounceTimerRef.current);
}, [state.components, calculateBuildMutation]);
```

**Benefits**:
- Centralized debounce logic (single source of truth)
- Automatic cleanup on unmount
- Works correctly even if user rapidly switches components

## Consequences

### Positive

1. **No New Dependencies**
   - Uses only React built-ins + React Query (already in use)
   - Reduces maintenance burden and bundle size

2. **Excellent Debuggability**
   - React DevTools show all reducer actions chronologically
   - Can replay state transitions during investigation
   - Clear action payloads make debugging intent obvious

3. **Testable Reducer**
   - Pure reducer function easily testable with simple inputs/outputs
   - No mocking of external dependencies needed

   ```typescript
   it('SELECT_COMPONENT updates components and triggers calculation', () => {
     const initialState = getInitialState();
     const action = { type: 'SELECT_COMPONENT', payload: { type: 'cpu', id: 42 } };
     const nextState = builderReducer(initialState, action);

     expect(nextState.components.cpu_id).toBe(42);
     expect(nextState.ui.isCalculating).toBe(true);
   });
   ```

4. **Proven Pattern in Deal Brain**
   - Used for filter state in listings page
   - Team familiar with Context + hooks patterns
   - No learning curve for developers

5. **Easy API Integration**
   - React Query mutations for save/load operations
   - Separate concerns: local state (Context) vs. server state (Query)
   - Can add optimistic updates later:
     ```typescript
     calculateBuildMutation.mutate(undefined, {
       onMutate: (variables) => {
         // Optimistically update UI before API response
         dispatch({
           type: 'SET_CALCULATION_RESULT',
           payload: estimatedResult,
         });
       },
     });
     ```

### Negative

1. **Manual Re-render Optimization Required**
   - Must remember to memoize callbacks and child components
   - If optimization missed, entire subtree re-renders on state change
   - **Mitigation**: Use ESLint rule `react/jsx-no-constructed-values` to catch common mistakes

2. **Boilerplate for Complex State**
   - More verbose than Zustand for simple state
   - Defining action types + reducer cases is repetitive
   - **Mitigation**: Code generation tools (future) or shared reducer utilities

3. **No Built-in Devtools**
   - Redux has time-travel debugging + action history browser
   - React Context has none (only React DevTools)
   - **Mitigation**: Acceptable for feature scope; can migrate to Redux if debugging becomes pain point

4. **Manual Debouncing**
   - Zustand or Redux middleware could handle debouncing declaratively
   - useEffect + setTimeout is imperative and must be replicated across features
   - **Mitigation**: Extract debounce hook to `/home/user/deal-brain/apps/web/hooks/useDebounce.ts` for reuse

### Mitigations Implemented

**ESLint Configuration** (in `/home/user/deal-brain/.eslintrc.json`):
```json
{
  "rules": {
    "react/jsx-no-constructed-values": "error",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

**Custom Debounce Hook** (reusable utility):
```typescript
// File: /home/user/deal-brain/apps/web/hooks/useDebounce.ts
import { useEffect, useRef } from 'react';

export function useDebounce(
  callback: () => void,
  dependencies: unknown[],
  delayMs: number = 300
) {
  const timerRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(callback, delayMs);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [callback, delayMs, ...dependencies]);
}
```

## Alternatives Considered

### Option A: Zustand (State Management Library)

**Pros**:
- Minimal boilerplate (no reducer functions)
- Selective re-renders by default (subscribers only subscribe to fields they use)
- Built-in persistence plugin for save/load
- Smaller bundle than Redux

**Cons**:
- New dependency (team has no experience)
- Less obvious when re-renders happen (harder to optimize)
- Persistence plugin adds magic; serialization less explicit than reducer
- No time-travel debugging

**Verdict**: Rejected. Team already knows Context + useReducer; introducing Zustand adds learning curve for marginal gains (bundle size, re-render optimization). Can migrate to Zustand in future if React Context becomes bottleneck.

**When to Revisit**: If performance profiling shows >5 unnecessary re-renders per component selection, consider Zustand for selective subscription pattern.

### Option B: React Query Only + Local State

**Pros**:
- Use existing Query infrastructure for build calculations
- Server-driven state eliminates client-side complexity

**Cons**:
- Build configuration is primarily local state, not server state
- React Query designed for managing API responses, not build config
- Awkward to model component selections as queries (not idiomatic)
- Server round-trip required for every component change (slow)

**Verdict**: Rejected. Build configuration is ephemeral client state until saved to server. Forcing it through React Query inverts the design.

### Option C: Redux Toolkit

**Pros**:
- Excellent devtools with time-travel debugging
- Established patterns and middleware ecosystem
- Works well at enterprise scale with many developers
- Excellent for debugging complex state issues

**Cons**:
- Significant boilerplate (reducer, actions, selectors)
- Overkill for this feature scope
- Extra bundle size (~20KB minified)
- Steeper learning curve; team has no Redux experience
- Requires configuring store, providers, etc.

**Verdict**: Rejected. Redux is premature optimization for Deal Builder scope. Re-evaluate if:
1. State management spans 4+ major features
2. Devtools time-travel becomes critical for debugging
3. Team grows to 10+ developers and needs standardized patterns

**Migration Path**: If migrating to Redux later, reducer structure maps directly:
```typescript
// Context reducer → Redux reducer (mechanical transformation)
const builderReducer = (state, action) => { ... } // Same logic in Redux

// Context dispatch → Redux dispatch (same action types)
dispatch({ type: 'SELECT_COMPONENT', payload: {...} }) // Works in Redux too
```

### Option D: Jotai (Lightweight Atoms)

**Pros**:
- Ultra-lightweight (~2KB)
- Primitive atoms easy to reason about
- Automatic memoization of selectors

**Cons**:
- Less familiar than Context to React developers
- Small ecosystem; fewer examples for complex patterns
- Debugging is less intuitive (atoms distributed, not centralized)
- Serialization more awkward than reducer pattern

**Verdict**: Rejected. Atomic state model doesn't match Deal Builder's requirement for coordinated state updates (selecting CPU triggers cascading changes to metrics, pricing). Reducer pattern (grouping related state updates) is more natural.

## Implementation Details

### File Structure

```
/home/user/deal-brain/apps/web/components/builder/
├── builder-provider.tsx          # Context + Reducer (this ADR)
├── component-builder.tsx         # Left panel with component cards
├── component-card.tsx            # Memoized card component
├── component-selector-modal.tsx  # Modal for component search/selection
├── valuation-panel.tsx           # Right sticky panel
├── price-display.tsx             # Pricing breakdown
├── deal-meter.tsx                # Good/Great/Fair/Premium indicator
├── performance-metrics.tsx       # CPU Mark efficiency display
├── valuation-breakdown.tsx       # Expandable detailed breakdown
└── saved-builds-section.tsx      # Saved builds list + management

/home/user/deal-brain/apps/web/hooks/
├── useBuilder.ts                 # Export from provider (already exists)
├── useDebounce.ts               # Reusable debounce hook (new)
└── useValuationThresholds.ts    # Existing hook for Deal Meter thresholds
```

### State Lifecycle Example

```
1. User opens builder page
   → BuilderProvider initializes state
   → getInitialState() creates empty components, zero pricing

2. User selects CPU (id=42)
   → ComponentCard.onSelect({ type: 'cpu', id: 42 })
   → selectComponent('cpu', 42) called
   → dispatch({ type: 'SELECT_COMPONENT', payload: { type: 'cpu', id: 42 } })
   → Reducer updates state.components.cpu_id = 42
   → Reducer sets state.ui.isCalculating = true

3. useEffect debounce timer triggered (300ms later)
   → dispatch({ type: 'START_CALCULATION' })
   → calculateBuildMutation.mutate() sends POST to /api/v1/builder/calculate
   → API processes calculation (valuation, metrics)

4. API response received
   → onSuccess callback triggered
   → dispatch({ type: 'SET_CALCULATION_RESULT', payload: {...} })
   → Reducer updates pricing, metrics, valuation_breakdown
   → Reducer sets state.ui.isCalculating = false
   → ValuationPanel re-renders with new prices and deal meter

5. User selects RAM (id=88) while previous calculation in-flight
   → selectComponent('ram', 88) called
   → Dispatch triggers new reducer state with ram_spec_id=88
   → useEffect debounce timer resets
   → Previous in-flight request still completes but ignored (React Query handles)
   → New timer expires after 300ms
   → New calculation request sent

6. User clicks "Save Build"
   → SaveBuildsSection receives state via useBuilder()
   → BuildName, BuildDescription from state passed to save mutation
   → POST /api/v1/builder/builds with serialized state
   → API saves to SavedBuild table
   → onSuccess callback: dispatch({ type: 'SET_SAVE_SUCCESS', payload: { buildId } })
   → editingBuildId set; UI shows "Build saved" indicator
```

### Performance Optimization Checklist

When implementing child components, ensure:

1. **ComponentCard** memoized:
   ```typescript
   export const ComponentCard = React.memo(({ type, selection }: Props) => {
     return <div>{/* Component content */}</div>;
   });
   ```

2. **Callbacks wrapped in useCallback**:
   ```typescript
   const handleSelect = useCallback((id: number) => {
     selectComponent(type, id);
   }, [type, selectComponent]);
   ```

3. **Derived values memoized**:
   ```typescript
   const dealQuality = useMemo(() => {
     return calculateDealQuality(state.pricing.adjusted_price, thresholds);
   }, [state.pricing.adjusted_price, thresholds]);
   ```

4. **Large lists virtualized** (if build history >100 items):
   ```typescript
   // Use react-window for SavedBuildsSection infinite scroll
   import { FixedSizeList } from 'react-window';
   ```

## Migration Path

If future analysis shows React Context bottleneck (e.g., >100ms re-render times):

1. **Phase 1: Profile with React DevTools Profiler**
   - Identify which components render unnecessarily
   - Measure re-render frequency during rapid component selection

2. **Phase 2: Zustand Migration** (if Context problematic)
   - Create Zustand store with same state structure
   - Reducer → Zustand store actions (mechanical translation)
   - Extract BuilderProvider → useBuilderStore hook
   - Zero API changes; child components continue using `useBuilder()` hook

3. **Phase 3: Redux Migration** (if Zustand insufficient)
   - Only if managing state across 4+ major features (e.g., compare-builds, wishlist, etc.)
   - Reducer logic maps 1:1 to Redux reducer
   - Action types reusable unchanged

**Key Principle**: Migration is low-friction because state is normalized and reducer is decoupled from React.

## References

**Existing Deal Brain Patterns**:
- Context + hooks pattern: `/home/user/deal-brain/apps/web/components/listings/filter-provider.tsx`
- React Query integration: `/home/user/deal-brain/apps/web/hooks/useFieldOptions.ts`
- Performance optimization: `/home/user/deal-brain/apps/web/components/listings/listings-table.tsx` (memoized rows)

**PRD & Design**:
- `/home/user/deal-brain/docs/project_plans/PRDs/features/deal-builder-v1.md` (performance requirements)
- `/home/user/deal-brain/docs/design/deal-builder-implementation-guide.md` (architecture diagram)

**Related Architecture**:
- `/home/user/deal-brain/docs/architecture/adr/ADR-007-catalog-state-management.md` (similar Context pattern for catalog)
- `/home/user/deal-brain/packages/core/dealbrain_core/valuation.py` (domain logic Deal Builder delegates to)

**React Documentation**:
- [useReducer Hook](https://react.dev/reference/react/useReducer)
- [Context API](https://react.dev/reference/react/createContext)
- [React.memo](https://react.dev/reference/react/memo)
- [useMemo & useCallback](https://react.dev/reference/react/useMemo)

**Testing**:
- Reducer unit tests: Pure function testing, no mocking required
- Provider integration tests: Use React Testing Library `renderWithProvider` helper
- See `/home/user/deal-brain/tests/` for pytest patterns; apply same principles to JS tests

## Open Questions for Team Discussion

1. Should we add Redux DevTools support to Context (via middleware-like pattern) for easier debugging?
2. Should SavedBuilds support branching/versioning (save multiple variations of same build)?
3. Should we implement undo/redo (replay actions) given reducer architecture naturally supports it?
4. Should we cache recent calculations to avoid re-fetching same component combinations?

---

**Decision Made By**: [AI Artifacts Engineer]
**Decision Date**: 2025-11-12
**Status**: Proposed (Ready for Architecture Review)
