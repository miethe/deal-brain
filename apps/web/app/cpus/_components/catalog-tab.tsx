'use client'

import React from 'react'
import { CPUFilters } from './cpu-filters'
import { CPUSortControls } from './cpu-sort-controls'
import { ViewSwitcher } from './view-switcher'
import { GridView } from './grid-view'
import { ListView } from './list-view'
import { MasterDetailView } from './master-detail-view'
import { CPUDetailDialog } from './cpu-detail-dialog'
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store'
import { ErrorBoundary } from '@/components/error-boundary'
import { CPURecord } from '@/types/cpus'

interface CatalogTabProps {
  cpus: CPURecord[]
  isLoading?: boolean
}

/**
 * CPU Catalog Tab Component
 *
 * Main container for CPU catalog views with filters, sorting, and view mode switching.
 * Integrates:
 * - CPUFilters component for search and filtering
 * - CPUSortControls for sorting configuration
 * - ViewSwitcher for toggling between Grid/List/Master-Detail
 * - Active view component (Grid, List, or Master-Detail)
 *
 * Features:
 * - Server-side filtering and sorting via API
 * - View mode persistence via cpu-catalog-store
 * - Error boundary for graceful error handling
 * - Responsive layout
 */
export const CatalogTab = React.memo(function CatalogTab({
  cpus,
  isLoading
}: CatalogTabProps) {
  const activeView = useCPUCatalogStore((state) => state.activeView)

  return (
    <div className="space-y-4">
      {/* Filters */}
      <CPUFilters />

      {/* Sort Controls and View Switcher */}
      <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4">
        <CPUSortControls />
        <ViewSwitcher />
      </div>

      {/* Active View */}
      {activeView === 'grid' && (
        <ErrorBoundary>
          <GridView
            cpus={cpus}
            isLoading={isLoading}
          />
        </ErrorBoundary>
      )}
      {activeView === 'list' && (
        <ErrorBoundary>
          <ListView
            cpus={cpus}
            isLoading={isLoading}
          />
        </ErrorBoundary>
      )}
      {activeView === 'master-detail' && (
        <ErrorBoundary>
          <MasterDetailView
            cpus={cpus}
            isLoading={isLoading}
          />
        </ErrorBoundary>
      )}

      {/* CPU Detail Dialog */}
      <CPUDetailDialog />
    </div>
  )
})
