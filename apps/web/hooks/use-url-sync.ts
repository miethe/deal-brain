import { useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useCatalogStore, ViewMode, TabMode } from '@/stores/catalog-store';
import { useDebouncedCallback } from 'use-debounce';

/**
 * URL State Synchronization Hook
 *
 * Synchronizes Zustand catalog store state with URL parameters for:
 * - Shareable URLs
 * - Browser back/forward navigation
 * - Page refresh state preservation
 *
 * URL Parameters:
 * - view: 'grid' | 'list' | 'master-detail'
 * - tab: 'catalog' | 'data'
 * - q: search query
 * - formFactor: form factor filter
 * - manufacturer: manufacturer filter
 * - maxPrice: price range filter
 */
export function useUrlSync() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hasHydrated = useRef(false);

  const activeView = useCatalogStore((state) => state.activeView);
  const activeTab = useCatalogStore((state) => state.activeTab);
  const filters = useCatalogStore((state) => state.filters);

  const setActiveView = useCatalogStore((state) => state.setActiveView);
  const setActiveTab = useCatalogStore((state) => state.setActiveTab);
  const setFilters = useCatalogStore((state) => state.setFilters);

  // Hydrate store from URL on mount
  useEffect(() => {
    if (hasHydrated.current) return;
    hasHydrated.current = true;

    const urlView = searchParams.get('view') as ViewMode;
    const urlTab = searchParams.get('tab') as TabMode;
    const urlQuery = searchParams.get('q');
    const urlFormFactor = searchParams.get('formFactor');
    const urlManufacturer = searchParams.get('manufacturer');
    const urlMaxPrice = searchParams.get('maxPrice');

    // Validate and apply URL params
    if (urlView && ['grid', 'list', 'master-detail'].includes(urlView)) {
      setActiveView(urlView);
    }

    if (urlTab && ['catalog', 'data'].includes(urlTab)) {
      setActiveTab(urlTab);
    }

    const filterUpdates: Partial<typeof filters> = {};

    if (urlQuery !== null) {
      filterUpdates.searchQuery = urlQuery;
    }

    if (urlFormFactor !== null) {
      filterUpdates.formFactor = urlFormFactor;
    }

    if (urlManufacturer !== null) {
      filterUpdates.manufacturer = urlManufacturer;
    }

    if (urlMaxPrice !== null) {
      const priceNum = parseInt(urlMaxPrice, 10);
      if (!isNaN(priceNum)) {
        filterUpdates.priceRange = priceNum;
      }
    }

    if (Object.keys(filterUpdates).length > 0) {
      setFilters(filterUpdates);
    }
  }, [searchParams, setActiveView, setActiveTab, setFilters]);

  // Update URL when store changes (debounced to avoid excessive pushes)
  const updateUrl = useDebouncedCallback(() => {
    const params = new URLSearchParams();

    // Only add params if they differ from defaults
    if (activeView !== 'grid') {
      params.set('view', activeView);
    }

    if (activeTab !== 'catalog') {
      params.set('tab', activeTab);
    }

    if (filters.searchQuery) {
      params.set('q', filters.searchQuery);
    }

    if (filters.formFactor !== 'all') {
      params.set('formFactor', filters.formFactor);
    }

    if (filters.manufacturer !== 'all') {
      params.set('manufacturer', filters.manufacturer);
    }

    if (filters.priceRange !== 10000) {
      params.set('maxPrice', filters.priceRange.toString());
    }

    const newUrl = params.toString() ? `?${params.toString()}` : '/listings';

    // Use replace to avoid polluting browser history
    router.replace(newUrl, { scroll: false });
  }, 300);

  // Trigger URL update when store state changes
  useEffect(() => {
    if (!hasHydrated.current) return;
    updateUrl();
  }, [activeView, activeTab, filters, updateUrl]);
}
