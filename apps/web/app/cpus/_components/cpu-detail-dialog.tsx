'use client'

import React from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store'
import { useCPUs, useCPUDetail } from '@/hooks/use-cpus'
import { DetailPanel } from './master-detail-view/detail-panel'

/**
 * CPU Detail Dialog Component
 *
 * Modal dialog that displays detailed CPU information, analytics, and listings.
 * Opens when clicking CPU cards/rows in Grid, List, or Master-Detail views.
 *
 * Features:
 * - Full-screen modal (max-width 4xl, max-height 90vh)
 * - Scrollable content using ScrollArea
 * - Reuses DetailPanel component from master-detail view
 * - Handles loading and error states
 * - Keyboard accessible (ESC closes, focus trapped)
 * - Screen reader accessible
 *
 * State Management:
 * - Controlled via cpu-catalog-store (detailsDialogOpen, detailsDialogCPUId)
 * - Fetches CPU data using React Query hooks (useCPUs, useCPUDetail)
 *
 * @example
 * ```tsx
 * // In catalog-tab.tsx
 * <CPUDetailDialog />
 * ```
 */
export const CPUDetailDialog = React.memo(function CPUDetailDialog() {
  const { detailsDialogOpen, detailsDialogCPUId, closeDetailsDialog } = useCPUCatalogStore()

  // Fetch all CPUs to get basic info for selected CPU
  const { data: cpus } = useCPUs(true)

  // Fetch detailed info for selected CPU
  const {
    data: cpuDetail,
    isLoading: isLoadingDetail,
    isError: isErrorDetail
  } = useCPUDetail(detailsDialogCPUId)

  // Find the selected CPU in the list
  const selectedCPU = React.useMemo(() => {
    if (!cpus || !detailsDialogCPUId) return undefined
    return cpus.find(cpu => cpu.id === detailsDialogCPUId)
  }, [cpus, detailsDialogCPUId])

  return (
    <Dialog open={detailsDialogOpen} onOpenChange={closeDetailsDialog}>
      <DialogContent className="max-w-4xl max-h-[90vh] p-0">
        <DialogHeader className="px-6 pt-6 pb-0">
          <DialogTitle className="sr-only">
            CPU Details: {selectedCPU?.name || 'Loading...'}
          </DialogTitle>
        </DialogHeader>
        <ScrollArea className="max-h-[calc(90vh-4rem)] px-6 pb-6">
          <DetailPanel
            cpu={selectedCPU}
            cpuDetail={cpuDetail}
            isLoadingDetail={isLoadingDetail}
            isErrorDetail={isErrorDetail}
          />
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
})
