import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * CPU Catalog View State Management
 *
 * This store manages the state for the CPU Catalog View, including:
 * - Active view mode (grid, list, master-detail)
 * - Active tab (catalog, data)
 * - Filter state (search, manufacturer, socket, cores, TDP, performance)
 * - Compare selections for Master-Detail view
 * - Dialog states for details and quick edit
 */

export type ViewMode = 'grid' | 'list' | 'master-detail';
export type TabMode = 'catalog' | 'data';

export interface CPUFilterState {
  searchQuery: string;                    // Search CPU name
  manufacturer: string[];                 // AMD, Intel, etc.
  socket: string[];                       // AM4, LGA1700, etc.
  coreRange: [number, number];            // Min/max cores (e.g., [2, 64])
  tdpRange: [number, number];             // Min/max TDP (e.g., [15, 280])
  yearRange: [number, number] | null;     // Release year range
  hasIGPU: boolean | null;                // null = all, true = only with iGPU
  minPassMark: number | null;             // Minimum PassMark score
  performanceRating: string | null;       // 'excellent' | 'good' | 'fair' | null
}

export interface CPUCatalogState {
  // View mode
  activeView: ViewMode;
  setActiveView: (view: ViewMode) => void;

  // Active tab
  activeTab: TabMode;
  setActiveTab: (tab: TabMode) => void;

  // Filters
  filters: CPUFilterState;
  setFilters: (filters: Partial<CPUFilterState>) => void;
  clearFilters: () => void;

  // Compare selections (for Master-Detail view)
  compareSelections: number[]; // CPU IDs
  toggleCompare: (id: number) => void;
  clearCompare: () => void;

  // Selected CPU for detail panel
  selectedCPUId: number | null;
  setSelectedCPU: (id: number | null) => void;

  // Dialog states
  detailsDialogOpen: boolean;
  detailsDialogCPUId: number | null;
  openDetailsDialog: (id: number) => void;
  closeDetailsDialog: () => void;

  quickEditDialogOpen: boolean;
  quickEditDialogCPUId: number | null;
  openQuickEditDialog: (id: number) => void;
  closeQuickEditDialog: () => void;
}

const DEFAULT_FILTERS: CPUFilterState = {
  searchQuery: '',
  manufacturer: [],
  socket: [],
  coreRange: [2, 64],
  tdpRange: [15, 280],
  yearRange: null,
  hasIGPU: null,
  minPassMark: null,
  performanceRating: null,
};

export const useCPUCatalogStore = create<CPUCatalogState>()(
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
            ? state.compareSelections.filter((cpuId) => cpuId !== id)
            : [...state.compareSelections, id],
        })),
      clearCompare: () => set({ compareSelections: [] }),

      // Selected CPU for detail panel
      selectedCPUId: null,
      setSelectedCPU: (id) => set({ selectedCPUId: id }),

      // Dialog states
      detailsDialogOpen: false,
      detailsDialogCPUId: null,
      openDetailsDialog: (id) =>
        set({ detailsDialogOpen: true, detailsDialogCPUId: id }),
      closeDetailsDialog: () =>
        set({ detailsDialogOpen: false, detailsDialogCPUId: null }),

      quickEditDialogOpen: false,
      quickEditDialogCPUId: null,
      openQuickEditDialog: (id) =>
        set({ quickEditDialogOpen: true, quickEditDialogCPUId: id }),
      closeQuickEditDialog: () =>
        set({ quickEditDialogOpen: false, quickEditDialogCPUId: null }),
    }),
    {
      name: 'cpu-catalog-store',
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
  const filters = useCPUCatalogStore((state) => state.filters);
  const setFilters = useCPUCatalogStore((state) => state.setFilters);
  const clearFilters = useCPUCatalogStore((state) => state.clearFilters);

  return { filters, setFilters, clearFilters };
};

/**
 * Custom hook for accessing compare state
 */
export const useCompare = () => {
  const compareSelections = useCPUCatalogStore((state) => state.compareSelections);
  const toggleCompare = useCPUCatalogStore((state) => state.toggleCompare);
  const clearCompare = useCPUCatalogStore((state) => state.clearCompare);

  return { compareSelections, toggleCompare, clearCompare };
};
