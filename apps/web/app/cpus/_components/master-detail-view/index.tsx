'use client'

import React, { useMemo } from 'react'
import { MasterList } from './master-list'
import { DetailPanel } from './detail-panel'
import { CompareDrawer } from './compare-drawer'
import { MasterDetailSkeleton } from './master-detail-skeleton'
import { NoFilterResultsEmptyState } from '@/components/ui/empty-state'
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store'
import type { CPURecord } from '@/types/cpus'

interface MasterDetailViewProps {
  cpus: CPURecord[]
  isLoading?: boolean
}

export const MasterDetailView = React.memo(function MasterDetailView({
  cpus,
  isLoading
}: MasterDetailViewProps) {
  const { selectedCPUId, compareSelections } = useCPUCatalogStore()

  // Sort by performance value (ascending - best value first)
  const sortedCPUs = useMemo(() => {
    return [...cpus].sort((a, b) => {
      const aMetric = a.dollar_per_mark_multi ?? Infinity
      const bMetric = b.dollar_per_mark_multi ?? Infinity
      return aMetric - bMetric
    })
  }, [cpus])

  // Get selected CPU
  const selectedCPU = useMemo(() => {
    if (!selectedCPUId) return sortedCPUs[0]
    return sortedCPUs.find((cpu) => cpu.id === selectedCPUId) || sortedCPUs[0]
  }, [selectedCPUId, sortedCPUs])

  // Get compared CPUs
  const comparedCPUs = useMemo(() => {
    return sortedCPUs.filter((cpu) => compareSelections.includes(cpu.id))
  }, [sortedCPUs, compareSelections])

  if (isLoading) {
    return <MasterDetailSkeleton />
  }

  if (sortedCPUs.length === 0) {
    return <NoFilterResultsEmptyState />
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-10">
        {/* Master List - Left Panel */}
        <div className="lg:col-span-4">
          <MasterList cpus={sortedCPUs} />
        </div>

        {/* Detail Panel - Right Panel */}
        <div className="lg:col-span-6">
          <DetailPanel cpu={selectedCPU} />
        </div>
      </div>

      {/* Compare Drawer */}
      <CompareDrawer cpus={comparedCPUs} />
    </div>
  )
})
