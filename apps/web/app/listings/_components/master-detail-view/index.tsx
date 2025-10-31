'use client'

import React, { useMemo } from 'react'
import { MasterList } from './master-list'
import { DetailPanel } from './detail-panel'
import { CompareDrawer } from './compare-drawer'
import { MasterDetailSkeleton } from './master-detail-skeleton'
import { NoFilterResultsEmptyState } from '@/components/ui/empty-state'
import { useCatalogStore } from '@/stores/catalog-store'
import type { ListingRow } from '@/components/listings/listings-table'

interface MasterDetailViewProps {
  listings: ListingRow[]
  isLoading?: boolean
  highlightedId?: number | null
}

export const MasterDetailView = React.memo(function MasterDetailView({
  listings,
  isLoading,
  highlightedId
}: MasterDetailViewProps) {
  const { selectedListingId, compareSelections } = useCatalogStore()

  // Sort by adjusted $/MT (ascending - best value first)
  const sortedListings = useMemo(() => {
    return [...listings].sort((a, b) => {
      const aMetric = a.dollar_per_cpu_mark_multi_adjusted ?? Infinity
      const bMetric = b.dollar_per_cpu_mark_multi_adjusted ?? Infinity
      return aMetric - bMetric
    })
  }, [listings])

  // Get selected listing
  const selectedListing = useMemo(() => {
    if (!selectedListingId) return sortedListings[0]
    return sortedListings.find((l) => l.id === selectedListingId) || sortedListings[0]
  }, [selectedListingId, sortedListings])

  // Get compared listings
  const comparedListings = useMemo(() => {
    return sortedListings.filter((l) => compareSelections.includes(l.id))
  }, [sortedListings, compareSelections])

  if (isLoading) {
    return <MasterDetailSkeleton />
  }

  if (sortedListings.length === 0) {
    return <NoFilterResultsEmptyState />
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-10">
        {/* Master List - Left Panel */}
        <div className="lg:col-span-4">
          <MasterList listings={sortedListings} highlightedId={highlightedId} />
        </div>

        {/* Detail Panel - Right Panel */}
        <div className="lg:col-span-6">
          <DetailPanel listing={selectedListing} />
        </div>
      </div>

      {/* Compare Drawer */}
      <CompareDrawer listings={comparedListings} />
    </div>
  )
})
