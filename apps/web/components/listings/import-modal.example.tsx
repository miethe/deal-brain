'use client';

/**
 * Example usage of ImportModal component
 *
 * This file demonstrates how to integrate the ImportModal
 * into any page or component in the application.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ImportModal } from './import-modal';
import { Plus } from 'lucide-react';

export function ImportModalExample() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleImportSuccess = () => {
    console.log('Import completed successfully!');
    // Optionally: refresh data, navigate to listings page, etc.
    // Example: router.push('/listings');
    // Example: queryClient.invalidateQueries(['listings']);
  };

  return (
    <div>
      {/* Trigger Button */}
      <Button onClick={() => setIsModalOpen(true)}>
        <Plus className="h-4 w-4 mr-2" />
        Import Listing
      </Button>

      {/* Import Modal */}
      <ImportModal
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        onSuccess={handleImportSuccess}
      />
    </div>
  );
}

/**
 * Integration Examples:
 *
 * 1. In a listings page header:
 * ```tsx
 * export default function ListingsPage() {
 *   const [importOpen, setImportOpen] = useState(false);
 *
 *   return (
 *     <div>
 *       <div className="flex justify-between">
 *         <h1>Listings</h1>
 *         <Button onClick={() => setImportOpen(true)}>Import</Button>
 *       </div>
 *       <ImportModal
 *         open={importOpen}
 *         onOpenChange={setImportOpen}
 *         onSuccess={() => {
 *           // Refresh listings table
 *           queryClient.invalidateQueries(['listings']);
 *         }}
 *       />
 *     </div>
 *   );
 * }
 * ```
 *
 * 2. In a dashboard with multiple actions:
 * ```tsx
 * export default function Dashboard() {
 *   const [importOpen, setImportOpen] = useState(false);
 *
 *   return (
 *     <div className="grid gap-4">
 *       <Card>
 *         <CardHeader>Quick Actions</CardHeader>
 *         <CardContent>
 *           <Button onClick={() => setImportOpen(true)}>
 *             Import New Listing
 *           </Button>
 *         </CardContent>
 *       </Card>
 *
 *       <ImportModal
 *         open={importOpen}
 *         onOpenChange={setImportOpen}
 *         onSuccess={() => {
 *           toast({
 *             title: 'Success',
 *             description: 'Import initiated successfully'
 *           });
 *         }}
 *       />
 *     </div>
 *   );
 * }
 * ```
 *
 * 3. In an empty state:
 * ```tsx
 * function EmptyListings() {
 *   const [importOpen, setImportOpen] = useState(false);
 *
 *   return (
 *     <div className="text-center py-12">
 *       <h3>No listings yet</h3>
 *       <Button onClick={() => setImportOpen(true)}>
 *         Import Your First Listing
 *       </Button>
 *       <ImportModal
 *         open={importOpen}
 *         onOpenChange={setImportOpen}
 *         onSuccess={() => router.push('/listings')}
 *       />
 *     </div>
 *   );
 * }
 * ```
 */
