'use client'

import React, { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ArrowUpRight } from 'lucide-react'
import { PerformanceBadges } from '../grid-view/performance-badges'
import { KpiMetric } from './kpi-metric'
import { KeyValue } from './key-value'
import type { ListingRow } from '@/components/listings/listings-table'
import { formatRamSummary, formatStorageSummary } from '@/components/listings/listing-formatters'

interface DetailPanelProps {
  listing: ListingRow | undefined
}

export const DetailPanel = React.memo(function DetailPanel({
  listing
}: DetailPanelProps) {
  // Calculate valuation accent
  const valuationAccent = useMemo(() => {
    if (!listing?.price_usd || !listing?.adjusted_price_usd) return 'neutral'
    const savings = ((listing.price_usd - listing.adjusted_price_usd) / listing.price_usd) * 100
    if (savings > 15) return 'good'
    if (savings < -10) return 'warn'
    return 'neutral'
  }, [listing])

  const ramSummary = listing ? formatRamSummary(listing) : null
  const primaryStorageSummary = listing
    ? formatStorageSummary(
        listing.primary_storage_profile ?? null,
        listing.primary_storage_gb ?? null,
        listing.primary_storage_type ?? null
      )
    : null
  const secondaryStorageSummary = listing
    ? formatStorageSummary(
        listing.secondary_storage_profile ?? null,
        listing.secondary_storage_gb ?? null,
        listing.secondary_storage_type ?? null
      )
    : null

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

  const getLinkLabel = (url: string, label?: string | null) => {
    if (label) return label
    try {
      const { hostname } = new URL(url)
      return hostname.replace(/^www\./, '')
    } catch {
      return url
    }
  }

  if (!listing) {
    return (
      <Card className="h-[70vh]">
        <CardContent className="flex h-full items-center justify-center">
          <p className="text-sm text-muted-foreground">
            Select a listing to view details
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-[70vh] overflow-auto">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <CardTitle className="text-xl">{listing.title || 'Untitled'}</CardTitle>
            <div className="flex items-center gap-2">
              {listing.form_factor && (
                <Badge variant="secondary">{listing.form_factor}</Badge>
              )}
              {listing.manufacturer && (
                <Badge variant="outline">{listing.manufacturer}</Badge>
              )}
            </div>
          </div>
          {listing.listing_url && (
            <Button asChild size="sm">
              <a
                href={listing.listing_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ArrowUpRight className="mr-2 h-4 w-4" />
                Open
              </a>
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* KPI Metrics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <KpiMetric
            label="List Price"
            value={formatCurrency(listing.price_usd)}
          />
          <KpiMetric
            label="Adjusted Price"
            value={formatCurrency(listing.adjusted_price_usd)}
            accent={valuationAccent}
          />
          <KpiMetric
            label="$/ST (adj)"
            value={formatMetric(listing.dollar_per_cpu_mark_single_adjusted)}
          />
          <KpiMetric
            label="$/MT (adj)"
            value={formatMetric(listing.dollar_per_cpu_mark_multi_adjusted)}
          />
        </div>

        {/* Performance Badges */}
        <div>
          <h4 className="mb-3 text-sm font-semibold">Performance Metrics</h4>
          <PerformanceBadges listing={listing} />
        </div>

        {/* CPU Specs */}
        <div>
          <h4 className="mb-3 text-sm font-semibold">CPU Information</h4>
          <div className="grid grid-cols-2 gap-4">
            <KeyValue
              label="CPU Model"
              value={listing.cpu?.name || 'Unknown'}
            />
            <KeyValue
              label="Single-Thread Score"
              value={listing.cpu?.cpu_mark_single?.toLocaleString() || '-'}
            />
            <KeyValue
              label="Multi-Thread Score"
              value={listing.cpu?.cpu_mark_multi?.toLocaleString() || '-'}
            />
            <KeyValue
              label="iGPU Score"
              value={listing.cpu?.igpu_mark?.toLocaleString() || '-'}
            />
          </div>
        </div>

        {!!listing.other_urls?.length && (
          <div>
            <h4 className="mb-3 text-sm font-semibold">Additional Links</h4>
            <ul className="space-y-2 text-sm">
              {listing.other_urls.map((link) => (
                <li key={link.url}>
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    {getLinkLabel(link.url, link.label)}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Hardware Specs */}
        <div>
          <h4 className="mb-3 text-sm font-semibold">Hardware</h4>
          <div className="grid grid-cols-2 gap-4">
            <KeyValue
              label="RAM"
              value={ramSummary || '-'}
            />
            <KeyValue
              label="Primary Storage"
              value={primaryStorageSummary || '-'}
            />
            <KeyValue
              label="Secondary Storage"
              value={secondaryStorageSummary || '-'}
            />
            {listing.gpu?.name && (
              <KeyValue
                label="GPU"
                value={listing.gpu.name}
              />
            )}
          </div>
        </div>

        {/* Metadata */}
        <div>
          <h4 className="mb-3 text-sm font-semibold">Details</h4>
          <div className="grid grid-cols-2 gap-4">
            <KeyValue
              label="Condition"
              value={listing.condition || '-'}
            />
            <KeyValue
              label="Vendor"
              value={listing.vendor || '-'}
            />
            <KeyValue
              label="Model"
              value={listing.model_number || '-'}
            />
            <KeyValue
              label="Series"
              value={listing.series || '-'}
            />
          </div>
        </div>

        {/* Ports */}
        {listing.ports && Object.keys(listing.ports).length > 0 && (
          <div>
            <h4 className="mb-3 text-sm font-semibold">Ports & Connectivity</h4>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(listing.ports).map(([key, value]) => (
                <KeyValue
                  key={key}
                  label={key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  value={value}
                />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
})
