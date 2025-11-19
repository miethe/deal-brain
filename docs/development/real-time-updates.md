---
title: "Real-Time Updates with Server-Sent Events (SSE)"
description: "Guide to using SSE for real-time UI updates in Deal Brain"
audience: [developers, ai-agents]
tags: [sse, real-time, events, react, fastapi]
created: 2025-11-19
updated: 2025-11-19
category: "developer-documentation"
status: published
related:
  - /docs/architecture/events-architecture.md
---

# Real-Time Updates with Server-Sent Events (SSE)

Deal Brain uses Server-Sent Events (SSE) to provide real-time UI updates when listings, valuations, and imports change.

## Architecture

### Backend (FastAPI)

**Event Publishing**:
- Services publish events to Redis pub/sub channel: `dealbrain:events`
- Events are automatically published on listing create/update/delete
- Valuation recalculation tasks publish completion events

**SSE Endpoint**:
- `/api/v1/events` - SSE endpoint for streaming events
- Handles 100+ concurrent connections
- Auto-reconnects on disconnect

### Frontend (React)

**Hooks**:
- `useEventStream` - Low-level hook for subscribing to specific events
- `useListingUpdates` - High-level hook for listing-related events
- `useImportUpdates` - Hook for import completion events

## Usage

### Basic Event Listening

```tsx
import { useEventStream } from "@/hooks/use-event-stream";

function MyComponent() {
  useEventStream("listing.created", (data) => {
    console.log("New listing:", data.listing_id);
  });

  return <div>Listening for events...</div>;
}
```

### Listing Updates with Auto-Invalidation

```tsx
import { useListingUpdates } from "@/hooks/use-event-stream";

function ListingsPage() {
  // Automatically invalidates React Query caches and shows toasts
  useListingUpdates({ showToasts: true });

  // Your listings query will auto-refresh when events are received
  const { data: listings } = useQuery({
    queryKey: ["listings"],
    queryFn: fetchListings,
  });

  return <ListingsTable data={listings} />;
}
```

### Import Completion Tracking

```tsx
import { useImportUpdates } from "@/hooks/use-event-stream";

function ImportPage() {
  useImportUpdates({
    onComplete: (data) => {
      console.log(`Created ${data.listings_created} listings`);
      // Navigate to listings page or show success message
    },
  });

  return <ImportForm />;
}
```

### Recalculation Progress Indicators

The `useListingUpdates` hook automatically shows toast notifications when valuations are recalculated:

```tsx
function Dashboard() {
  // Shows toast: "Valuations recalculated - N listing(s) recalculated"
  useListingUpdates({ showToasts: true });

  return <div>Dashboard content</div>;
}
```

For custom progress indicators:

```tsx
import { useEventStream } from "@/hooks/use-event-stream";
import { useState } from "react";

function CustomProgressIndicator() {
  const [isRecalculating, setIsRecalculating] = useState(false);

  useEventStream("valuation.recalculated", (data) => {
    setIsRecalculating(false);
    toast({
      title: "Recalculation complete",
      description: `${data.listing_ids.length} listings updated`,
    });
  });

  return (
    <>
      {isRecalculating && (
        <div className="fixed bottom-4 right-4 bg-blue-500 text-white p-4 rounded-lg">
          <Loader2 className="animate-spin" />
          <span>Recalculating valuations...</span>
        </div>
      )}
    </>
  );
}
```

## Event Types

### listing.created
Published when a new listing is created.

**Payload**:
```typescript
{
  listing_id: number;
  timestamp: string; // ISO 8601
}
```

### listing.updated
Published when a listing is updated.

**Payload**:
```typescript
{
  listing_id: number;
  changes: string[]; // Field names that changed
  timestamp: string;
}
```

### listing.deleted
Published when a listing is deleted.

**Payload**:
```typescript
{
  listing_id: number;
  timestamp: string;
}
```

### valuation.recalculated
Published when listing valuations are recalculated (background task).

**Payload**:
```typescript
{
  listing_ids: number[];
  timestamp: string;
}
```

### import.completed
Published when an import job completes.

**Payload**:
```typescript
{
  import_job_id: number;
  listings_created: number;
  listings_updated: number;
  timestamp: string;
}
```

## Auto-Recalculation Triggers

Valuations are automatically recalculated (async via Celery) when these fields change:
- `price_usd`
- `cpu_id`
- `gpu_id`
- `ram_gb` / `ram_capacity_gb`
- `primary_storage_gb`
- `secondary_storage_gb`
- `ruleset_id`

The recalculation happens in the background and publishes a `valuation.recalculated` event when complete.

## Performance

- SSE endpoint supports 100+ concurrent connections
- Events are fire-and-forget (non-blocking)
- Recalculation completes in <2s for 100 listings
- Auto-reconnects with 5s backoff on connection loss

## Error Handling

The hooks handle errors gracefully:
- Auto-reconnect on connection loss
- Failed events are logged but don't block UI
- Event parsing errors are caught and logged
- SSE unavailable falls back to polling (React Query refetch intervals)

## Testing

To test SSE in development:

1. Start the API: `make api`
2. Open browser console on any page using `useListingUpdates`
3. Create/update/delete a listing via API or UI
4. Watch console logs for SSE events
5. Observe React Query cache invalidations and UI updates

## Troubleshooting

**Events not received:**
- Check that API is running and SSE endpoint is accessible: `curl http://localhost:8000/api/v1/events`
- Check browser console for SSE connection errors
- Verify Redis is running: `docker ps | grep redis`

**Reconnection loops:**
- Check Redis pub/sub channel: `redis-cli SUBSCRIBE dealbrain:events`
- Verify no CORS errors in browser console
- Check API logs for SSE endpoint errors

**Stale data after events:**
- Verify React Query queryKey matches expected format
- Check that `useListingUpdates` is mounted in parent component
- Ensure query invalidation is working: enable React Query DevTools
