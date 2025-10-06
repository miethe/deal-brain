import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

/**
 * Skeleton loader for ListingCard component
 * Matches the layout of the actual card for smooth loading experience
 */
export const ListingCardSkeleton = React.memo(function ListingCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="space-y-2 pb-3">
        {/* Title skeleton */}
        <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />

        {/* Badges row skeleton */}
        <div className="flex flex-wrap gap-2">
          <div className="h-5 w-16 animate-pulse rounded-full bg-muted" />
          <div className="h-5 w-20 animate-pulse rounded-full bg-muted" />
          <div className="h-5 w-24 animate-pulse rounded-full bg-muted" />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Price section skeleton */}
        <div className="space-y-1">
          <div className="h-8 w-24 animate-pulse rounded bg-muted" />
          <div className="h-6 w-32 animate-pulse rounded bg-muted" />
        </div>

        {/* Performance badges skeleton */}
        <div className="grid grid-cols-2 gap-2">
          <div className="h-6 w-full animate-pulse rounded-full bg-muted" />
          <div className="h-6 w-full animate-pulse rounded-full bg-muted" />
          <div className="h-6 w-full animate-pulse rounded-full bg-muted" />
          <div className="h-6 w-full animate-pulse rounded-full bg-muted" />
        </div>

        {/* Metadata row skeleton */}
        <div className="flex items-center gap-2 text-sm">
          <div className="h-4 w-16 animate-pulse rounded bg-muted" />
          <div className="h-4 w-20 animate-pulse rounded bg-muted" />
          <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        </div>

        {/* Footer skeleton */}
        <div className="flex items-center justify-between pt-2">
          <div className="h-5 w-20 animate-pulse rounded-full bg-muted" />
          <div className="h-8 w-8 animate-pulse rounded bg-muted" />
        </div>
      </CardContent>
    </Card>
  );
});
