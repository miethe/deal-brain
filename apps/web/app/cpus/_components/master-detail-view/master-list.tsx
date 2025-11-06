'use client'

import React, { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Search } from 'lucide-react'
import { useCPUCatalogStore } from '@/stores/cpu-catalog-store'
import type { CPURecord } from '@/types/cpus'

interface MasterListProps {
  cpus: CPURecord[]
}

export const MasterList = React.memo(function MasterList({
  cpus
}: MasterListProps) {
  const {
    selectedCPUId,
    setSelectedCPU,
    compareSelections,
    toggleCompare
  } = useCPUCatalogStore()

  const listRef = useRef<HTMLDivElement>(null)
  const [focusedIndex, setFocusedIndex] = React.useState<number>(0)
  const [searchQuery, setSearchQuery] = React.useState('')

  // Select first item if nothing is selected
  useEffect(() => {
    if (!selectedCPUId && cpus.length > 0) {
      setSelectedCPU(cpus[0].id)
    }
  }, [selectedCPUId, cpus, setSelectedCPU])

  // Filter CPUs by search query
  const filteredCPUs = React.useMemo(() => {
    if (!searchQuery.trim()) return cpus

    const query = searchQuery.toLowerCase()
    return cpus.filter((cpu) =>
      cpu.name.toLowerCase().includes(query) ||
      cpu.manufacturer.toLowerCase().includes(query) ||
      cpu.socket?.toLowerCase().includes(query)
    )
  }, [cpus, searchQuery])

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
            const next = Math.min(prev + 1, filteredCPUs.length - 1)
            setSelectedCPU(filteredCPUs[next].id)
            return next
          })
          break
        case 'k':
        case 'ArrowUp':
          e.preventDefault()
          setFocusedIndex((prev) => {
            const next = Math.max(prev - 1, 0)
            setSelectedCPU(filteredCPUs[next].id)
            return next
          })
          break
        case 'c':
          e.preventDefault()
          if (filteredCPUs[focusedIndex]) {
            toggleCompare(filteredCPUs[focusedIndex].id)
          }
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [focusedIndex, filteredCPUs, setSelectedCPU, toggleCompare])

  // Format TDP
  const formatTDP = (tdp: number | null) => {
    if (tdp == null) return null
    return `${tdp}W`
  }

  return (
    <div className="rounded-lg border bg-background">
      <div className="border-b p-4">
        <h3 className="font-semibold mb-3">All CPUs ({filteredCPUs.length})</h3>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search CPUs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Use j/k or arrow keys to navigate, c to compare
        </p>
      </div>
      <ScrollArea className="h-[70vh]" ref={listRef}>
        <div className="space-y-1 p-2">
          {filteredCPUs.map((cpu, index) => {
            const isSelected = selectedCPUId === cpu.id
            const isCompared = compareSelections.includes(cpu.id)

            return (
              <div
                key={cpu.id}
                className="space-y-1"
              >
                <Button
                  variant={isSelected ? 'secondary' : 'ghost'}
                  className={`h-auto w-full justify-start p-3 text-left ${
                    isSelected ? 'border-primary bg-muted ring-2 ring-primary' : ''
                  }`}
                  onClick={() => {
                    setSelectedCPU(cpu.id)
                    setFocusedIndex(index)
                  }}
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold">{cpu.name}</span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {cpu.manufacturer}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground flex flex-wrap gap-2">
                      {cpu.cores && <span>{cpu.cores}C/{cpu.threads}T</span>}
                      {cpu.tdp_w && <span>{formatTDP(cpu.tdp_w)}</span>}
                      {cpu.cpu_mark_multi && (
                        <span className="font-medium">
                          MT {cpu.cpu_mark_multi.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                </Button>
                <div className="flex items-center gap-2 px-3 py-1">
                  <Checkbox
                    id={`compare-${cpu.id}`}
                    checked={isCompared}
                    onCheckedChange={() => toggleCompare(cpu.id)}
                  />
                  <label
                    htmlFor={`compare-${cpu.id}`}
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
