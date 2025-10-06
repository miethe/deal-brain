import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Catalog View State Management
 *
 * This store manages the state for the Listings Catalog View, including:
 * - Active view mode (grid, list, master-detail)
 * - Active tab (catalog, data)
 * - Filter state (search, form factor, manufacturer, price)
 * - Compare selections for Master-Detail view
 * - Dialog states for details and quick edit
 */

export type ViewMode = 'grid' | 'list' | 'master-detail';
export type TabMode = 'catalog' | 'data';

export interface FilterState {
  searchQuery: string;
  formFactor: string; // 'all' | specific form factor
  manufacturer: string; // 'all' | specific manufacturer
  priceRange: number; // max price in USD
}

export interface CatalogState {
  // View mode
  activeView: ViewMode;
  setActiveView: (view: ViewMode) => void;

  // Active tab
  activeTab: TabMode;
  setActiveTab: (tab: TabMode) => void;

  // Filters
  filters: FilterState;
  setFilters: (filters: Partial<FilterState>) => void;
  clearFilters: () => void;

  // Compare selections (for Master-Detail view)
  compareSelections: number[]; // listing IDs
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

const DEFAULT_FILTERS: FilterState = {
  searchQuery: '',
  formFactor: 'all',
  manufacturer: 'all',
  priceRange: 10000, // $10,000 max by default
};

export const useCatalogStore = create<CatalogState>()(
  persist(
    (set) => ({
      // View mode
      activeView: 'grid',
      setActiveView: (view) => set({ activeView: view }),

      // Active tab
      activeTab: 'catalog',
      setActiveTab: (tab) => set({ activeTab: tab }),

      // Filters
      filters: DEFAULT_FILTERS,
      setFilters: (partialFilters) =>
        set((state) => ({
          filters: { ...state.filters, ...partialFilters },
        })),
      clearFilters: () => set({ filters: DEFAULT_FILTERS }),

      // Compare selections
      compareSelections: [],
      toggleCompare: (id) =>
        set((state) => ({
          compareSelections: state.compareSelections.includes(id)
            ? state.compareSelections.filter((listingId) => listingId !== id)
            : [...state.compareSelections, id],
        })),
      clearCompare: () => set({ compareSelections: [] }),

      // Selected listing for detail panel
      selectedListingId: null,
      setSelectedListing: (id) => set({ selectedListingId: id }),

      // Dialog states
      detailsDialogOpen: false,
      detailsDialogListingId: null,
      openDetailsDialog: (id) =>
        set({ detailsDialogOpen: true, detailsDialogListingId: id }),
      closeDetailsDialog: () =>
        set({ detailsDialogOpen: false, detailsDialogListingId: null }),

      quickEditDialogOpen: false,
      quickEditDialogListingId: null,
      openQuickEditDialog: (id) =>
        set({ quickEditDialogOpen: true, quickEditDialogListingId: id }),
      closeQuickEditDialog: () =>
        set({ quickEditDialogOpen: false, quickEditDialogListingId: null }),
    }),
    {
      name: 'catalog-store',
      // Only persist view preferences, not temporary state
      partialize: (state) => ({
        activeView: state.activeView,
        activeTab: state.activeTab,
        filters: state.filters,
      }),
    }
  )
);

/**
 * Custom hook for accessing filter state
 */
export const useFilters = () => {
  const filters = useCatalogStore((state) => state.filters);
  const setFilters = useCatalogStore((state) => state.setFilters);
  const clearFilters = useCatalogStore((state) => state.clearFilters);

  return { filters, setFilters, clearFilters };
};

/**
 * Custom hook for accessing compare state
 */
export const useCompare = () => {
  const compareSelections = useCatalogStore((state) => state.compareSelections);
  const toggleCompare = useCatalogStore((state) => state.toggleCompare);
  const clearCompare = useCatalogStore((state) => state.clearCompare);

  return { compareSelections, toggleCompare, clearCompare };
};
