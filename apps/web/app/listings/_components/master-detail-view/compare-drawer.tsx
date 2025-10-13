'use client'

import React from 'react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Layers3, X } from 'lucide-react'
import { PerformanceBadges } from '../grid-view/performance-badges'
import { useCatalogStore } from '@/stores/catalog-store'
import type { ListingRow } from '@/components/listings/listings-table'
import { formatRamSummary, formatStorageSummary } from '@/components/listings/listing-formatters'

interface CompareDrawerProps {
  listings: ListingRow[]
}

export const CompareDrawer = React.memo(function CompareDrawer({
  listings
}: CompareDrawerProps) {
  const { toggleCompare, clearCompare } = useCatalogStore()
  const [isOpen, setIsOpen] = React.useState(false)

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

  if (listings.length === 0) return null

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button
          className="fixed bottom-4 right-4 z-40 shadow-lg"
          size="lg"
        >
          <Layers3 className="mr-2 h-5 w-5" />
          Compare ({listings.length})
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="h-[60vh]">
        <SheetHeader>
          <div className="flex items-center justify-between">
            <SheetTitle>Compare Listings</SheetTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                clearCompare()
                setIsOpen(false)
              }}
            >
              Clear All
            </Button>
          </div>
        </SheetHeader>
        <div className="mt-6 h-[calc(100%-60px)] overflow-auto">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {listings.slice(0, 6).map((listing) => {
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

              return (
                <div
                  key={listing.id}
                  className="relative space-y-3 rounded-lg border bg-background p-4"
                >
                {/* Remove button */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 top-2 h-6 w-6 p-0"
                  onClick={() => toggleCompare(listing.id)}
                >
                  <X className="h-4 w-4" />
                </Button>

                {/* Title and Price */}
                <div className="pr-8">
                  <h4 className="font-semibold">{listing.title || 'Untitled'}</h4>
                  <div className="mt-1 flex items-baseline gap-2">
                    <span
                      className={`text-xl font-bold ${getValuationColor(
                        listing.adjusted_price_usd,
                        listing.price_usd
                      )}`}
                    >
                      {formatCurrency(listing.adjusted_price_usd)}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {formatMetric(listing.dollar_per_cpu_mark_multi_adjusted)} /MT
                    </span>
                  </div>
                </div>

                {/* CPU Info */}
                <div className="space-y-1 text-sm">
                  <div className="font-medium">{listing.cpu?.name || 'Unknown CPU'}</div>
                  {listing.cpu?.cpu_mark_single && listing.cpu?.cpu_mark_multi && (
                    <div className="text-xs text-muted-foreground">
                      ST {listing.cpu.cpu_mark_single.toLocaleString()} /
                      MT {listing.cpu.cpu_mark_multi.toLocaleString()}
                    </div>
                  )}
                </div>

                {/* Hardware */}
                <div className="flex flex-wrap gap-2 text-xs">
                  {ramSummary && <Badge variant="secondary">{ramSummary}</Badge>}
                  {primaryStorageSummary && (
                    <Badge variant="secondary">{primaryStorageSummary}</Badge>
                  )}
                  {secondaryStorageSummary && (
                    <Badge variant="outline">{secondaryStorageSummary}</Badge>
                  )}
                  {listing.form_factor && (
                    <Badge variant="outline">{listing.form_factor}</Badge>
                  )}
                </div>

                {/* Performance Badges */}
                <div>
                  <PerformanceBadges listing={listing} />
                </div>
                </div>
              )
            })}
          </div>
          {listings.length > 6 && (
            <p className="mt-4 text-center text-sm text-muted-foreground">
              Showing first 6 of {listings.length} selected
            </p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
})
