import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

/**
 * Skeleton loader for CPU Master-Detail view
 * Shows placeholder for split layout with master list and detail panel
 */
export const MasterDetailSkeleton = React.memo(function MasterDetailSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-10">
      {/* Master List Skeleton */}
      <div className="space-y-2 lg:col-span-4">
        <div className="rounded-lg border p-4">
          {/* Search bar skeleton */}
          <div className="mb-4 space-y-2">
            <div className="h-4 w-32 animate-pulse rounded bg-muted" />
            <div className="h-10 w-full animate-pulse rounded bg-muted" />
            <div className="h-3 w-48 animate-pulse rounded bg-muted" />
          </div>

          {/* CPU list items skeleton */}
          {Array.from({ length: 8 }).map((_, index) => (
            <div
              key={index}
              className="mb-2 space-y-2 rounded-lg border p-3 last:mb-0"
            >
              {/* Title and manufacturer row */}
              <div className="flex items-center justify-between">
                <div className="h-4 w-40 animate-pulse rounded bg-muted" />
                <div className="h-3 w-12 animate-pulse rounded bg-muted" />
              </div>

              {/* CPU specs row */}
              <div className="flex gap-2">
                <div className="h-3 w-16 animate-pulse rounded bg-muted" />
                <div className="h-3 w-12 animate-pulse rounded bg-muted" />
                <div className="h-3 w-20 animate-pulse rounded bg-muted" />
              </div>

              {/* Compare checkbox */}
              <div className="flex items-center gap-2 pt-1">
                <div className="h-4 w-4 animate-pulse rounded bg-muted" />
                <div className="h-3 w-24 animate-pulse rounded bg-muted" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detail Panel Skeleton */}
      <div className="lg:col-span-6">
        <Card>
          <CardHeader>
            {/* Title */}
            <div className="h-6 w-3/4 animate-pulse rounded bg-muted" />

            {/* Badges */}
            <div className="flex gap-2 pt-2">
              <div className="h-5 w-16 animate-pulse rounded-full bg-muted" />
              <div className="h-5 w-20 animate-pulse rounded-full bg-muted" />
              <div className="h-5 w-12 animate-pulse rounded-full bg-muted" />
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* KPI Metrics Grid */}
            <div className="grid grid-cols-2 gap-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="space-y-2 rounded-lg border p-3">
                  <div className="h-3 w-16 animate-pulse rounded bg-muted" />
                  <div className="h-6 w-20 animate-pulse rounded bg-muted" />
                </div>
              ))}
            </div>

            {/* Price Confidence */}
            <div className="space-y-2 rounded-lg border p-3">
              <div className="h-3 w-24 animate-pulse rounded bg-muted" />
              <div className="h-4 w-32 animate-pulse rounded bg-muted" />
            </div>

            {/* Performance Badges */}
            <div className="space-y-2">
              <div className="h-4 w-32 animate-pulse rounded bg-muted" />
              <div className="flex gap-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div
                    key={index}
                    className="h-6 w-24 animate-pulse rounded-full bg-muted"
                  />
                ))}
              </div>
            </div>

            {/* Specs Grid */}
            <div className="space-y-2">
              <div className="h-4 w-24 animate-pulse rounded bg-muted" />
              <div className="grid grid-cols-2 gap-3">
                {Array.from({ length: 6 }).map((_, index) => (
                  <div key={index} className="space-y-1">
                    <div className="h-3 w-20 animate-pulse rounded bg-muted" />
                    <div className="h-4 w-28 animate-pulse rounded bg-muted" />
                  </div>
                ))}
              </div>
            </div>

            {/* Performance Value */}
            <div className="space-y-2">
              <div className="h-4 w-32 animate-pulse rounded bg-muted" />
              <div className="grid grid-cols-2 gap-3">
                {Array.from({ length: 2 }).map((_, index) => (
                  <div key={index} className="space-y-1">
                    <div className="h-3 w-20 animate-pulse rounded bg-muted" />
                    <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
});
