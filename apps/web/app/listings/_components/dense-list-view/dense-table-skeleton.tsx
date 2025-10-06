import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

/**
 * Skeleton loader for Dense Table view
 * Shows 8 placeholder rows matching the table layout
 */
export const DenseTableSkeleton = React.memo(function DenseTableSkeleton() {
  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <div className="h-4 w-4 animate-pulse rounded bg-muted" />
            </TableHead>
            <TableHead>Title</TableHead>
            <TableHead>CPU</TableHead>
            <TableHead className="text-right">Price</TableHead>
            <TableHead className="text-right">Adjusted</TableHead>
            <TableHead className="text-right">$/ST</TableHead>
            <TableHead className="text-right">$/MT</TableHead>
            <TableHead className="w-32 text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: 8 }).map((_, index) => (
            <TableRow key={index}>
              {/* Checkbox column */}
              <TableCell>
                <div className="h-4 w-4 animate-pulse rounded bg-muted" />
              </TableCell>

              {/* Title column */}
              <TableCell>
                <div className="space-y-1">
                  <div className="h-4 w-48 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-32 animate-pulse rounded bg-muted" />
                </div>
              </TableCell>

              {/* CPU column */}
              <TableCell>
                <div className="space-y-1">
                  <div className="h-4 w-36 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-28 animate-pulse rounded bg-muted" />
                </div>
              </TableCell>

              {/* Price column */}
              <TableCell className="text-right">
                <div className="ml-auto h-4 w-20 animate-pulse rounded bg-muted" />
              </TableCell>

              {/* Adjusted column */}
              <TableCell className="text-right">
                <div className="ml-auto h-4 w-20 animate-pulse rounded bg-muted" />
              </TableCell>

              {/* $/ST column */}
              <TableCell className="text-right">
                <div className="ml-auto h-4 w-16 animate-pulse rounded bg-muted" />
              </TableCell>

              {/* $/MT column */}
              <TableCell className="text-right">
                <div className="ml-auto h-4 w-16 animate-pulse rounded bg-muted" />
              </TableCell>

              {/* Actions column */}
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-2">
                  <div className="h-8 w-8 animate-pulse rounded bg-muted" />
                  <div className="h-8 w-8 animate-pulse rounded bg-muted" />
                  <div className="h-8 w-8 animate-pulse rounded bg-muted" />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
});
