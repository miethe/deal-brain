'use client'

import React, { useMemo } from 'react'
import { CPUTable } from './cpu-table'
import { CPUTableSkeleton } from './cpu-table-skeleton'
import { NoFilterResultsEmptyState } from '@/components/ui/empty-state'
import type { CPURecord } from '@/types/cpus'

interface ListViewProps {
  cpus: CPURecord[]
  isLoading?: boolean
}

/**
 * CPU List View Component
 *
 * Dense table view for CPU catalog with virtual scrolling, sorting, and keyboard navigation.
 * Features:
 * - Default sort by Multi-Thread CPU Mark (descending - highest performance first)
 * - Virtual scrolling for large datasets via @tanstack/react-virtual
 * - Sortable columns (name, manufacturer, cores, TDP, PassMark scores)
 * - Row selection and keyboard navigation
 * - Empty state for no results
 * - Loading skeleton
 */
export const ListView = React.memo(function ListView({
  cpus,
  isLoading
}: ListViewProps) {
  // Default sort by Multi-Thread CPU Mark (descending - highest performance first)
  const sortedCPUs = useMemo(() => {
    return [...cpus].sort((a, b) => {
      const aMetric = a.cpu_mark_multi ?? -Infinity
      const bMetric = b.cpu_mark_multi ?? -Infinity
      return bMetric - aMetric // Descending order
    })
  }, [cpus])

  if (isLoading) {
    return <CPUTableSkeleton />
  }

  if (sortedCPUs.length === 0) {
    return <NoFilterResultsEmptyState />
  }

  return <CPUTable cpus={sortedCPUs} />
})
