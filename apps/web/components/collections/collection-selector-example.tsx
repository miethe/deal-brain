"use client";

/**
 * Example usage of CollectionSelectorModal
 *
 * This demonstrates how to integrate the collection selector modal
 * into various pages and components throughout the application.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { CollectionSelectorModal } from "./collection-selector-modal";
import { Heart, Plus } from "lucide-react";

/**
 * Example 1: From Public Deal Page
 * User clicks "Add to Collection" on a shared deal link
 */
export function PublicDealExample({ listingId }: { listingId: number }) {
  const [showSelector, setShowSelector] = useState(false);
  const router = useRouter();

  return (
    <>
      <Button onClick={() => setShowSelector(true)} variant="outline">
        <Heart className="h-4 w-4 mr-2" />
        Add to Collection
      </Button>

      <CollectionSelectorModal
        listingId={listingId}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onSuccess={(collectionId) => {
          // Optional: Navigate to the collection after adding
          router.push(`/collections/${collectionId}`);
        }}
      />
    </>
  );
}

/**
 * Example 2: From Listings Search Results
 * Quick add button on each listing card
 */
export function ListingCardExample({ listingId }: { listingId: number }) {
  const [showSelector, setShowSelector] = useState(false);

  return (
    <>
      <Button
        onClick={() => setShowSelector(true)}
        variant="ghost"
        size="sm"
        aria-label="Add to collection"
      >
        <Plus className="h-4 w-4" />
      </Button>

      <CollectionSelectorModal
        listingId={listingId}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        // No onSuccess - just show toast and stay on current page
      />
    </>
  );
}

/**
 * Example 3: From Listing Detail Page
 * Prominent "Add to Collection" action in the detail view
 */
export function ListingDetailExample({ listingId }: { listingId: number }) {
  const [showSelector, setShowSelector] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button onClick={() => setShowSelector(true)}>
          <Heart className="h-4 w-4 mr-2" />
          Save to Collection
        </Button>
        {/* Other action buttons... */}
      </div>

      <CollectionSelectorModal
        listingId={listingId}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onSuccess={(collectionId) => {
          console.log(`Added to collection ${collectionId}`);
          // Could update UI state, show additional actions, etc.
        }}
      />
    </div>
  );
}

/**
 * Example 4: Programmatic Trigger
 * Auto-open modal after importing a shared deal
 */
export function ImportedDealExample({
  listingId,
  autoOpen = false,
}: {
  listingId: number;
  autoOpen?: boolean;
}) {
  const [showSelector, setShowSelector] = useState(autoOpen);

  // Could be triggered by various events:
  // - After successfully importing a deal via URL
  // - After importing from share link
  // - After bulk import completion

  return (
    <CollectionSelectorModal
      listingId={listingId}
      isOpen={showSelector}
      onClose={() => setShowSelector(false)}
      onSuccess={(collectionId) => {
        // Update state, navigate, etc.
        console.log(`Imported deal added to collection ${collectionId}`);
      }}
    />
  );
}
