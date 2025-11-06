'use client'

import React, { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ArrowUpRight, Plus } from 'lucide-react'
import { KpiMetric } from './kpi-metric'
import { KeyValue } from './key-value'
import { PerformanceBadge } from '../grid-view/performance-badge'
import { PriceTargets } from '../price-targets'
import { PerformanceValueBadge } from '../performance-value-badge'
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store'
import type { CPURecord } from '@/types/cpus'

interface DetailPanelProps {
  cpu: CPURecord | undefined
}

export const DetailPanel = React.memo(function DetailPanel({
  cpu
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
        </div>

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
