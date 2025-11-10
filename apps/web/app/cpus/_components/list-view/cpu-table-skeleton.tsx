import React from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'

/**
 * Skeleton loader for CPU Table view
 *
 * Shows 10 placeholder rows matching the table layout with shimmer animation.
 * Displays while CPU data is loading.
 */
export const CPUTableSkeleton = React.memo(function CPUTableSkeleton() {
  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="flex-1 min-w-[250px]">Name</TableHead>
            <TableHead className="w-[140px]">Manufacturer</TableHead>
            <TableHead className="w-[120px]">Socket</TableHead>
            <TableHead className="w-[120px] text-center">Cores/Threads</TableHead>
            <TableHead className="w-[80px] text-right">TDP</TableHead>
            <TableHead className="w-[100px] text-right">ST Mark</TableHead>
            <TableHead className="w-[100px] text-right">MT Mark</TableHead>
            <TableHead className="w-[100px] text-right">iGPU</TableHead>
            <TableHead className="w-[120px] text-center">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: 10 }).map((_, index) => (
            <TableRow key={index}>
              {/* Name column */}
              <TableCell className="min-w-[250px]">
                <div className="space-y-1">
                  <div className="h-4 w-56 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-24 animate-pulse rounded bg-muted" />
                </div>
              </TableCell>

              {/* Manufacturer column */}
              <TableCell className="w-[140px]">
                <div className="h-5 w-16 animate-pulse rounded bg-muted" />
              </TableCell>

              {/* Socket column */}
              <TableCell className="w-[120px]">
                <div className="h-4 w-20 animate-pulse rounded bg-muted" />
              </TableCell>

              {/* Cores/Threads column */}
              <TableCell className="w-[120px] text-center">
                <div className="h-4 w-16 mx-auto animate-pulse rounded bg-muted" />
              </TableCell>

              {/* TDP column */}
              <TableCell className="w-[80px] text-right">
                <div className="h-4 w-12 ml-auto animate-pulse rounded bg-muted" />
              </TableCell>

              {/* ST Mark column */}
              <TableCell className="w-[100px] text-right">
                <div className="h-5 w-20 ml-auto animate-pulse rounded bg-muted" />
              </TableCell>

              {/* MT Mark column */}
              <TableCell className="w-[100px] text-right">
                <div className="h-5 w-20 ml-auto animate-pulse rounded bg-muted" />
              </TableCell>

              {/* iGPU column */}
              <TableCell className="w-[100px] text-right">
                <div className="h-5 w-16 ml-auto animate-pulse rounded bg-muted" />
              </TableCell>

              {/* Actions column */}
              <TableCell className="w-[120px] text-center">
                <div className="h-8 w-24 mx-auto animate-pulse rounded bg-muted" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
})
