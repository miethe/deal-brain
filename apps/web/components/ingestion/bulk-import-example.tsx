/**
 * Example usage of BulkImportDialog component
 *
 * This file demonstrates how to integrate the bulk URL import feature
 * into your application.
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { BulkImportDialog } from './bulk-import-dialog';
import { Upload } from 'lucide-react';
import { telemetry } from '@/lib/telemetry';
import type { BulkIngestionStatusResponse, BulkImportError } from './bulk-import-types';

export function BulkImportExample() {
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleSuccess = (result: BulkIngestionStatusResponse) => {
    telemetry.info('frontend.import.bulk.success', {
      total: result.total_urls,
      success: result.success,
      failed: result.failed,
    });

    // Optionally close dialog after completion
    // setDialogOpen(false);
  };

  const handleError = (error: BulkImportError) => {
    telemetry.error('frontend.import.bulk.failed', {
      message: error?.message ?? 'Unknown error',
    });
    // Handle error (show toast notification, etc.)
  };

  return (
    <>
      <Button onClick={() => setDialogOpen(true)}>
        <Upload className="h-4 w-4 mr-2" />
        Bulk Import URLs
      </Button>

      <BulkImportDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={handleSuccess}
        onError={handleError}
      />
    </>
  );
}

/**
 * Usage in a page:
 *
 * ```tsx
 * import { BulkImportExample } from '@/components/ingestion/bulk-import-example';
 *
 * export default function ImportPage() {
 *   return (
 *     <div>
 *       <h1>Import Listings</h1>
 *       <BulkImportExample />
 *     </div>
 *   );
 * }
 * ```
 */
