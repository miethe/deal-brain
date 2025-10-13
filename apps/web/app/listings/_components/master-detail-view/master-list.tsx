'use client'

import React, { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { useCatalogStore } from '@/stores/catalog-store'
import type { ListingRow } from '@/components/listings/listings-table'

interface MasterListProps {
  listings: ListingRow[]
}

export const MasterList = React.memo(function MasterList({
  listings
}: MasterListProps) {
  const {
    selectedListingId,
    setSelectedListing,
    compareSelections,
    toggleCompare
  } = useCatalogStore()

  const listRef = useRef<HTMLDivElement>(null)
  const [focusedIndex, setFocusedIndex] = React.useState<number>(0)

  // Select first item if nothing is selected
  useEffect(() => {
    if (!selectedListingId && listings.length > 0) {
      setSelectedListing(listings[0].id)
    }
  }, [selectedListingId, listings, setSelectedListing])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      switch (e.key) {
        case 'j':
        case 'ArrowDown':
          e.preventDefault()
          setFocusedIndex((prev) => {
            const next = Math.min(prev + 1, listings.length - 1)
            setSelectedListing(listings[next].id)
            return next
          })
          break
        case 'k':
        case 'ArrowUp':
          e.preventDefault()
          setFocusedIndex((prev) => {
            const next = Math.max(prev - 1, 0)
            setSelectedListing(listings[next].id)
            return next
          })
          break
        case 'c':
          e.preventDefault()
          if (listings[focusedIndex]) {
            toggleCompare(listings[focusedIndex].id)
          }
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [focusedIndex, listings, setSelectedListing, toggleCompare])

  // Format currency
  const formatCurrency = (value: number | null | undefined) => {
    if (value == null) return '-'
    return `$${Math.round(value)}`
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
    <div className="rounded-lg border bg-background">
      <div className="border-b p-4">
        <h3 className="font-semibold">All Listings ({listings.length})</h3>
        <p className="text-xs text-muted-foreground">
          Use j/k or arrow keys to navigate
        </p>
      </div>
      <ScrollArea className="h-[70vh]" ref={listRef}>
        <div className="space-y-1 p-2">
          {listings.map((listing, index) => {
            const isSelected = selectedListingId === listing.id
            const isCompared = compareSelections.includes(listing.id)

            return (
              <div key={listing.id} className="space-y-1">
                <Button
                  variant={isSelected ? 'secondary' : 'ghost'}
                  className={`h-auto w-full justify-start p-3 text-left ${
                    isSelected ? 'border-primary bg-muted ring-2 ring-primary' : ''
                  }`}
                  onClick={() => {
                    setSelectedListing(listing.id)
                    setFocusedIndex(index)
                  }}
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold">{listing.title || 'Untitled'}</span>
                      <span
                        className={`shrink-0 text-sm ${getValuationColor(
                          listing.adjusted_price_usd,
                          listing.price_usd
                        )}`}
                      >
                        {formatCurrency(listing.adjusted_price_usd)}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {listing.cpu?.name || 'Unknown CPU'}
                      {listing.cpu?.cpu_mark_single && listing.cpu?.cpu_mark_multi && (
                        <span className="ml-2">
                          ST {listing.cpu.cpu_mark_single.toLocaleString()} /
                          MT {listing.cpu.cpu_mark_multi.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                </Button>
                <div className="flex items-center gap-2 px-3 py-1">
                  <Checkbox
                    id={`compare-${listing.id}`}
                    checked={isCompared}
                    onCheckedChange={() => toggleCompare(listing.id)}
                  />
                  <label
                    htmlFor={`compare-${listing.id}`}
                    className="text-xs text-muted-foreground cursor-pointer"
                  >
                    Add to compare
                  </label>
                </div>
              </div>
            )
          })}
        </div>
      </ScrollArea>
    </div>
  )
})
