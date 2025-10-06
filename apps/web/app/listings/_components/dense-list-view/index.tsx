'use client'

import React, { useMemo } from 'react'
import { DenseTable } from './dense-table'
import { DenseTableSkeleton } from './dense-table-skeleton'
import { NoFilterResultsEmptyState } from '@/components/ui/empty-state'
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
    return <DenseTableSkeleton />
  }

  if (sortedListings.length === 0) {
    return <NoFilterResultsEmptyState />
  }

  return <DenseTable listings={sortedListings} />
})
