/**
 * React Query hook for adding items to collections
 *
 * Provides a mutation hook for adding listings to collections with proper
 * error handling, toast notifications, and cache invalidation.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import type { CollectionItem } from "@/types/collections";

interface AddToCollectionPayload {
  listing_id: number;
  status?: "undecided" | "shortlisted" | "rejected" | "bought";
  notes?: string;
}

interface UseAddToCollectionOptions {
  collectionId: number;
  collectionName?: string;
  onSuccess?: (item: CollectionItem) => void;
}

/**
 * Add a listing to a collection
 *
 * Automatically invalidates relevant queries and shows toast notifications.
 * Handles 409 Conflict errors (item already in collection) gracefully.
 *
 * @param options - Collection ID and optional callbacks
 * @returns Mutation with addItem function
 */
export function useAddToCollection(options: UseAddToCollectionOptions) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { collectionId, collectionName, onSuccess } = options;

  return useMutation({
    mutationFn: async (data: AddToCollectionPayload) => {
      return apiFetch<CollectionItem>(
        `/v1/collections/${collectionId}/items`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        }
      );
    },
    onError: (err) => {
      // Handle 409 Conflict (item already in collection)
      if (err instanceof ApiError && err.status === 409) {
        toast({
          title: "Already in collection",
          description: collectionName
            ? `This listing is already in "${collectionName}".`
            : "This listing is already in the collection.",
          variant: "destructive",
        });
        return;
      }

      // Handle other errors
      const errorMessage =
        err instanceof ApiError
          ? err.message
          : "Failed to add item to collection";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: (item) => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ["collections", collectionId] });
      queryClient.invalidateQueries({ queryKey: ["collections"] }); // Update item counts

      // Show success toast
      toast({
        title: "Added to collection",
        description: collectionName
          ? `Added to "${collectionName}" successfully.`
          : "Item added to collection successfully.",
      });

      // Call optional success callback
      onSuccess?.(item);
    },
  });
}
