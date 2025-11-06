'use client'

import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  ChevronUp,
  ChevronDown,
  Eye
} from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store'
import type { CPURecord } from '@/types/cpus'
import {
  columns,
  type SortableColumn,
  getSortValue
} from './column-definitions'

interface CPUTableProps {
  cpus: CPURecord[]
}

/**
 * Virtualized CPU Table Component
 *
 * Features:
 * - Virtual scrolling for large datasets (@tanstack/react-virtual)
 * - Sortable columns with visual indicators
 * - Row selection and highlighting
 * - Keyboard navigation (Arrow keys, Enter)
 * - Sticky header with 64px row height
 * - Color-coded performance badges
 * - Responsive column widths
 */
export const CPUTable = React.memo(function CPUTable({
  cpus
}: CPUTableProps) {
  const { openDetailsDialog } = useCPUCatalogStore()
  const [selectedCPUId, setSelectedCPUId] = useState<number | null>(null)
  const [focusedIndex, setFocusedIndex] = useState<number>(-1)
  const tableContainerRef = useRef<HTMLDivElement>(null)

  // Sorting state (default: Multi-Thread CPU Mark descending)
  const [sortConfig, setSortConfig] = useState<{
    key: SortableColumn
    direction: 'asc' | 'desc'
  }>({
    key: 'cpu_mark_multi',
    direction: 'desc'
  })

  // Sort CPUs based on current sort configuration
  const sortedCPUs = useMemo(() => {
    return [...cpus].sort((a, b) => {
      const aValue = getSortValue(a, sortConfig.key)
      const bValue = getSortValue(b, sortConfig.key)

      if (aValue === bValue) return 0

      const comparison = aValue > bValue ? 1 : -1
      return sortConfig.direction === 'asc' ? comparison : -comparison
    })
  }, [cpus, sortConfig])

  // Virtual scrolling for large datasets
  const rowVirtualizer = useVirtualizer({
    count: sortedCPUs.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => 64, // 64px row height
    overscan: 5
  })

  // Handle column sort
  const handleSort = useCallback((key: SortableColumn) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        // Toggle direction if same column
        return {
          key,
          direction: prev.direction === 'asc' ? 'desc' : 'asc'
        }
      }
      // Default to descending for new column
      return {
        key,
        direction: 'desc'
      }
    })
  }, [])

  // Handle row click
  const handleRowClick = useCallback((cpuId: number, index: number) => {
    setSelectedCPUId(cpuId)
    setFocusedIndex(index)
  }, [])

  // Handle row double-click
  const handleRowDoubleClick = useCallback((cpuId: number) => {
    openDetailsDialog(cpuId)
  }, [openDetailsDialog])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return // Don't handle if focus is in input
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setFocusedIndex((prev) => {
            const newIndex = Math.min(prev + 1, sortedCPUs.length - 1)
            if (newIndex >= 0) {
              setSelectedCPUId(sortedCPUs[newIndex].id)
            }
            return newIndex
          })
          break
        case 'ArrowUp':
          e.preventDefault()
          setFocusedIndex((prev) => {
            const newIndex = Math.max(prev - 1, 0)
            if (newIndex >= 0) {
              setSelectedCPUId(sortedCPUs[newIndex].id)
            }
            return newIndex
          })
          break
        case 'Enter':
          if (focusedIndex >= 0) {
            e.preventDefault()
            openDetailsDialog(sortedCPUs[focusedIndex].id)
          }
          break
        case 'Escape':
          e.preventDefault()
          setFocusedIndex(-1)
          setSelectedCPUId(null)
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [focusedIndex, sortedCPUs, openDetailsDialog])

  // Get performance badge variant based on rating
  const getPerformanceVariant = (
    rating: string | null
  ): 'excellent' | 'good' | 'fair' | 'poor' | null => {
    if (!rating) return null
    return rating as 'excellent' | 'good' | 'fair' | 'poor'
  }

  // Get badge color classes based on variant
  const getBadgeClasses = (variant: 'excellent' | 'good' | 'fair' | 'poor' | null) => {
    switch (variant) {
      case 'excellent':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800'
      case 'good':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-950/30 dark:text-blue-400 border-blue-300 dark:border-blue-800'
      case 'fair':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-950/30 dark:text-amber-400 border-amber-300 dark:border-amber-800'
      case 'poor':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-950/30 dark:text-gray-400 border-gray-300 dark:border-gray-800'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-950/30 dark:text-gray-400 border-gray-300 dark:border-gray-800'
    }
  }

  // Render sort indicator
  const renderSortIndicator = (columnKey: string) => {
    const column = columns.find((c) => c.key === columnKey)
    if (!column?.sortable || !column.sortKey) return null

    const isActive = sortConfig.key === column.sortKey

    return (
      <span className="ml-1 inline-flex">
        {isActive ? (
          sortConfig.direction === 'asc' ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )
        ) : (
          <ChevronDown className="h-4 w-4 opacity-0 group-hover:opacity-40" />
        )}
      </span>
    )
  }

  // Render table header
  const renderHeader = () => {
    return (
      <TableHeader className="sticky top-0 z-10 bg-background backdrop-blur">
        <TableRow>
          {columns.map((column) => (
            <TableHead
              key={column.key}
              className={`
                ${column.width}
                ${column.align === 'center' ? 'text-center' : ''}
                ${column.align === 'right' ? 'text-right' : ''}
                ${column.sortable ? 'cursor-pointer select-none hover:bg-muted/50 group' : ''}
              `}
              onClick={() => {
                if (column.sortable && column.sortKey) {
                  handleSort(column.sortKey)
                }
              }}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm">{column.label}</span>
                {renderSortIndicator(column.key)}
              </div>
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
    )
  }

  // Render cell content
  const renderCellContent = (cpu: CPURecord, column: typeof columns[number]) => {
    // Use formatter if defined
    if (column.formatter) {
      const formatted = column.formatter(cpu)

      // Special formatting for benchmark scores with badges
      if (column.key === 'cpu_mark_single' || column.key === 'cpu_mark_multi') {
        const variant = getPerformanceVariant(cpu.performance_value_rating)
        const value = column.key === 'cpu_mark_single' ? cpu.cpu_mark_single : cpu.cpu_mark_multi

        if (value) {
          return (
            <TooltipProvider delayDuration={300}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge
                    variant="outline"
                    className={`text-xs font-mono cursor-help ${getBadgeClasses(variant)}`}
                  >
                    {formatted}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs">
                  <p className="text-sm">
                    {column.key === 'cpu_mark_single'
                      ? 'PassMark Single-Thread Score: Measures single-core performance'
                      : 'PassMark Multi-Thread Score: Measures multi-core performance'}
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )
        }
      }

      // Special formatting for iGPU with badge
      if (column.key === 'igpu_mark' && cpu.igpu_mark) {
        return (
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge
                  variant="outline"
                  className={`text-xs font-mono cursor-help ${getBadgeClasses(null)}`}
                >
                  {formatted}
                </Badge>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="text-sm">
                  Integrated GPU PassMark Score: Measures graphics performance
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )
      }

      return formatted
    }

    // Default rendering by column key
    switch (column.key) {
      case 'name':
        return (
          <div className="space-y-1">
            <div className="font-semibold truncate">{cpu.name}</div>
            {cpu.release_year && (
              <div className="text-xs text-muted-foreground">
                Released: {cpu.release_year}
              </div>
            )}
          </div>
        )
      case 'manufacturer':
        return (
          <Badge variant="secondary" className="text-xs">
            {cpu.manufacturer}
          </Badge>
        )
      case 'socket':
        return cpu.socket || '-'
      case 'actions':
        return (
          <div className="flex items-center justify-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                openDetailsDialog(cpu.id)
              }}
              aria-label="View details"
            >
              <Eye className="h-4 w-4 mr-1.5" />
              <span className="hidden sm:inline">Details</span>
            </Button>
          </div>
        )
      default:
        return '-'
    }
  }

  return (
    <div
      ref={tableContainerRef}
      className="relative h-[calc(100vh-300px)] overflow-auto rounded-lg border"
    >
      <Table>
        {renderHeader()}
        <TableBody>
          <tr style={{ height: `${rowVirtualizer.getTotalSize()}px` }} />
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const cpu = sortedCPUs[virtualRow.index]
            const isSelected = selectedCPUId === cpu.id
            const isFocused = focusedIndex === virtualRow.index

            return (
              <TableRow
                key={cpu.id}
                data-index={virtualRow.index}
                className={`
                  group absolute left-0 top-0 h-16 w-full cursor-pointer
                  transition-colors
                  hover:bg-muted/50
                  ${isSelected ? 'bg-muted/80' : ''}
                  ${isFocused ? 'ring-2 ring-primary ring-inset' : ''}
                  ${virtualRow.index % 2 === 0 ? 'bg-background' : 'bg-muted/20'}
                `}
                style={{
                  transform: `translateY(${virtualRow.start}px)`
                }}
                onClick={() => handleRowClick(cpu.id, virtualRow.index)}
                onDoubleClick={() => handleRowDoubleClick(cpu.id)}
              >
                {columns.map((column) => (
                  <TableCell
                    key={column.key}
                    className={`
                      px-4 py-2
                      ${column.width}
                      ${column.align === 'center' ? 'text-center' : ''}
                      ${column.align === 'right' ? 'text-right' : ''}
                    `}
                  >
                    {renderCellContent(cpu, column)}
                  </TableCell>
                ))}
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
})
