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
import { PerformanceBadge } from '../grid-view/performance-badge'
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store'
import type { CPURecord } from '@/types/cpus'

interface CompareDrawerProps {
  cpus: CPURecord[]
}

export const CompareDrawer = React.memo(function CompareDrawer({
  cpus
}: CompareDrawerProps) {
  const { toggleCompare, clearCompare } = useCPUCatalogStore()
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

  // Get performance variant
  const getPerformanceVariant = (
    rating: 'excellent' | 'good' | 'fair' | 'poor' | null
  ): 'excellent' | 'good' | 'fair' | 'poor' | null => {
    return rating
  }

  if (cpus.length === 0) return null

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button
          className="fixed bottom-4 right-4 z-40 shadow-lg"
          size="lg"
        >
          <Layers3 className="mr-2 h-5 w-5" />
          Compare ({cpus.length})
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="h-[60vh]">
        <SheetHeader>
          <div className="flex items-center justify-between">
            <SheetTitle>Compare CPUs</SheetTitle>
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
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {cpus.slice(0, 4).map((cpu) => {
              return (
                <div
                  key={cpu.id}
                  className="relative space-y-3 rounded-lg border bg-background p-4"
                >
                  {/* Remove button */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-2 top-2 h-6 w-6 p-0"
                    onClick={() => toggleCompare(cpu.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>

                  {/* Title and Manufacturer */}
                  <div className="pr-8">
                    <h4 className="font-semibold">{cpu.name}</h4>
                    <div className="mt-1 flex items-center gap-2">
                      <Badge variant="secondary">{cpu.manufacturer}</Badge>
                      {cpu.socket && (
                        <Badge variant="outline" className="text-xs">
                          {cpu.socket}
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Price Targets */}
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Good Price:</span>
                      <span className="font-semibold text-emerald-700">
                        {formatCurrency(cpu.price_target_good)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Great Price:</span>
                      <span className="font-semibold text-emerald-800">
                        {formatCurrency(cpu.price_target_great)}
                      </span>
                    </div>
                  </div>

                  {/* Core Specs */}
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Cores/Threads:</span>
                      <span className="font-medium">
                        {cpu.cores && cpu.threads
                          ? `${cpu.cores}C / ${cpu.threads}T`
                          : '-'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">TDP:</span>
                      <span className="font-medium">
                        {cpu.tdp_w ? `${cpu.tdp_w}W` : '-'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Release:</span>
                      <span className="font-medium">{cpu.release_year || '-'}</span>
                    </div>
                  </div>

                  {/* Performance Badges */}
                  <div className="flex flex-wrap gap-1">
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

                  {/* Performance Value */}
                  <div className="space-y-1 border-t pt-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">$/ST Mark:</span>
                      <span className="font-medium">
                        {formatMetric(cpu.dollar_per_mark_single)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">$/MT Mark:</span>
                      <span className="font-medium">
                        {formatMetric(cpu.dollar_per_mark_multi)}
                      </span>
                    </div>
                    {cpu.performance_value_rating && (
                      <div className="flex justify-between items-center">
                        <span className="text-muted-foreground">Value Rating:</span>
                        <Badge
                          variant={
                            cpu.performance_value_rating === 'excellent'
                              ? 'default'
                              : cpu.performance_value_rating === 'good'
                              ? 'secondary'
                              : 'outline'
                          }
                          className="text-xs"
                        >
                          {cpu.performance_value_rating}
                        </Badge>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
          {cpus.length > 4 && (
            <p className="mt-4 text-center text-sm text-muted-foreground">
              Showing first 4 of {cpus.length} selected. Maximum 4 CPUs can be compared.
            </p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
})
