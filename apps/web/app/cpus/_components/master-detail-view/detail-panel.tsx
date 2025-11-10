'use client'

import React, { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'
import { ArrowUpRight, Plus, AlertCircle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { KpiMetric } from './kpi-metric'
import { KeyValue } from './key-value'
import { PerformanceBadge } from '../grid-view/performance-badge'
import { PriceTargets } from '../price-targets'
import { PerformanceValueBadge } from '../performance-value-badge'
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store'
import type { CPURecord, CPUDetail } from '@/types/cpus'

interface DetailPanelProps {
  cpu: CPURecord | undefined
  cpuDetail: CPUDetail | undefined
  isLoadingDetail?: boolean
  isErrorDetail?: boolean
}

export const DetailPanel = React.memo(function DetailPanel({
  cpu,
  cpuDetail,
  isLoadingDetail,
  isErrorDetail
}: DetailPanelProps) {
  const { toggleCompare, compareSelections } = useCPUCatalogStore()

  const isCompared = cpu ? compareSelections.includes(cpu.id) : false

  // Calculate price target accent
  const priceTargetAccent = useMemo(() => {
    if (!cpu?.price_target_good || !cpu?.price_target_great) return 'neutral'
    if (cpu.price_target_confidence === 'high') return 'good'
    if (cpu.price_target_confidence === 'medium') return 'neutral'
    return 'warn'
  }, [cpu])

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

  // Get performance rating variant
  const getPerformanceVariant = (
    rating: 'excellent' | 'good' | 'fair' | 'poor' | null
  ): 'excellent' | 'good' | 'fair' | 'poor' | null => {
    return rating
  }

  // Helper: Create histogram bins from price distribution
  const createHistogramBins = (prices: number[], binCount: number = 10) => {
    if (!prices || prices.length === 0) return []

    const min = Math.min(...prices)
    const max = Math.max(...prices)

    // Edge case: All prices are identical
    if (min === max) {
      return [{
        range: `$${Math.round(min)}`,
        count: prices.length,
        minPrice: min,
        maxPrice: max,
      }]
    }

    // Edge case: Very small price range (less than bin count)
    // Reduce bin count to avoid empty bins
    const priceRange = max - min
    const adjustedBinCount = priceRange < binCount
      ? Math.max(1, Math.ceil(priceRange))
      : binCount

    const binSize = (max - min) / adjustedBinCount

    const bins = Array.from({ length: adjustedBinCount }, (_, i) => ({
      range: `$${Math.round(min + i * binSize)}-${Math.round(min + (i + 1) * binSize)}`,
      count: 0,
      minPrice: min + i * binSize,
      maxPrice: min + (i + 1) * binSize,
    }))

    prices.forEach(price => {
      // Calculate bin index safely
      const binIndex = Math.floor((price - min) / binSize)
      // Ensure bin index is within valid range (handle edge case where price === max)
      const safeBinIndex = Math.min(Math.max(0, binIndex), adjustedBinCount - 1)
      bins[safeBinIndex].count++
    })

    return bins.filter(bin => bin.count > 0)
  }

  // Helper: Get chart color for performance metrics
  const getPerformanceChartColor = (name: string): string => {
    const colors: Record<string, string> = {
      'Single-Thread': 'hsl(217, 91%, 60%)', // Blue (primary)
      'Multi-Thread': 'hsl(262, 83%, 58%)', // Purple
      'iGPU': 'hsl(330, 81%, 60%)', // Pink
    }
    return colors[name] || 'hsl(var(--primary))'
  }

  // Memoize performance chart data
  const performanceData = useMemo(() => {
    if (!cpu) return []

    const data = [
      { name: 'Single-Thread', value: cpu.cpu_mark_single, maxValue: 5000 },
      { name: 'Multi-Thread', value: cpu.cpu_mark_multi, maxValue: 50000 },
      { name: 'iGPU', value: cpu.igpu_mark || 0, maxValue: 10000 },
    ].filter(item => item.value && item.value > 0)

    return data
  }, [cpu])

  // Memoize histogram data
  const histogramData = useMemo(() => {
    if (!cpuDetail?.market_data.price_distribution) return []
    return createHistogramBins(cpuDetail.market_data.price_distribution)
  }, [cpuDetail?.market_data.price_distribution])

  if (!cpu) {
    return (
      <Card className="h-[70vh]">
        <CardContent className="flex h-full items-center justify-center">
          <p className="text-sm text-muted-foreground">
            Select a CPU to view details
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
            <CardTitle className="text-xl">{cpu.name}</CardTitle>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="secondary">{cpu.manufacturer}</Badge>
              {cpu.socket && <Badge variant="outline">{cpu.socket}</Badge>}
              {cpu.release_year && (
                <Badge variant="outline">{cpu.release_year}</Badge>
              )}
            </div>
          </div>
          <Button
            variant={isCompared ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => toggleCompare(cpu.id)}
          >
            <Plus className="mr-2 h-4 w-4" />
            {isCompared ? 'In Compare' : 'Compare'}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Loading State for Analytics Data */}
        {isLoadingDetail && (
          <Alert>
            <AlertDescription className="flex items-center gap-2">
              <Skeleton className="h-4 w-4 rounded-full" />
              <span className="text-sm">Loading market analytics...</span>
            </AlertDescription>
          </Alert>
        )}

        {/* Error State for Analytics Data */}
        {isErrorDetail && !isLoadingDetail && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              Failed to load market analytics. Basic CPU information shown.
            </AlertDescription>
          </Alert>
        )}

        {/* KPI Metrics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <KpiMetric
            label="Good Price"
            value={formatCurrency(cpu.price_target_good)}
            accent={priceTargetAccent}
          />
          <KpiMetric
            label="Great Price"
            value={formatCurrency(cpu.price_target_great)}
            accent={priceTargetAccent}
          />
          <KpiMetric
            label="$/ST Mark"
            value={formatMetric(cpu.dollar_per_mark_single)}
          />
          <KpiMetric
            label="$/MT Mark"
            value={formatMetric(cpu.dollar_per_mark_multi)}
          />
        </div>

        {/* Price Targets - Detailed View */}
        <PriceTargets
          priceTargetGreat={cpu.price_target_great}
          priceTargetGood={cpu.price_target_good}
          priceTargetFair={cpu.price_target_fair}
          confidence={cpu.price_target_confidence}
          sampleSize={cpu.price_target_sample_size}
          variant="detailed"
        />

        {/* Performance Badges */}
        <div>
          <h4 className="mb-3 text-sm font-semibold">Performance Metrics</h4>
          <div className="flex flex-wrap gap-2">
            {cpu.cpu_mark_single && (
              <PerformanceBadge
                label="ST"
                value={cpu.cpu_mark_single}
                variant={getPerformanceVariant(cpu.performance_value_rating)}
              />
            )}
            {cpu.cpu_mark_multi && (
              <PerformanceBadge
                label="MT"
                value={cpu.cpu_mark_multi}
                variant={getPerformanceVariant(cpu.performance_value_rating)}
              />
            )}
            {cpu.igpu_mark && (
              <PerformanceBadge
                label="iGPU"
                value={cpu.igpu_mark}
                variant="igpu"
              />
            )}
          </div>
          {/* Performance Value Badges */}
          <div className="flex flex-wrap gap-2 mt-2">
            {cpu.dollar_per_mark_single && (
              <PerformanceValueBadge
                rating={cpu.performance_value_rating}
                dollarPerMark={cpu.dollar_per_mark_single}
                percentile={cpu.performance_value_percentile}
                metricType="single"
              />
            )}
            {cpu.dollar_per_mark_multi && (
              <PerformanceValueBadge
                rating={cpu.performance_value_rating}
                dollarPerMark={cpu.dollar_per_mark_multi}
                percentile={cpu.performance_value_percentile}
                metricType="multi"
              />
            )}
          </div>

          {/* PassMark Comparison Chart */}
          {performanceData.length > 0 && (
            <figure
              className="mt-4"
              role="img"
              aria-label="CPU benchmark performance comparison"
            >
              <figcaption className="text-xs text-muted-foreground mb-2">
                Benchmark Scores
              </figcaption>
              <div className="sr-only">
                Bar chart showing {performanceData.map(d => d.name).join(', ')} benchmark scores
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={performanceData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                  <XAxis
                    dataKey="name"
                    fontSize={12}
                    stroke="hsl(var(--muted-foreground))"
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    fontSize={12}
                    stroke="hsl(var(--muted-foreground))"
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => value.toLocaleString()}
                  />
                  <Tooltip
                    cursor={{ fill: 'hsl(var(--muted) / 0.3)' }}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px',
                      padding: '8px 12px',
                    }}
                    labelStyle={{
                      fontSize: '12px',
                      fontWeight: 600,
                      color: 'hsl(var(--foreground))',
                    }}
                    itemStyle={{
                      fontSize: '12px',
                      color: 'hsl(var(--muted-foreground))',
                    }}
                    formatter={(value: number) => [value.toLocaleString(), 'Score']}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {performanceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getPerformanceChartColor(entry.name)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </figure>
          )}
        </div>

        {/* Market Data Section - Shows when analytics loaded */}
        {cpuDetail?.market_data && (
          <div>
            <h4 className="mb-3 text-sm font-semibold">Market Analytics</h4>
            <div className="grid grid-cols-2 gap-4">
              <KeyValue
                label="Total Listings"
                value={cpuDetail.listings_count || 0}
              />
              <KeyValue
                label="Price Data Points"
                value={cpuDetail.market_data.price_distribution?.length || 0}
              />
            </div>

            {/* Price Distribution Histogram */}
            {cpuDetail.market_data.price_distribution &&
              cpuDetail.market_data.price_distribution.length > 0 &&
              histogramData.length > 0 && (
                <figure
                  className="mt-4"
                  role="img"
                  aria-label="Price distribution histogram"
                >
                  <figcaption className="text-xs text-muted-foreground mb-2">
                    Price Distribution ({cpuDetail.market_data.price_distribution.length} listings)
                  </figcaption>
                  <div className="sr-only">
                    Histogram showing the distribution of listing prices across {histogramData.length} price ranges
                  </div>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={histogramData} margin={{ top: 5, right: 10, left: 10, bottom: 80 }}>
                      <XAxis
                        dataKey="range"
                        fontSize={11}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        stroke="hsl(var(--muted-foreground))"
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        fontSize={12}
                        stroke="hsl(var(--muted-foreground))"
                        tickLine={false}
                        axisLine={false}
                        label={{
                          value: 'Listings',
                          angle: -90,
                          position: 'insideLeft',
                          style: {
                            fontSize: 12,
                            fill: 'hsl(var(--muted-foreground))',
                          },
                        }}
                      />
                      <Tooltip
                        cursor={{ fill: 'hsl(var(--muted) / 0.3)' }}
                        content={({ payload }) => {
                          if (!payload || !payload.length) return null
                          const data = payload[0].payload
                          return (
                            <div
                              className="bg-background border rounded p-2 shadow-md"
                              style={{
                                backgroundColor: 'hsl(var(--background))',
                                border: '1px solid hsl(var(--border))',
                              }}
                            >
                              <p className="text-sm font-medium">{data.range}</p>
                              <p className="text-sm text-muted-foreground">
                                {data.count} listing{data.count !== 1 ? 's' : ''}
                              </p>
                            </div>
                          )
                        }}
                      />
                      <Bar
                        dataKey="count"
                        fill="hsl(var(--primary))"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </figure>
              )}
          </div>
        )}

        {/* Associated Listings Section - Shows when analytics loaded */}
        {cpuDetail?.associated_listings && cpuDetail.associated_listings.length > 0 && (
          <div>
            <h4 className="mb-3 text-sm font-semibold">
              Top Listings ({cpuDetail.associated_listings.length})
            </h4>
            <div className="space-y-2">
              {cpuDetail.associated_listings.slice(0, 5).map((listing) => (
                <div
                  key={listing.id}
                  className="flex items-center justify-between p-2 rounded-md bg-muted/50 text-sm"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{listing.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {listing.marketplace} • {listing.condition}
                    </p>
                  </div>
                  <div className="text-right ml-2">
                    <p className="font-semibold">
                      {formatCurrency(listing.adjusted_price_usd)}
                    </p>
                    {listing.base_price_usd !== listing.adjusted_price_usd && (
                      <p className="text-xs text-muted-foreground line-through">
                        {formatCurrency(listing.base_price_usd)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CPU Specifications */}
        <div>
          <h4 className="mb-3 text-sm font-semibold">Specifications</h4>
          <div className="grid grid-cols-2 gap-4">
            <KeyValue
              label="Cores / Threads"
              value={
                cpu.cores && cpu.threads
                  ? `${cpu.cores} cores / ${cpu.threads} threads`
                  : '-'
              }
            />
            <KeyValue
              label="TDP"
              value={cpu.tdp_w ? `${cpu.tdp_w}W` : '-'}
            />
            <KeyValue
              label="Socket"
              value={cpu.socket || '-'}
            />
            <KeyValue
              label="Release Year"
              value={cpu.release_year || '-'}
            />
            <KeyValue
              label="Integrated GPU"
              value={cpu.igpu_model || (cpu.igpu_mark ? 'Yes' : 'None')}
            />
            <KeyValue
              label="Active Listings"
              value={cpu.listings_count || 0}
            />
          </div>
        </div>

        {/* Performance Value Details */}
        {cpu.performance_value_rating && (
          <div>
            <h4 className="mb-3 text-sm font-semibold">Performance Value</h4>
            <div className="grid grid-cols-2 gap-4">
              <KeyValue
                label="Value Rating"
                value={
                  <Badge
                    variant={
                      cpu.performance_value_rating === 'excellent'
                        ? 'default'
                        : cpu.performance_value_rating === 'good'
                        ? 'secondary'
                        : 'outline'
                    }
                  >
                    {cpu.performance_value_rating}
                  </Badge>
                }
              />
              <KeyValue
                label="Percentile Rank"
                value={
                  cpu.performance_value_percentile !== null
                    ? `${cpu.performance_value_percentile.toFixed(0)}th`
                    : '-'
                }
              />
            </div>
          </div>
        )}

        {/* Additional Information */}
        {cpu.notes && (
          <div>
            <h4 className="mb-3 text-sm font-semibold">Notes</h4>
            <p className="text-sm text-muted-foreground">{cpu.notes}</p>
          </div>
        )}

        {/* PassMark Link */}
        {cpu.passmark_slug && (
          <div className="pt-4 border-t">
            <Button asChild size="sm" variant="outline">
              <a
                href={`https://www.cpubenchmark.net/cpu.php?cpu=${encodeURIComponent(
                  cpu.passmark_slug
                )}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ArrowUpRight className="mr-2 h-4 w-4" />
                View on PassMark
              </a>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
})
