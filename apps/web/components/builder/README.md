# Builder Components

React components for the Deal Builder feature - PC configuration with real-time valuation.

## Architecture

### State Management

**BuilderProvider** (`builder-provider.tsx`)
- React Context with `useReducer` for global state
- Manages component selection, valuation, and metrics
- Auto-clears calculations when components change

```typescript
import { useBuilder } from '@/components/builder';

function MyComponent() {
  const { state, dispatch } = useBuilder();

  // Access state
  const { components, valuation, metrics, isCalculating } = state;

  // Update state
  dispatch({
    type: 'SELECT_COMPONENT',
    payload: { componentType: 'cpu_id', id: 1 }
  });
}
```

### Components

**ComponentBuilder** (`component-builder.tsx`)
- Main layout with 6 component cards
- Manages modal state for component selection
- Handles component selection/removal
- Currently uses mock data (Phase 6 will add real API integration)

**ComponentCard** (`component-card.tsx`)
- Individual component card with empty/selected states
- Shows component name, specs, and price
- "Change" and "Remove" actions
- Supports disabled state and required indicators

**ComponentSelectorModal** (`component-selector-modal.tsx`)
- Modal for searching and selecting components
- Real-time search filtering
- Scrollable component list
- Shows component details with badges

## Usage

### Basic Setup

```typescript
import { BuilderProvider } from '@/components/builder';
import { ComponentBuilder } from '@/components/builder';

export default function BuilderPage() {
  return (
    <BuilderProvider>
      <ComponentBuilder />
    </BuilderProvider>
  );
}
```

### Accessing State

```typescript
import { useBuilder } from '@/components/builder';

function CustomComponent() {
  const { state } = useBuilder();

  // Check if CPU is selected
  if (state.components.cpu_id) {
    // CPU is selected
  }

  // Check if valuation is available
  if (state.valuation) {
    console.log(`Price: $${state.valuation.adjusted_price}`);
  }
}
```

### Dispatching Actions

```typescript
const { dispatch } = useBuilder();

// Select a component
dispatch({
  type: 'SELECT_COMPONENT',
  payload: { componentType: 'cpu_id', id: 1 }
});

// Remove a component
dispatch({
  type: 'REMOVE_COMPONENT',
  payload: { componentType: 'gpu_id' }
});

// Set calculations (Phase 6)
dispatch({
  type: 'SET_CALCULATIONS',
  payload: { valuation, metrics }
});

// Set calculating state
dispatch({ type: 'SET_CALCULATING', payload: true });

// Set error
dispatch({ type: 'SET_ERROR', payload: 'Error message' });

// Reset entire build
dispatch({ type: 'RESET_BUILD' });
```

## Component Types

The builder supports 6 component types:

1. **cpu_id** (Required) - Central Processing Unit
2. **gpu_id** (Optional) - Graphics Processing Unit
3. **ram_spec_id** (Optional) - Memory
4. **storage_spec_id** (Optional) - Storage
5. **psu_spec_id** (Optional) - Power Supply
6. **case_spec_id** (Optional) - Case

## State Structure

```typescript
interface BuilderState {
  components: {
    cpu_id: number | null;
    gpu_id: number | null;
    ram_spec_id: number | null;
    storage_spec_id: number | null;
    psu_spec_id: number | null;
    case_spec_id: number | null;
  };
  valuation: ValuationBreakdown | null;
  metrics: BuildMetrics | null;
  isCalculating: boolean;
  lastCalculated: Date | null;
  error: string | null;
}
```

## API Client

**Functions** (`lib/api/builder.ts`):

```typescript
// Calculate valuation without saving
calculateBuild(components: BuildComponents): Promise<CalculateBuildResponse>

// Save a build
saveBuild(buildData: SaveBuildRequest): Promise<SavedBuild>

// Get user's builds
getUserBuilds(limit?: number, offset?: number): Promise<ListBuildsResponse>

// Get specific build
getBuildById(buildId: number): Promise<SavedBuild>

// Get shared build
getSharedBuild(shareToken: string): Promise<SavedBuild>
```

## Phase 6 Integration

Phase 6 will add:

1. **useBuilderCalculations hook** - Automatic calculations with debouncing
2. **ValuationPanel** - Display pricing and metrics
3. **DealMeter** - Color-coded deal rating
4. **PerformanceMetrics** - CPU Mark efficiency display
5. **Real catalog integration** - Replace mock data with APIs

See `.claude/worknotes/deal-builder-v1/phase-6-handoff.md` for details.

## Testing

### Manual Testing

1. Start dev server: `make web`
2. Navigate to `/builder`
3. Select CPU (required)
4. Select optional components
5. Verify component cards update
6. Test modal search functionality
7. Test responsive layout

### Component Testing

```typescript
import { render, screen } from '@testing-library/react';
import { BuilderProvider } from '@/components/builder';
import { ComponentBuilder } from '@/components/builder';

test('renders component builder', () => {
  render(
    <BuilderProvider>
      <ComponentBuilder />
    </BuilderProvider>
  );

  expect(screen.getByText('CPU')).toBeInTheDocument();
});
```

## File Structure

```
components/builder/
├── README.md                          # This file
├── index.ts                           # Centralized exports
├── builder-provider.tsx               # State management context
├── component-builder.tsx              # Main layout
├── component-card.tsx                 # Individual component cards
└── component-selector-modal.tsx       # Selection modal

# Phase 6 will add:
├── valuation-panel.tsx                # Pricing display
├── deal-meter.tsx                     # Deal rating indicator
└── performance-metrics.tsx            # Metrics display
```

## Related Files

- **API Client**: `apps/web/lib/api/builder.ts`
- **Page Route**: `apps/web/app/builder/page.tsx`
- **Hooks**: `apps/web/hooks/use-builder-calculations.ts` (Phase 6)

## Design Patterns

- **Context + Reducer**: Predictable state management
- **Component Composition**: Reusable, focused components
- **Separation of Concerns**: UI, state, and API logic separated
- **Type Safety**: Comprehensive TypeScript interfaces
- **Responsive Design**: Mobile-first with desktop enhancements

## Contributing

When adding new features:

1. Follow existing naming conventions
2. Update state types in `builder-provider.tsx`
3. Add new actions if needed
4. Export from `index.ts`
5. Update this README
6. Add TypeScript types for all props

## Performance Considerations

- Component selection triggers state update (instant)
- Calculations cleared on component change (prevents stale data)
- Phase 6 will add debouncing (300ms) for API calls
- React Query caching for catalog data (5 minutes)
- No caching for calculations (always fresh)
