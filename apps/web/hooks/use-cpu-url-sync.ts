import { useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useCPUCatalogStore, ViewMode, TabMode } from '@/stores/cpu-catalog-store';
import { useDebouncedCallback } from 'use-debounce';

/**
 * CPU Catalog URL State Synchronization Hook
 *
 * Synchronizes Zustand CPU catalog store state with URL parameters for:
 * - Shareable URLs with filters and view preferences
 * - Browser back/forward navigation
 * - Page refresh state preservation
 * - Deep linking to CPU detail modals from listings page
 *
 * URL Parameters:
 * - view: 'grid' | 'list' | 'master-detail'
 * - tab: 'catalog' | 'data'
 * - q: search query
 * - manufacturer: comma-separated manufacturers (e.g., 'Intel,AMD')
 * - socket: comma-separated sockets (e.g., 'AM4,LGA1700')
 * - cores: core range as "min-max" (e.g., '4-16')
 * - tdp: TDP range as "min-max" (e.g., '65-125')
 * - year: year range as "min-max" (e.g., '2020-2024')
 * - igpu: 'true' | 'false' (has integrated GPU)
 * - minMark: minimum PassMark score
 * - perfRating: performance rating filter
 * - cpuId: CPU ID to display in modal (requires openModal=true)
 * - openModal: 'true' to open CPU detail modal on page load
 */

const DEFAULTS = {
  view: 'grid' as ViewMode,
  tab: 'catalog' as TabMode,
  searchQuery: '',
  manufacturer: [] as string[],
  socket: [] as string[],
  coreRange: [2, 64] as [number, number],
  tdpRange: [15, 280] as [number, number],
  yearRange: null as [number, number] | null,
  hasIGPU: null as boolean | null,
  minPassMark: null as number | null,
  performanceRating: null as string | null,
};

export function useCPUUrlSync() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hasHydrated = useRef(false);

  // Get all store state
  const activeView = useCPUCatalogStore((state) => state.activeView);
  const activeTab = useCPUCatalogStore((state) => state.activeTab);
  const filters = useCPUCatalogStore((state) => state.filters);

  // Get store actions
  const setActiveView = useCPUCatalogStore((state) => state.setActiveView);
  const setActiveTab = useCPUCatalogStore((state) => state.setActiveTab);
  const setFilters = useCPUCatalogStore((state) => state.setFilters);
  const openDetailsDialog = useCPUCatalogStore((state) => state.openDetailsDialog);

  // Hydrate store from URL on mount
  useEffect(() => {
    if (hasHydrated.current) return;
    hasHydrated.current = true;

    // Parse and validate URL params
    const viewParam = searchParams.get('view');
    const tabParam = searchParams.get('tab');
    const qParam = searchParams.get('q');
    const manufacturerParam = searchParams.get('manufacturer');
    const socketParam = searchParams.get('socket');
    const coresParam = searchParams.get('cores');
    const tdpParam = searchParams.get('tdp');
    const yearParam = searchParams.get('year');
    const igpuParam = searchParams.get('igpu');
    const minMarkParam = searchParams.get('minMark');
    const perfRatingParam = searchParams.get('perfRating');

    // Deep link params for modal opening
    const cpuIdParam = searchParams.get('cpuId');
    const openModalParam = searchParams.get('openModal');

    // Validate and apply view
    if (viewParam && ['grid', 'list', 'master-detail'].includes(viewParam)) {
      setActiveView(viewParam as ViewMode);
    }

    // Validate and apply tab
    if (tabParam && ['catalog', 'data'].includes(tabParam)) {
      setActiveTab(tabParam as TabMode);
    }

    // Build filter updates object
    const urlFilters: Partial<typeof filters> = {};

    // Search query
    if (qParam !== null) {
      urlFilters.searchQuery = qParam;
    }

    // Manufacturer (comma-separated array)
    if (manufacturerParam !== null) {
      urlFilters.manufacturer = manufacturerParam
        .split(',')
        .filter((m) => m.trim().length > 0);
    }

    // Socket (comma-separated array)
    if (socketParam !== null) {
      urlFilters.socket = socketParam
        .split(',')
        .filter((s) => s.trim().length > 0);
    }

    // Core range (min-max format)
    if (coresParam !== null) {
      const [min, max] = coresParam.split('-').map((n) => parseInt(n, 10));
      if (!isNaN(min) && !isNaN(max) && min >= 0 && max <= 128 && min <= max) {
        urlFilters.coreRange = [min, max];
      }
    }

    // TDP range (min-max format)
    if (tdpParam !== null) {
      const [min, max] = tdpParam.split('-').map((n) => parseInt(n, 10));
      if (!isNaN(min) && !isNaN(max) && min >= 0 && max <= 500 && min <= max) {
        urlFilters.tdpRange = [min, max];
      }
    }

    // Year range (min-max format)
    if (yearParam !== null) {
      const [min, max] = yearParam.split('-').map((n) => parseInt(n, 10));
      if (!isNaN(min) && !isNaN(max) && min >= 2000 && max <= 2100 && min <= max) {
        urlFilters.yearRange = [min, max];
      }
    }

    // Has iGPU (boolean)
    if (igpuParam === 'true') {
      urlFilters.hasIGPU = true;
    } else if (igpuParam === 'false') {
      urlFilters.hasIGPU = false;
    }

    // Min PassMark score
    if (minMarkParam !== null) {
      const mark = parseInt(minMarkParam, 10);
      if (!isNaN(mark) && mark >= 0) {
        urlFilters.minPassMark = mark;
      }
    }

    // Performance rating
    if (perfRatingParam !== null && perfRatingParam.length > 0) {
      urlFilters.performanceRating = perfRatingParam;
    }

    // Apply filter updates if any
    if (Object.keys(urlFilters).length > 0) {
      setFilters(urlFilters);
    }

    // Handle deep link to CPU detail modal
    if (cpuIdParam && openModalParam === 'true') {
      const id = parseInt(cpuIdParam, 10);
      if (!isNaN(id)) {
        // Open modal with CPU ID
        openDetailsDialog(id);

        // Clean up URL (remove query params after opening modal)
        // This keeps the URL clean and avoids re-triggering on subsequent renders
        const url = new URL(window.location.href);
        url.searchParams.delete('cpuId');
        url.searchParams.delete('openModal');
        router.replace(url.pathname + url.search, { scroll: false });
      }
    }
  }, [searchParams, setActiveView, setActiveTab, setFilters, openDetailsDialog, router]);

  // Update URL when store changes (debounced to avoid history pollution)
  const updateUrl = useDebouncedCallback(() => {
    const params = new URLSearchParams();

    // Add non-default params only to keep URLs clean

    // View mode
    if (activeView !== DEFAULTS.view) {
      params.set('view', activeView);
    }

    // Active tab
    if (activeTab !== DEFAULTS.tab) {
      params.set('tab', activeTab);
    }

    // Search query
    if (filters.searchQuery && filters.searchQuery !== DEFAULTS.searchQuery) {
      params.set('q', filters.searchQuery);
    }

    // Manufacturer filter
    if (filters.manufacturer.length > 0) {
      params.set('manufacturer', filters.manufacturer.join(','));
    }

    // Socket filter
    if (filters.socket.length > 0) {
      params.set('socket', filters.socket.join(','));
    }

    // Core range (only if different from default)
    if (
      filters.coreRange[0] !== DEFAULTS.coreRange[0] ||
      filters.coreRange[1] !== DEFAULTS.coreRange[1]
    ) {
      params.set('cores', `${filters.coreRange[0]}-${filters.coreRange[1]}`);
    }

    // TDP range (only if different from default)
    if (
      filters.tdpRange[0] !== DEFAULTS.tdpRange[0] ||
      filters.tdpRange[1] !== DEFAULTS.tdpRange[1]
    ) {
      params.set('tdp', `${filters.tdpRange[0]}-${filters.tdpRange[1]}`);
    }

    // Year range
    if (filters.yearRange !== null) {
      params.set('year', `${filters.yearRange[0]}-${filters.yearRange[1]}`);
    }

    // Has iGPU
    if (filters.hasIGPU !== null) {
      params.set('igpu', String(filters.hasIGPU));
    }

    // Min PassMark
    if (filters.minPassMark !== null) {
      params.set('minMark', String(filters.minPassMark));
    }

    // Performance rating
    if (filters.performanceRating !== null) {
      params.set('perfRating', filters.performanceRating);
    }

    // Build new URL
    const queryString = params.toString();
    const newUrl = queryString ? `/cpus?${queryString}` : '/cpus';

    // Update URL without navigation (use replace to avoid history pollution)
    router.replace(newUrl, { scroll: false });
  }, 300);

  // Trigger URL update when store state changes
  useEffect(() => {
    if (!hasHydrated.current) return;
    updateUrl();
  }, [activeView, activeTab, filters, updateUrl]);

  return null;
}
