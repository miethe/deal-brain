'use client';

import { useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import type { BulkImportStatus, PerRowImportStatus } from '@/hooks/useImportPolling';

export interface ImportNotificationsProps {
  bulkJobId: string; // Used for logging/debugging
}

/**
 * ImportNotifications - Toast notification component for import events
 *
 * This component listens for custom window events emitted during the import process
 * and displays toast notifications to inform users of important events:
 * - Partial imports detected (data needs manual completion)
 * - Import job completion (with success/partial/failure counts)
 *
 * The component renders nothing (toasts are rendered by the toast provider).
 * It uses the useToast hook for displaying notifications and properly cleans up
 * event listeners on unmount.
 *
 * Custom Events:
 * - 'import-partial-found': Emitted when a partial import is detected
 *   Detail: PerRowImportStatus with listing_id, url, quality='partial'
 * - 'import-job-complete': Emitted when the entire bulk import job completes
 *   Detail: BulkImportStatus with counts and final status
 *
 * Accessibility:
 * - Toasts are announced to screen readers via aria-live regions
 * - Auto-dismiss after default duration (5 seconds)
 * - Multiple toasts can appear without overlapping
 *
 * @param bulkJobId - Bulk import job ID for logging/debugging
 */
export function ImportNotifications({ bulkJobId }: ImportNotificationsProps) {
  const { toast } = useToast();

  useEffect(() => {
    /**
     * Handle partial import detected event
     * Shows a toast notification when a listing is imported with incomplete data
     */
    const handlePartialFound = (event: Event) => {
      const customEvent = event as CustomEvent<PerRowImportStatus>;
      const listing = customEvent.detail;

      toast({
        title: 'Data Needed',
        description: `Listing imported with partial data. Please complete the missing information.`,
        variant: 'default',
      });

      // Log for debugging
      console.log(`[ImportNotifications] Partial import detected:`, {
        bulkJobId,
        listingId: listing.listing_id,
        url: listing.url,
      });
    };

    /**
     * Handle import job complete event
     * Shows a toast notification with the final import results
     */
    const handleJobComplete = (event: Event) => {
      const customEvent = event as CustomEvent<BulkImportStatus>;
      const status = customEvent.detail;

      // Determine the appropriate message based on results
      let title: string;
      let description: string;
      let variant: 'default' | 'destructive' = 'default';

      if (status.failed === status.total_urls) {
        // All imports failed
        title = 'Import Failed';
        description = `All ${status.total_urls} import${status.total_urls !== 1 ? 's' : ''} failed. Please check the URLs and try again.`;
        variant = 'destructive';
      } else if (status.partial > 0 && status.success === 0) {
        // Only partial imports, no full successes
        title = 'Import Complete - Data Needed';
        description = `${status.partial} listing${status.partial !== 1 ? 's' : ''} imported with partial data. Please complete the missing information.`;
      } else if (status.partial > 0) {
        // Mixed results with some partials
        title = 'Import Complete';
        description = `Successfully imported ${status.success} listing${status.success !== 1 ? 's' : ''}, ${status.partial} need${status.partial === 1 ? 's' : ''} more data${status.failed > 0 ? `, ${status.failed} failed` : ''}.`;
      } else if (status.success > 0) {
        // All successful imports
        title = 'Import Complete';
        description = `Successfully imported ${status.success} listing${status.success !== 1 ? 's' : ''}${status.failed > 0 ? `, ${status.failed} failed` : ''}.`;
      } else {
        // Fallback (shouldn't happen)
        title = 'Import Complete';
        description = `Import job completed with ${status.completed} of ${status.total_urls} processed.`;
      }

      toast({
        title,
        description,
        variant,
      });

      // Log for debugging
      console.log(`[ImportNotifications] Import job complete:`, {
        bulkJobId,
        status: status.status,
        total: status.total_urls,
        success: status.success,
        partial: status.partial,
        failed: status.failed,
      });
    };

    // Add event listeners
    window.addEventListener('import-partial-found', handlePartialFound);
    window.addEventListener('import-job-complete', handleJobComplete);

    // Cleanup on unmount
    return () => {
      window.removeEventListener('import-partial-found', handlePartialFound);
      window.removeEventListener('import-job-complete', handleJobComplete);
    };
  }, [bulkJobId, toast]);

  // Render nothing - toasts are rendered by the toast provider
  return null;
}
