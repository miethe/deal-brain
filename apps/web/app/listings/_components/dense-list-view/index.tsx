'use client'

import React, { useMemo } from 'react'
import { DenseTable } from './dense-table'
import type { ListingRow } from '@/components/listings/listings-table'

interface DenseListViewProps {
  listings: ListingRow[]
  isLoading?: boolean
}

export const DenseListView = React.memo(function DenseListView({
  listings,
  isLoading
}: DenseListViewProps) {
  // Sort by adjusted $/MT (ascending - best value first)
  const sortedListings = useMemo(() => {
    return [...listings].sort((a, b) => {
      const aMetric = a.dollar_per_cpu_mark_multi_adjusted ?? Infinity
      const bMetric = b.dollar_per_cpu_mark_multi_adjusted ?? Infinity
      return aMetric - bMetric
    })
  }, [listings])

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <div
            key={i}
            className="h-16 w-full animate-pulse rounded-lg bg-muted"
          />
        ))}
      </div>
    )
  }

  if (sortedListings.length === 0) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center space-y-4 rounded-lg border border-dashed p-8">
        <p className="text-sm text-muted-foreground">
          No listings match your filters
        </p>
      </div>
    )
  }

  return <DenseTable listings={sortedListings} />
})
