'use client'

import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
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
import { Checkbox } from '@/components/ui/checkbox'
import {
  ArrowUpRight,
  SquarePen,
  MoreHorizontal,
  Info
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { useCatalogStore } from '@/stores/catalog-store'
import type { ListingRow } from '@/components/listings/listings-table'
import { formatRamSummary, formatStorageSummary } from '@/components/listings/listing-formatters'
import { EntityTooltip } from '@/components/listings/entity-tooltip'
import { fetchEntityData } from '@/lib/api/entities'

interface DenseTableProps {
  listings: ListingRow[]
  highlightedId?: number | null
}

export const DenseTable = React.memo(function DenseTable({
  listings,
  highlightedId
}: DenseTableProps) {
  const { openDetailsDialog, openQuickEditDialog } = useCatalogStore()
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())
  const [focusedIndex, setFocusedIndex] = useState<number>(-1)
  const tableContainerRef = useRef<HTMLDivElement>(null)
  const highlightedRef = useRef<HTMLTableRowElement>(null)
  const router = useRouter()

  // Virtual scrolling for large datasets
  const rowVirtualizer = useVirtualizer({
    count: listings.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => 64, // 64px row height
    overscan: 5
  })

  // Handle highlighting and scrolling
  useEffect(() => {
    if (highlightedId && highlightedRef.current) {
      // Scroll into view with smooth behavior
      highlightedRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })

      // Focus for accessibility
      highlightedRef.current.focus()

      // Clear highlight param after 2 seconds
      const timer = setTimeout(() => {
        const params = new URLSearchParams(window.location.search)
        params.delete('highlight')
        const newSearch = params.toString()
        router.replace(
          `${window.location.pathname}${newSearch ? `?${newSearch}` : ''}`,
          { scroll: false }
        )
      }, 2000)

      return () => clearTimeout(timer)
    }
  }, [highlightedId, router])

  // Toggle row selection
  const toggleRow = useCallback((id: number) => {
    setSelectedRows((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }, [])

  // Toggle all rows
  const toggleAll = useCallback(() => {
    if (selectedRows.size === listings.length) {
      setSelectedRows(new Set())
    } else {
      setSelectedRows(new Set(listings.map((l) => l.id)))
    }
  }, [listings, selectedRows.size])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return // Don't handle if focus is in input
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setFocusedIndex((prev) => Math.min(prev + 1, listings.length - 1))
          break
        case 'ArrowUp':
          e.preventDefault()
          setFocusedIndex((prev) => Math.max(prev - 1, 0))
          break
        case 'Enter':
          if (focusedIndex >= 0) {
            e.preventDefault()
            openDetailsDialog(listings[focusedIndex].id)
          }
          break
        case 'Escape':
          e.preventDefault()
          setFocusedIndex(-1)
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [focusedIndex, listings, openDetailsDialog])

  // Format currency
  const formatCurrency = (value: number | null | undefined) => {
    if (value == null) return '-'
    return `$${Math.round(value)}`
  }

  // Format performance metric
  const formatMetric = (value: number | null | undefined) => {
    if (value == null) return '-'
    return `$${value.toFixed(3)}`
  }

  // Get valuation color
  const getValuationColor = (adjusted: number | null, price: number | null) => {
    if (adjusted == null || price == null) return 'text-foreground'
    const savings = ((price - adjusted) / price) * 100
    if (savings > 15) return 'text-emerald-700 font-semibold'
    if (savings > 5) return 'text-emerald-600'
    if (savings < -10) return 'text-amber-600'
    return 'text-foreground'
  }

  return (
    <>
      <div
        ref={tableContainerRef}
        className="relative h-[calc(100vh-300px)] overflow-auto rounded-lg border"
      >
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-background">
            <TableRow>
              <TableHead className="w-12">
                <Checkbox
                  checked={selectedRows.size === listings.length && listings.length > 0}
                  onCheckedChange={toggleAll}
                  aria-label="Select all"
                />
              </TableHead>
              <TableHead className="min-w-[250px]">Title</TableHead>
              <TableHead className="min-w-[200px]">CPU</TableHead>
              <TableHead className="w-24 text-right">Price</TableHead>
              <TableHead className="w-24 text-right">Adjusted</TableHead>
              <TableHead className="w-24 text-right">$/ST</TableHead>
              <TableHead className="w-24 text-right">$/MT</TableHead>
              <TableHead className="w-32 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <tr style={{ height: `${rowVirtualizer.getTotalSize()}px` }} />
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const listing = listings[virtualRow.index]
              const isSelected = selectedRows.has(listing.id)
              const isFocused = focusedIndex === virtualRow.index
              const isHighlighted = listing.id === highlightedId
              const ramSummary = formatRamSummary(listing)
              const primaryStorageSummary = formatStorageSummary(
                listing.primary_storage_profile ?? null,
                listing.primary_storage_gb ?? null,
                listing.primary_storage_type ?? null
              )
              const secondaryStorageSummary = formatStorageSummary(
                listing.secondary_storage_profile ?? null,
                listing.secondary_storage_gb ?? null,
                listing.secondary_storage_type ?? null
              )
              const specSummary = [ramSummary, primaryStorageSummary, secondaryStorageSummary]
                .filter(Boolean)
                .join(' • ')

              return (
                <TableRow
                  key={listing.id}
                  ref={isHighlighted ? highlightedRef : null}
                  data-index={virtualRow.index}
                  data-highlighted={isHighlighted}
                  tabIndex={isHighlighted ? -1 : undefined}
                  aria-label={isHighlighted ? "Newly created listing" : undefined}
                  className={`group absolute left-0 top-0 h-16 w-full ${
                    isFocused ? 'ring-2 ring-primary' : ''
                  }`}
                  style={{
                    transform: `translateY(${virtualRow.start}px)`
                  }}
                >
                  <TableCell>
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => toggleRow(listing.id)}
                      aria-label={`Select ${listing.title}`}
                    />
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-semibold">{listing.title || 'Untitled'}</div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        {listing.form_factor && (
                          <Badge variant="secondary" className="text-xs">
                            {listing.form_factor}
                          </Badge>
                        )}
                        {specSummary && <span>{specSummary}</span>}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium">
                        {listing.cpu?.id ? (
                          <EntityTooltip
                            entityType="cpu"
                            entityId={listing.cpu.id}
                            fetchData={fetchEntityData}
                            variant="inline"
                          >
                            {listing.cpu_name || listing.cpu.name || 'Unknown CPU'}
                          </EntityTooltip>
                        ) : (
                          listing.cpu_name || listing.cpu?.name || 'Unknown CPU'
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {listing.gpu?.id && listing.gpu_name ? (
                          <EntityTooltip
                            entityType="gpu"
                            entityId={listing.gpu.id}
                            fetchData={fetchEntityData}
                            variant="inline"
                          >
                            GPU: {listing.gpu_name}
                          </EntityTooltip>
                        ) : listing.gpu_name ? (
                          <>GPU: {listing.gpu_name}</>
                        ) : (
                          <>
                            ST {listing.cpu?.cpu_mark_single?.toLocaleString() || '-'} /
                            MT {listing.cpu?.cpu_mark_multi?.toLocaleString() || '-'}
                          </>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(listing.price_usd)}
                  </TableCell>
                  <TableCell className={`text-right font-medium ${getValuationColor(listing.adjusted_price_usd, listing.price_usd)}`}>
                    {formatCurrency(listing.adjusted_price_usd)}
                  </TableCell>
                  <TableCell className="text-right text-sm">
                    {formatMetric(listing.dollar_per_cpu_mark_single_adjusted)}
                  </TableCell>
                  <TableCell className="text-right text-sm">
                    {formatMetric(listing.dollar_per_cpu_mark_multi_adjusted)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-1 opacity-70 transition-opacity group-hover:opacity-100">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDetailsDialog(listing.id)}
                        aria-label="View details"
                      >
                        <Info className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openQuickEditDialog(listing.id)}
                        aria-label="Quick edit"
                      >
                        <SquarePen className="h-4 w-4" />
                      </Button>
                      {listing.listing_url && (
                        <Button
                          variant="ghost"
                          size="sm"
                          asChild
                        >
                          <a
                            href={listing.listing_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label="Open listing"
                          >
                            <ArrowUpRight className="h-4 w-4" />
                          </a>
                        </Button>
                      )}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" aria-label="More actions">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>Archive</DropdownMenuItem>
                          <DropdownMenuItem>Duplicate</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>

      {/* Bulk Selection Panel */}
      {selectedRows.size > 0 && (
        <div className="fixed bottom-4 left-1/2 z-50 flex -translate-x-1/2 items-center gap-4 rounded-lg border bg-background px-6 py-3 shadow-lg">
          <span className="text-sm font-medium">
            {selectedRows.size} selected
          </span>
          <Button variant="outline" size="sm" onClick={() => setSelectedRows(new Set())}>
            Clear
          </Button>
          <Button variant="default" size="sm">
            Bulk Edit
          </Button>
        </div>
      )}
    </>
  )
})
