import React from 'react';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card';

/**
 * Skeleton loader for CPUCard component
 * Matches the layout of the actual card for smooth loading experience
 */
export const CPUCardSkeleton = React.memo(function CPUCardSkeleton() {
  return (
    <Card className="overflow-hidden h-full flex flex-col">
      <CardHeader className="pb-3">
        {/* CPU name skeleton */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 space-y-2">
            <div className="h-5 w-full animate-pulse rounded bg-muted" />
            <div className="h-5 w-20 animate-pulse rounded-full bg-muted" />
          </div>
          <div className="h-5 w-5 animate-pulse rounded bg-muted flex-shrink-0" />
        </div>
      </CardHeader>

      <CardContent className="pb-3 flex-1 space-y-3">
        {/* Specs grid skeleton */}
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1">
            <div className="h-4 w-16 animate-pulse rounded bg-muted" />
            <div className="h-4 w-20 animate-pulse rounded bg-muted" />
          </div>
          <div className="space-y-1">
            <div className="h-4 w-20 animate-pulse rounded bg-muted" />
            <div className="h-4 w-16 animate-pulse rounded bg-muted" />
          </div>
          <div className="space-y-1">
            <div className="h-4 w-12 animate-pulse rounded bg-muted" />
            <div className="h-4 w-16 animate-pulse rounded bg-muted" />
          </div>
          <div className="space-y-1">
            <div className="h-4 w-16 animate-pulse rounded bg-muted" />
            <div className="h-4 w-12 animate-pulse rounded bg-muted" />
          </div>
        </div>

        {/* Performance badges skeleton */}
        <div className="flex flex-wrap gap-1.5">
          <div className="h-6 w-20 animate-pulse rounded-full bg-muted" />
          <div className="h-6 w-20 animate-pulse rounded-full bg-muted" />
          <div className="h-6 w-24 animate-pulse rounded-full bg-muted" />
        </div>

        {/* Price targets skeleton */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="h-4 w-24 animate-pulse rounded bg-muted" />
            <div className="h-5 w-16 animate-pulse rounded-full bg-muted" />
          </div>
          <div className="grid grid-cols-3 gap-1.5">
            <div className="h-16 animate-pulse rounded bg-muted" />
            <div className="h-16 animate-pulse rounded bg-muted" />
            <div className="h-16 animate-pulse rounded bg-muted" />
          </div>
          <div className="h-3 w-32 mx-auto animate-pulse rounded bg-muted" />
        </div>

        {/* Value metrics skeleton */}
        <div className="space-y-1">
          <div className="h-4 w-24 animate-pulse rounded bg-muted" />
          <div className="space-y-0.5">
            <div className="flex justify-between">
              <div className="h-3 w-20 animate-pulse rounded bg-muted" />
              <div className="h-3 w-16 animate-pulse rounded bg-muted" />
            </div>
            <div className="flex justify-between">
              <div className="h-3 w-20 animate-pulse rounded bg-muted" />
              <div className="h-3 w-16 animate-pulse rounded bg-muted" />
            </div>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-3 border-t flex items-center justify-between">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="h-5 w-20 animate-pulse rounded-full bg-muted" />
      </CardFooter>
    </Card>
  );
});
