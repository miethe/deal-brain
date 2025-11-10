/**
 * ImportNotifications Usage Examples
 *
 * This file demonstrates how to use the ImportNotifications component
 * in various scenarios throughout the application.
 */

import { ImportNotifications } from '@/components/imports';

/**
 * Example 1: Basic Usage in Import Dashboard
 *
 * Add ImportNotifications to your import dashboard or page to receive
 * toast notifications for import events.
 */
export function ImportDashboardExample() {
  const bulkJobId = 'bulk-job-abc123';

  return (
    <div>
      <h1>Import Dashboard</h1>

      {/* Import Notifications - renders nothing, just listens for events */}
      <ImportNotifications bulkJobId={bulkJobId} />

      {/* Your other import UI components */}
      <div>Import progress and controls...</div>
    </div>
  );
}

/**
 * Example 2: Combined with Import Polling
 *
 * Use ImportNotifications alongside useImportPolling for a complete
 * import monitoring solution.
 */
export function ImportWithPollingExample() {
  const bulkJobId = 'bulk-job-xyz789';

  // useImportPolling will emit events that ImportNotifications listens for
  // const { status, progressPercent } = useImportPolling({ bulkJobId });

  return (
    <div>
      {/* ImportNotifications listens for events emitted by useImportPolling */}
      <ImportNotifications bulkJobId={bulkJobId} />

      {/* Progress UI */}
      <div>
        {/* Progress bar, status cards, etc. */}
      </div>
    </div>
  );
}

/**
 * Example 3: Multiple Import Jobs
 *
 * You can have multiple ImportNotifications components for different jobs.
 * Each will only log its own bulkJobId but will show toasts for all events.
 */
export function MultipleImportsExample() {
  const jobs = ['job-1', 'job-2', 'job-3'];

  return (
    <div>
      {jobs.map((jobId) => (
        <div key={jobId}>
          <ImportNotifications bulkJobId={jobId} />
          {/* Job-specific UI */}
        </div>
      ))}
    </div>
  );
}

/**
 * Example 4: Testing Events Manually
 *
 * For testing or debugging, you can manually dispatch events to trigger toasts.
 */
export function ManualEventDispatchExample() {
  const bulkJobId = 'test-job';

  const triggerPartialEvent = () => {
    window.dispatchEvent(
      new CustomEvent('import-partial-found', {
        detail: {
          url: 'https://example.com/listing/123',
          status: 'complete',
          listing_id: 456,
          quality: 'partial',
          error: null,
        },
      })
    );
  };

  const triggerCompleteEvent = () => {
    window.dispatchEvent(
      new CustomEvent('import-job-complete', {
        detail: {
          bulk_job_id: bulkJobId,
          status: 'complete',
          total_urls: 10,
          completed: 10,
          success: 8,
          partial: 2,
          failed: 0,
          running: 0,
          queued: 0,
          per_row_status: [],
          offset: 0,
          limit: 100,
          has_more: false,
        },
      })
    );
  };

  return (
    <div>
      <ImportNotifications bulkJobId={bulkJobId} />

      <button onClick={triggerPartialEvent}>
        Test Partial Import Toast
      </button>
      <button onClick={triggerCompleteEvent}>
        Test Complete Import Toast
      </button>
    </div>
  );
}

/**
 * Expected Toast Messages:
 *
 * Partial Import Found:
 *   Title: "Data Needed"
 *   Description: "Listing imported with partial data. Please complete the missing information."
 *   Variant: default
 *
 * Import Complete (all success):
 *   Title: "Import Complete"
 *   Description: "Successfully imported 5 listings."
 *   Variant: default
 *
 * Import Complete (with partials):
 *   Title: "Import Complete"
 *   Description: "Successfully imported 7 listings, 3 need more data."
 *   Variant: default
 *
 * Import Complete (with failures):
 *   Title: "Import Complete"
 *   Description: "Successfully imported 7 listings, 3 need more data, 2 failed."
 *   Variant: default
 *
 * Import Complete (only partials):
 *   Title: "Import Complete - Data Needed"
 *   Description: "4 listings imported with partial data. Please complete the missing information."
 *   Variant: default
 *
 * Import Failed (all failed):
 *   Title: "Import Failed"
 *   Description: "All 3 imports failed. Please check the URLs and try again."
 *   Variant: destructive
 */
