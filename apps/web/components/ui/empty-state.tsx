import React from 'react';
import { LucideIcon, PackageOpen, SearchX } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface EmptyStateProps {
  /**
   * Icon to display (defaults to PackageOpen)
   */
  icon?: LucideIcon;

  /**
   * Heading text
   */
  heading: string;

  /**
   * Description text
   */
  description: string;

  /**
   * Optional CTA button
   */
  action?: {
    label: string;
    onClick: () => void;
  };

  /**
   * Minimum height (defaults to 400px)
   */
  minHeight?: string;
}

/**
 * Empty State Component
 *
 * Reusable component for displaying empty states with optional CTA.
 * Used across catalog views when no listings are present.
 */
export const EmptyState = React.memo(function EmptyState({
  icon: Icon = PackageOpen,
  heading,
  description,
  action,
  minHeight = '400px',
}: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 p-8 text-center"
      style={{ minHeight }}
    >
      <div className="space-y-4">
        <Icon className="mx-auto h-12 w-12 text-muted-foreground" />
        <div className="space-y-2">
          <h3 className="text-lg font-medium">{heading}</h3>
          <p className="mx-auto max-w-md text-sm text-muted-foreground">
            {description}
          </p>
        </div>
        {action && (
          <Button onClick={action.onClick}>
            {action.label}
          </Button>
        )}
      </div>
    </div>
  );
});

/**
 * Predefined empty state for "no listings at all"
 */
export function NoListingsEmptyState({
  onAddListing,
}: {
  onAddListing?: () => void;
}) {
  return (
    <EmptyState
      icon={PackageOpen}
      heading="No listings yet"
      description="Get started by adding your first listing to compare deals and find the best value."
      action={
        onAddListing
          ? {
              label: 'Add Listing',
              onClick: onAddListing,
            }
          : undefined
      }
    />
  );
}

/**
 * Predefined empty state for "no results from filters"
 */
export function NoFilterResultsEmptyState() {
  return (
    <EmptyState
      icon={SearchX}
      heading="No listings match your filters"
      description="Try adjusting your filters to see more results, or clear all filters to start over."
    />
  );
}
