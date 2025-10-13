'use client'

import React, { useMemo } from 'react'
import { ListingsFilters } from './listings-filters'
import { ViewSwitcher } from './view-switcher'
import { GridView } from './grid-view'
import { DenseListView } from './dense-list-view'
import { MasterDetailView } from './master-detail-view'
import { useCatalogStore } from '@/stores/catalog-store'
import { ErrorBoundary } from '@/components/error-boundary'
import type { ListingRow } from '@/components/listings/listings-table'

interface CatalogTabProps {
  listings: ListingRow[]
  isLoading?: boolean
  onAddListing: () => void
}

export const CatalogTab = React.memo(function CatalogTab({
  listings,
  isLoading,
  onAddListing
}: CatalogTabProps) {
  const { activeView, filters } = useCatalogStore()

  // Filter listings client-side
  const filteredListings = useMemo(() => {
    if (!listings) return []

    return listings.filter((listing) => {
      // Search filter
      if (filters.searchQuery) {
        const term = filters.searchQuery.toLowerCase()
        const title = listing.title?.toLowerCase() || ''
        const cpuName = listing.cpu?.name?.toLowerCase() || ''
        if (!title.includes(term) && !cpuName.includes(term)) {
          return false
        }
      }

      // Form factor filter
      if (filters.formFactor !== 'all' && listing.form_factor !== filters.formFactor) {
        return false
      }

      // Manufacturer filter
      if (filters.manufacturer !== 'all' && listing.manufacturer !== filters.manufacturer) {
        return false
      }

      // Price range filter
      const price = listing.adjusted_price_usd ?? listing.price_usd ?? 0
      if (price > filters.priceRange) {
        return false
      }

      return true
    })
  }, [listings, filters])

  return (
    <div className="space-y-4">
      {/* Filters and View Switcher */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex-1">
          <ListingsFilters />
        </div>
        <ViewSwitcher />
      </div>

      {/* Active View */}
      {activeView === 'grid' && (
        <ErrorBoundary>
          <GridView
            listings={filteredListings}
            isLoading={isLoading}
            onAddListing={onAddListing}
          />
        </ErrorBoundary>
      )}
      {activeView === 'list' && (
        <ErrorBoundary>
          <DenseListView
            listings={filteredListings}
            isLoading={isLoading}
          />
        </ErrorBoundary>
      )}
      {activeView === 'master-detail' && (
        <ErrorBoundary>
          <MasterDetailView
            listings={filteredListings}
            isLoading={isLoading}
          />
        </ErrorBoundary>
      )}
    </div>
  )
})
