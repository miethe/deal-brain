'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Columns2, List, Rows } from 'lucide-react'
import { useCatalogStore } from '@/stores/catalog-store'

export const ViewSwitcher = React.memo(function ViewSwitcher() {
  const { activeView, setActiveView } = useCatalogStore()

  return (
    <div className="flex items-center gap-1 rounded-lg border bg-background p-1">
      <Button
        variant={activeView === 'grid' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => setActiveView('grid')}
        aria-label="Grid view"
      >
        <Columns2 className="h-4 w-4" />
        <span className="ml-2 hidden sm:inline">Grid</span>
      </Button>
      <Button
        variant={activeView === 'list' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => setActiveView('list')}
        aria-label="List view"
      >
        <List className="h-4 w-4" />
        <span className="ml-2 hidden sm:inline">List</span>
      </Button>
      <Button
        variant={activeView === 'master-detail' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => setActiveView('master-detail')}
        aria-label="Master-detail view"
      >
        <Rows className="h-4 w-4" />
        <span className="ml-2 hidden sm:inline">Compare</span>
      </Button>
    </div>
  )
})
