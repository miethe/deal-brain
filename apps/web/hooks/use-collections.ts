/**
 * React Query hooks for Collections API
 *
 * Provides hooks for fetching and managing collections:
 * - useCollections: Fetch user's collections with pagination
 * - useCollection: Fetch single collection with items
 * - useCreateCollection: Create a new collection
 * - useUpdateCollectionItem: Update collection item (status, notes, position)
 * - useRemoveCollectionItem: Remove item from collection
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import type {
  Collection,
  CollectionItem,
  CollectionWithItems,
  CollectionsListResponse,
  CreateCollectionPayload,
  UpdateCollectionItemPayload,
  UpdateCollectionVisibilityPayload,
  DiscoverCollectionsParams,
  DiscoverCollectionsResponse,
  CopyCollectionPayload,
} from "@/types/collections";

// ============================================================================
// Query Hooks (Fetching)
// ============================================================================

interface UseCollectionsOptions {
  limit?: number;
  offset?: number;
}

/**
 * Fetch user's collections with pagination
 *
 * @param options - Pagination options (limit, offset)
 * @returns Query result with collections array and total count
 */
export function useCollections(options: UseCollectionsOptions = {}) {
  const { limit = 20, offset = 0 } = options;

  return useQuery({
    queryKey: ["collections", { limit, offset }],
    queryFn: () =>
      apiFetch<CollectionsListResponse>(
        `/v1/collections?limit=${limit}&offset=${offset}`
      ),
    staleTime: 5 * 60 * 1000, // 5 minutes - collections change infrequently
  });
}

/**
 * Fetch a single collection with all its items
 *
 * @param collectionId - The collection ID
 * @returns Query result with full collection including items
 */
export function useCollection(collectionId: number | string) {
  return useQuery({
    queryKey: ["collections", collectionId],
    queryFn: () =>
      apiFetch<CollectionWithItems>(`/v1/collections/${collectionId}`),
    staleTime: 2 * 60 * 1000, // 2 minutes - workspace data changes more frequently
  });
}

/**
 * Discover public collections with search and filters
 *
 * @param params - Search and filter parameters
 * @returns Query result with discovered collections
 */
export function useDiscoverCollections(params: DiscoverCollectionsParams = {}) {
  const { search, owner_filter, sort = "recent", limit = 20, offset = 0 } = params;

  const queryParams = new URLSearchParams();
  if (search) queryParams.set("search", search);
  if (owner_filter) queryParams.set("owner_filter", owner_filter);
  queryParams.set("sort", sort);
  queryParams.set("limit", String(limit));
  queryParams.set("offset", String(offset));

  return useQuery({
    queryKey: ["collections", "discover", params],
    queryFn: () =>
      apiFetch<DiscoverCollectionsResponse>(
        `/v1/collections/discover?${queryParams.toString()}`
      ),
    staleTime: 1 * 60 * 1000, // 1 minute - discovery data changes more frequently
  });
}

// ============================================================================
// Mutation Hooks (Creating, Updating, Deleting)
// ============================================================================

interface UseCreateCollectionOptions {
  onSuccess?: (collection: Collection) => void;
}

/**
 * Create a new collection
 *
 * Automatically invalidates collections cache and shows toast notification
 */
export function useCreateCollection(options?: UseCreateCollectionOptions) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: CreateCollectionPayload) => {
      return apiFetch<Collection>("/v1/collections", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onError: (err) => {
      const errorMessage =
        err instanceof ApiError ? err.message : "Failed to create collection";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: (collection) => {
      // Invalidate all collections queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ["collections"] });

      toast({
        title: "Collection created",
        description: `"${collection.name}" has been created successfully.`,
      });

      options?.onSuccess?.(collection);
    },
  });
}

interface UseUpdateCollectionItemOptions {
  collectionId: number | string;
  onSuccess?: (item: CollectionItem) => void;
}

/**
 * Update a collection item (status, notes, position)
 *
 * Automatically invalidates collection cache and shows toast on error
 */
export function useUpdateCollectionItem(
  options: UseUpdateCollectionItemOptions
) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { collectionId } = options;

  return useMutation({
    mutationFn: async ({
      itemId,
      data,
    }: {
      itemId: number;
      data: UpdateCollectionItemPayload;
    }) => {
      return apiFetch<CollectionItem>(
        `/v1/collections/${collectionId}/items/${itemId}`,
        {
          method: "PATCH",
          body: JSON.stringify(data),
        }
      );
    },
    onError: (err) => {
      const errorMessage =
        err instanceof ApiError ? err.message : "Failed to update item";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: (item) => {
      // Invalidate the specific collection query to refresh
      queryClient.invalidateQueries({ queryKey: ["collections", collectionId] });

      options?.onSuccess?.(item);
    },
  });
}

interface UseRemoveCollectionItemOptions {
  collectionId: number | string;
  onSuccess?: () => void;
}

/**
 * Remove an item from a collection
 *
 * Automatically invalidates collection cache and shows toast notification
 */
export function useRemoveCollectionItem(
  options: UseRemoveCollectionItemOptions
) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { collectionId } = options;

  return useMutation({
    mutationFn: async (itemId: number) => {
      await apiFetch(`/v1/collections/${collectionId}/items/${itemId}`, {
        method: "DELETE",
      });
    },
    onError: (err) => {
      const errorMessage =
        err instanceof ApiError ? err.message : "Failed to remove item";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      // Invalidate queries to refresh
      queryClient.invalidateQueries({ queryKey: ["collections", collectionId] });
      queryClient.invalidateQueries({ queryKey: ["collections"] }); // Update item counts

      toast({
        title: "Item removed",
        description: "The item has been removed from the collection.",
      });

      options?.onSuccess?.();
    },
  });
}

interface UseUpdateCollectionVisibilityOptions {
  collectionId: number | string;
  onSuccess?: (collection: Collection) => void;
}

/**
 * Update collection visibility setting
 *
 * Automatically invalidates collection cache and shows toast notification
 */
export function useUpdateCollectionVisibility(
  options: UseUpdateCollectionVisibilityOptions
) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { collectionId } = options;

  return useMutation({
    mutationFn: async (data: UpdateCollectionVisibilityPayload) => {
      return apiFetch<Collection>(
        `/v1/collections/${collectionId}/visibility`,
        {
          method: "PATCH",
          body: JSON.stringify(data),
        }
      );
    },
    onError: (err) => {
      const errorMessage =
        err instanceof ApiError ? err.message : "Failed to update visibility";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: (collection) => {
      // Invalidate queries to refresh
      queryClient.invalidateQueries({ queryKey: ["collections", collectionId] });
      queryClient.invalidateQueries({ queryKey: ["collections"] });

      toast({
        title: "Visibility updated",
        description: `Collection is now ${collection.visibility}.`,
      });

      options?.onSuccess?.(collection);
    },
  });
}

interface UseCopyCollectionOptions {
  onSuccess?: (collection: Collection) => void;
}

/**
 * Copy a collection to current user's workspace
 *
 * Automatically invalidates collections cache and shows toast notification
 */
export function useCopyCollection(options?: UseCopyCollectionOptions) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: CopyCollectionPayload) => {
      return apiFetch<Collection>("/v1/collections/copy", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onError: (err) => {
      const errorMessage =
        err instanceof ApiError ? err.message : "Failed to copy collection";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: (collection) => {
      // Invalidate all collections queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ["collections"] });

      toast({
        title: "Collection copied",
        description: `"${collection.name}" has been copied to your workspace.`,
      });

      options?.onSuccess?.(collection);
    },
  });
}
