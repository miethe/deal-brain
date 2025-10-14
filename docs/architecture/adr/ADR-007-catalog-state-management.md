# ADR 007: Catalog View State Management with Zustand

**Status:** Accepted
**Date:** 2025-10-06
**Decision Makers:** Lead Architect (Claude Code)
**Related PRD:** [Listings Catalog View Revamp PRD](../../project_plans/requests/listings-revamp/PRD.md)

---

## Context

The Listings Catalog View Revamp introduces three new interactive views (Grid, Dense List, Master/Detail) with complex client-side state requirements:

- Active view mode (grid | list | master-detail)
- Active tab (catalog | data)
- Filter state (search query, form factor, manufacturer, price range)
- Compare selections (array of listing IDs)
- Selected listing for detail panel
- Multiple dialog open states

We need to decide on the state management approach that balances:
1. **Developer Experience:** Simple API, minimal boilerplate
2. **Performance:** Efficient re-renders, no unnecessary updates
3. **Persistence:** Save state to localStorage and URL params
4. **Maintainability:** Clear patterns, testable, scalable

---

## Decision

We will use **Zustand** as the primary state management solution for catalog view state.

### Implementation Details

```typescript
// apps/web/stores/catalog-store.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface CatalogState {
  // View mode
  activeView: 'grid' | 'list' | 'master-detail';
  setActiveView: (view: CatalogState['activeView']) => void;

  // Active tab
  activeTab: 'catalog' | 'data';
  setActiveTab: (tab: CatalogState['activeTab']) => void;

  // Filters
  filters: {
    searchQuery: string;
    formFactor: string;
    manufacturer: string;
    priceRange: number;
  };
  setFilters: (filters: Partial<CatalogState['filters']>) => void;
  clearFilters: () => void;

  // Compare selections
  compareSelections: number[];
  toggleCompare: (id: number) => void;
  clearCompare: () => void;

  // Selected listing for detail panel
  selectedListingId: number | null;
  setSelectedListing: (id: number | null) => void;

  // Dialog states
  detailsDialogOpen: boolean;
  detailsDialogListingId: number | null;
  openDetailsDialog: (id: number) => void;
  closeDetailsDialog: () => void;

  quickEditDialogOpen: boolean;
  quickEditDialogListingId: number | null;
  openQuickEditDialog: (id: number) => void;
  closeQuickEditDialog: () => void;
}

export const useCatalogStore = create<CatalogState>()(
  persist(
    (set) => ({
      // Initial state
      activeView: 'grid',
      activeTab: 'catalog',
      filters: {
        searchQuery: '',
        formFactor: 'all',
        manufacturer: 'all',
        priceRange: 2500,
      },
      compareSelections: [],
      selectedListingId: null,
      detailsDialogOpen: false,
      detailsDialogListingId: null,
      quickEditDialogOpen: false,
      quickEditDialogListingId: null,

      // Actions
      setActiveView: (view) => set({ activeView: view }),
      setActiveTab: (tab) => set({ activeTab: tab }),
      setFilters: (newFilters) =>
        set((state) => ({
          filters: { ...state.filters, ...newFilters },
        })),
      clearFilters: () =>
        set({
          filters: {
            searchQuery: '',
            formFactor: 'all',
            manufacturer: 'all',
            priceRange: 2500,
          },
        }),
      toggleCompare: (id) =>
        set((state) => ({
          compareSelections: state.compareSelections.includes(id)
            ? state.compareSelections.filter((itemId) => itemId !== id)
            : [...state.compareSelections, id],
        })),
      clearCompare: () => set({ compareSelections: [] }),
      setSelectedListing: (id) => set({ selectedListingId: id }),
      openDetailsDialog: (id) =>
        set({ detailsDialogOpen: true, detailsDialogListingId: id }),
      closeDetailsDialog: () =>
        set({ detailsDialogOpen: false, detailsDialogListingId: null }),
      openQuickEditDialog: (id) =>
        set({ quickEditDialogOpen: true, quickEditDialogListingId: id }),
      closeQuickEditDialog: () =>
        set({ quickEditDialogOpen: false, quickEditDialogListingId: null }),
    }),
    {
      name: 'catalog-view-storage',
      partialize: (state) => ({
        activeView: state.activeView,
        activeTab: state.activeTab,
        filters: state.filters,
        // Don't persist: compareSelections, selectedListingId, dialog states
      }),
    }
  )
);

// Custom hooks for selective state subscription
export const useActiveView = () =>
  useCatalogStore((state) => state.activeView);
export const useFilters = () => useCatalogStore((state) => state.filters);
export const useCompareSelections = () =>
  useCatalogStore((state) => state.compareSelections);
```

### URL Synchronization Strategy

```typescript
// apps/web/hooks/use-url-sync.ts

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useCatalogStore } from '@/stores/catalog-store';

export function useUrlSync() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { activeView, activeTab, filters, setActiveView, setActiveTab, setFilters } =
    useCatalogStore();

  // Hydrate store from URL on mount
  useEffect(() => {
    const view = searchParams.get('view') as 'grid' | 'list' | 'master-detail';
    const tab = searchParams.get('tab') as 'catalog' | 'data';
    const q = searchParams.get('q');
    const formFactor = searchParams.get('formFactor');
    const manufacturer = searchParams.get('manufacturer');
    const maxPrice = searchParams.get('maxPrice');

    if (view && ['grid', 'list', 'master-detail'].includes(view)) {
      setActiveView(view);
    }
    if (tab && ['catalog', 'data'].includes(tab)) {
      setActiveTab(tab);
    }
    if (q !== null || formFactor || manufacturer || maxPrice) {
      setFilters({
        ...(q !== null && { searchQuery: q }),
        ...(formFactor && { formFactor }),
        ...(manufacturer && { manufacturer }),
        ...(maxPrice && { priceRange: parseInt(maxPrice, 10) }),
      });
    }
  }, []); // Run once on mount

  // Update URL when store changes
  useEffect(() => {
    const params = new URLSearchParams();
    params.set('view', activeView);
    params.set('tab', activeTab);
    if (filters.searchQuery) params.set('q', filters.searchQuery);
    if (filters.formFactor !== 'all') params.set('formFactor', filters.formFactor);
    if (filters.manufacturer !== 'all')
      params.set('manufacturer', filters.manufacturer);
    if (filters.priceRange !== 2500)
      params.set('maxPrice', filters.priceRange.toString());

    router.replace(`?${params.toString()}`, { scroll: false });
  }, [activeView, activeTab, filters, router]);
}
```

---

## Alternatives Considered

### Alternative 1: React Context API + useReducer

**Pros:**
- No external dependencies
- Standard React patterns
- Well-understood by React developers

**Cons:**
- Verbose boilerplate (provider, context, reducer, actions)
- Performance issues with large state (all consumers re-render on any state change)
- No built-in persistence middleware
- Difficult to test in isolation

**Why Rejected:**
The Context API would require careful optimization (splitting contexts) to avoid re-render issues. With 10+ state fields and multiple views, this becomes complex and error-prone.

---

### Alternative 2: Redux Toolkit

**Pros:**
- Industry standard for complex state
- Excellent DevTools
- Strong TypeScript support
- Mature ecosystem

**Cons:**
- Heavy dependency (larger bundle size)
- More boilerplate than Zustand (slices, reducers, actions)
- Overkill for this use case (no async middleware needed, React Query handles server state)
- Steeper learning curve for new contributors

**Why Rejected:**
Redux is designed for application-wide state with complex async flows. Our catalog state is localized to one feature, and React Query already handles server state. Zustand provides 90% of Redux benefits with 10% of the complexity.

---

### Alternative 3: Jotai (Atomic State)

**Pros:**
- Minimal boilerplate
- Atomic state updates (fine-grained reactivity)
- Built-in persistence utilities
- Small bundle size

**Cons:**
- Less familiar to most developers (newer library)
- Atom composition can become complex
- Harder to visualize full state shape
- Limited DevTools compared to Redux/Zustand

**Why Rejected:**
While Jotai is excellent for atomic state, our catalog views benefit from a centralized store where the state shape is clear. The learning curve and less mature ecosystem make it riskier for this project.

---

### Alternative 4: Component State (useState + Props)

**Pros:**
- No external dependencies
- Simple for small components
- Colocated with component logic

**Cons:**
- Prop drilling nightmare (5+ levels deep)
- State spread across multiple components
- No persistence out of the box
- Difficult to sync with URL params
- Hard to test

**Why Rejected:**
With state needed in multiple sibling components (filters, views, dialogs), prop drilling would become unmanageable. A shared store is essential.

---

## Decision Rationale

### Why Zustand Wins

**1. Simplicity & Developer Experience**
- Minimal boilerplate: One store file, no providers, no context
- Simple API: `useCatalogStore()` hook works anywhere
- TypeScript-first design with excellent inference

**2. Performance**
- Fine-grained subscriptions: Components only re-render when their selected state changes
- No provider wrapping required (unlike Context)
- Efficient shallow comparisons out of the box

**3. Persistence**
- Built-in `persist` middleware for localStorage
- Configurable partialize function (don't persist dialogs, do persist filters)
- Works seamlessly with SSR (Next.js)

**4. Testability**
- Store is plain JavaScript object, easy to mock
- Actions are pure functions
- No React context required for tests

**5. Bundle Size**
- ~1KB gzipped (vs. Redux ~9KB)
- No peer dependencies beyond React

**6. Existing Patterns**
- Deal Brain already uses React Query for server state (separation of concerns)
- Zustand complements this pattern perfectly
- No state management conflicts

---

## Consequences

### Positive

✅ **Simple mental model:** One store for catalog UI state, React Query for server data
✅ **Fast development:** No boilerplate, immediate productivity
✅ **Performant:** Only components using specific state slice re-render
✅ **Testable:** Store logic isolated, easy to unit test
✅ **Maintainable:** Clear state shape, predictable updates
✅ **Persistent:** Filters and view preferences survive page refresh

### Negative

⚠️ **New dependency:** Team must learn Zustand (mitigated: simple API, 10-minute onboarding)
⚠️ **Less mature DevTools:** Not as robust as Redux DevTools (acceptable: simple state tree)
⚠️ **Global store:** Potential for abuse if not disciplined (mitigated: clear guidelines)

### Neutral

➖ **Not application-wide:** This store is catalog-specific, not global app state
➖ **URL sync requires custom hook:** Not automatic (acceptable: explicit is better)

---

## Implementation Guidelines

### Best Practices

1. **Colocate selectors with components:**
   ```typescript
   // In component file
   const activeView = useCatalogStore((state) => state.activeView);
   const setActiveView = useCatalogStore((state) => state.setActiveView);
   ```

2. **Use custom hooks for common patterns:**
   ```typescript
   export function useFilters() {
     return useCatalogStore((state) => ({
       filters: state.filters,
       setFilters: state.setFilters,
       clearFilters: state.clearFilters,
     }));
   }
   ```

3. **Test store logic in isolation:**
   ```typescript
   import { renderHook, act } from '@testing-library/react';
   import { useCatalogStore } from '@/stores/catalog-store';

   test('toggleCompare adds and removes listing', () => {
     const { result } = renderHook(() => useCatalogStore());

     act(() => {
       result.current.toggleCompare(1);
     });
     expect(result.current.compareSelections).toEqual([1]);

     act(() => {
       result.current.toggleCompare(1);
     });
     expect(result.current.compareSelections).toEqual([]);
   });
   ```

4. **Don't put server data in Zustand:**
   ```typescript
   // ❌ Bad: Duplicating server state
   setListings: (listings) => set({ listings });

   // ✅ Good: Use React Query
   const { data: listings } = useQuery(['listings'], fetchListings);
   ```

---

## Monitoring & Validation

### Success Criteria (Post-Implementation)

- [ ] All catalog state updates trigger correct re-renders
- [ ] Filter changes update URL params within 200ms
- [ ] localStorage persists view preferences across sessions
- [ ] No unnecessary re-renders (verify with React DevTools Profiler)
- [ ] Store tests achieve 90%+ coverage

### Performance Benchmarks

- State update latency: <5ms (measured in DevTools)
- Re-render count: Only affected components (not entire tree)
- Bundle size impact: <5KB (Zustand + custom store code)

---

## References

- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Next.js State Management Guide](https://nextjs.org/docs/app/building-your-application/data-fetching/caching)
- [PRD: Listings Catalog View Revamp](../../project_plans/requests/listings-revamp/PRD.md)

---

## Revision History

| Version | Date       | Author      | Changes                          |
| ------- | ---------- | ----------- | -------------------------------- |
| 1.0     | 2025-10-06 | Claude Code | Initial decision document        |

---

**Decision Status:** ✅ Accepted
**Implementation Status:** 🟡 Pending (Phase 1)
