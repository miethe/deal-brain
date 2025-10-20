'use client';

import { SingleUrlImportForm } from '@/components/ingestion';
import { useRouter } from 'next/navigation';

export default function ImportPage() {
  const router = useRouter();

  return (
    <div className="container max-w-2xl py-8">
      <SingleUrlImportForm
        onSuccess={(result) => {
          console.log('Import successful:', result);
          // Optionally navigate to the listing
          // router.push(`/listings/${result.listingId}`);
        }}
        onError={(error) => {
          console.error('Import failed:', error);
        }}
      />
    </div>
  );
}
