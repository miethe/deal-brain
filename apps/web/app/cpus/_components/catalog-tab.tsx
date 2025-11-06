'use client'

import React from 'react'
import { CPUFilters } from './cpu-filters'
import { ViewSwitcher } from './view-switcher'
import { GridView } from './grid-view'
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
 * Main container for CPU catalog views with filters and view mode switching.
 * Integrates:
 * - CPUFilters component for search and filtering
 * - ViewSwitcher for toggling between Grid/List/Master-Detail
 * - Active view component (Grid, List, or Master-Detail)
 *
 * Features:
 * - Client-side filtering via cpu-filters
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

      {/* View Switcher */}
      <div className="flex items-center justify-end">
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
        <div className="rounded-lg border border-dashed border-muted-foreground/25 p-12 text-center">
          <p className="text-sm text-muted-foreground">
            List View - Coming in Phase 2 (FE-004)
          </p>
        </div>
      )}
      {activeView === 'master-detail' && (
        <div className="rounded-lg border border-dashed border-muted-foreground/25 p-12 text-center">
          <p className="text-sm text-muted-foreground">
            Master-Detail View - Coming in Phase 2 (FE-005)
          </p>
        </div>
      )}
    </div>
  )
})
