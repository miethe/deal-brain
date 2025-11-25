"use client";

import { useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { API_URL } from "@/lib/utils";
import { toast } from "./use-toast";

/**
 * Event types supported by the SSE stream
 */
export type EventType =
  | "listing.created"
  | "listing.updated"
  | "listing.deleted"
  | "valuation.recalculated"
  | "import.completed"
  | "import.progress";

/**
 * Event data payloads for different event types
 */
export interface ListingCreatedData {
  listing_id: number;
  timestamp: string;
}

export interface ListingUpdatedData {
  listing_id: number;
  changes: string[];
  timestamp: string;
}

export interface ListingDeletedData {
  listing_id: number;
  timestamp: string;
}

export interface ValuationRecalculatedData {
  listing_ids: number[];
  timestamp: string;
}

export interface ImportCompletedData {
  import_job_id: number;
  listings_created: number;
  listings_updated: number;
  timestamp: string;
}

export interface ImportProgressData {
  job_id: string;
  progress_pct: number;
  status: string;
  message: string;
  timestamp?: string;
}

/**
 * Hook for subscribing to Server-Sent Events (SSE) from the API.
 *
 * Automatically manages EventSource connection lifecycle, handles reconnection,
 * and cleans up on unmount.
 *
 * @param eventType - The event type to listen for
 * @param handler - Callback function to handle received events
 * @param options - Optional configuration
 *
 * @example
 * ```tsx
 * useEventStream('listing.created', (data) => {
 *   console.log('New listing created:', data.listing_id)
 * })
 * ```
 */
export function useEventStream<T = unknown>(
  eventType: EventType,
  handler: (data: T) => void,
  options?: {
    enabled?: boolean;
    reconnectDelay?: number;
  }
) {
  const { enabled = true, reconnectDelay = 5000 } = options || {};
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const handlerRef = useRef(handler);

  // Keep handler ref up to date
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  const connect = useCallback(() => {
    if (!enabled) return;

    // Create EventSource connection
    const eventSource = new EventSource(`${API_URL}/api/v1/events`);
    eventSourceRef.current = eventSource;

    // Listen for specific event type
    eventSource.addEventListener(eventType, (event) => {
      try {
        const data = JSON.parse(event.data) as T;
        handlerRef.current(data);
      } catch (error) {
        console.error("Failed to parse SSE event data:", error);
      }
    });

    // Handle connection open
    eventSource.addEventListener("open", () => {
      console.log(`[SSE] Connected to event stream`);
    });

    // Handle errors and reconnect
    eventSource.addEventListener("error", (error) => {
      console.error("[SSE] Connection error:", error);
      eventSource.close();

      // Reconnect after delay
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log(`[SSE] Reconnecting after ${reconnectDelay}ms...`);
        connect();
      }, reconnectDelay);
    });
  }, [eventType, enabled, reconnectDelay]);

  useEffect(() => {
    if (!enabled) {
      // Clean up if disabled
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      return;
    }

    connect();

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [connect, enabled]);
}

/**
 * Hook for listening to listing-related events and automatically
 * invalidating React Query caches.
 *
 * Handles:
 * - listing.created: Invalidates listings list
 * - listing.updated: Invalidates specific listing and list
 * - listing.deleted: Invalidates listings list
 * - valuation.recalculated: Invalidates affected listings
 *
 * @param options - Optional configuration
 *
 * @example
 * ```tsx
 * function ListingsPage() {
 *   useListingUpdates({ showToasts: true })
 *   // ...
 * }
 * ```
 */
export function useListingUpdates(options?: {
  enabled?: boolean;
  showToasts?: boolean;
}) {
  const { enabled = true, showToasts = false } = options || {};
  const queryClient = useQueryClient();

  // Listen for listing.created events
  useEventStream<ListingCreatedData>(
    "listing.created",
    (data) => {
      // Invalidate listings query to refetch
      queryClient.invalidateQueries({ queryKey: ["listings"] });

      if (showToasts) {
        toast({
          title: "New listing added",
          description: `Listing #${data.listing_id} was created`,
        });
      }
    },
    { enabled }
  );

  // Listen for listing.updated events
  useEventStream<ListingUpdatedData>(
    "listing.updated",
    (data) => {
      // Invalidate specific listing
      queryClient.invalidateQueries({
        queryKey: ["listing", data.listing_id],
      });
      // Invalidate listings list (in case it affects sorting/filtering)
      queryClient.invalidateQueries({ queryKey: ["listings"] });

      if (showToasts) {
        toast({
          title: "Listing updated",
          description: `Listing #${data.listing_id} was updated`,
        });
      }
    },
    { enabled }
  );

  // Listen for listing.deleted events
  useEventStream<ListingDeletedData>(
    "listing.deleted",
    (data) => {
      // Invalidate listings query to refetch
      queryClient.invalidateQueries({ queryKey: ["listings"] });

      if (showToasts) {
        toast({
          title: "Listing deleted",
          description: `Listing #${data.listing_id} was deleted`,
          variant: "destructive",
        });
      }
    },
    { enabled }
  );

  // Listen for valuation.recalculated events
  useEventStream<ValuationRecalculatedData>(
    "valuation.recalculated",
    (data) => {
      // Invalidate affected listings
      data.listing_ids.forEach((id) => {
        queryClient.invalidateQueries({ queryKey: ["listing", id] });
      });
      // Invalidate listings list
      queryClient.invalidateQueries({ queryKey: ["listings"] });

      if (showToasts) {
        toast({
          title: "Valuations recalculated",
          description: `${data.listing_ids.length} listing(s) recalculated`,
        });
      }
    },
    { enabled }
  );
}

/**
 * Hook for listening to import progress events for a specific job.
 *
 * Listens for real-time progress updates via SSE and calls the onProgress
 * callback with the latest progress data. Automatically filters events to
 * only process those matching the provided jobId.
 *
 * @param jobId - The job ID to listen for progress updates (null disables listening)
 * @param onProgress - Callback to handle progress updates
 *
 * @example
 * ```tsx
 * function ImportProgress() {
 *   const [jobId, setJobId] = useState<string | null>(null);
 *
 *   useImportProgress(jobId, (data) => {
 *     console.log(`Progress: ${data.progress_pct}%`)
 *   });
 * }
 * ```
 */
export function useImportProgress(
  jobId: string | null,
  onProgress: (data: ImportProgressData) => void
) {
  const onProgressRef = useRef(onProgress);

  // Keep callback ref up to date
  useEffect(() => {
    onProgressRef.current = onProgress;
  }, [onProgress]);

  useEventStream<ImportProgressData>(
    "import.progress",
    useCallback(
      (data) => {
        // Filter to only process events for the specified job
        if (jobId && data.job_id === jobId) {
          onProgressRef.current(data);
        }
      },
      [jobId]
    ),
    {
      enabled: jobId !== null && jobId !== undefined,
    }
  );
}

/**
 * Hook for listening to import completion events.
 *
 * @example
 * ```tsx
 * function ImportPage() {
 *   useImportUpdates({
 *     onComplete: (data) => {
 *       console.log(`Import ${data.import_job_id} completed`)
 *     }
 *   })
 * }
 * ```
 */
export function useImportUpdates(options?: {
  enabled?: boolean;
  onComplete?: (data: ImportCompletedData) => void;
}) {
  const { enabled = true, onComplete } = options || {};
  const queryClient = useQueryClient();

  useEventStream<ImportCompletedData>(
    "import.completed",
    (data) => {
      // Invalidate listings query
      queryClient.invalidateQueries({ queryKey: ["listings"] });

      toast({
        title: "Import completed",
        description: `Created ${data.listings_created} listing(s), updated ${data.listings_updated}`,
      });

      onComplete?.(data);
    },
    { enabled }
  );
}
