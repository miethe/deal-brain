"use client";

import { useQuery } from "@tanstack/react-query";
import { AdapterCard } from "./adapter-card";
import { fetchAllAdapters } from "../../lib/api/adapter-settings";
import { ApiError } from "../../lib/utils";

export function AdapterSettings() {
  const { data: adapters, isLoading, error, refetch } = useQuery({
    queryKey: ["adapters"],
    queryFn: fetchAllAdapters,
    refetchInterval: 30000, // Poll every 30 seconds for real-time metrics updates
    retry: 3,
  });

  if (isLoading) {
    return (
      <div className="space-y-8" aria-busy="true" aria-label="Loading adapter settings">
        <section>
          <h1 className="text-3xl font-semibold">Adapter Settings</h1>
          <p className="text-muted-foreground">
            Configure URL ingestion adapters and monitor their performance.
          </p>
        </section>

        <div className="grid gap-6 md:grid-cols-2">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="rounded-lg border bg-card p-6 shadow-sm"
            >
              <div className="space-y-4">
                <div className="h-6 w-32 animate-pulse rounded bg-muted" />
                <div className="h-4 w-48 animate-pulse rounded bg-muted" />
                <div className="space-y-2">
                  <div className="h-10 w-full animate-pulse rounded bg-muted" />
                  <div className="h-10 w-full animate-pulse rounded bg-muted" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    const errorMessage =
      error instanceof ApiError
        ? error.message
        : "Failed to load adapter settings. Please try again.";

    return (
      <div className="space-y-8">
        <section>
          <h1 className="text-3xl font-semibold">Adapter Settings</h1>
          <p className="text-muted-foreground">
            Configure URL ingestion adapters and monitor their performance.
          </p>
        </section>

        <div
          className="rounded-lg border border-destructive bg-destructive/10 p-6"
          role="alert"
          aria-live="assertive"
        >
          <div className="flex flex-col gap-4">
            <div>
              <h3 className="text-lg font-semibold text-destructive">Error Loading Adapters</h3>
              <p className="text-sm text-destructive/90">{errorMessage}</p>
            </div>
            <div>
              <button
                onClick={() => refetch()}
                className="rounded-md bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground hover:bg-destructive/90"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!adapters || adapters.length === 0) {
    return (
      <div className="space-y-8">
        <section>
          <h1 className="text-3xl font-semibold">Adapter Settings</h1>
          <p className="text-muted-foreground">
            Configure URL ingestion adapters and monitor their performance.
          </p>
        </section>

        <div className="rounded-lg border border-dashed p-12 text-center">
          <p className="text-sm text-muted-foreground">
            No adapters configured. Contact system administrator.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-semibold">Adapter Settings</h1>
        <p className="text-muted-foreground">
          Configure URL ingestion adapters and monitor their performance. Metrics update automatically
          every 30 seconds.
        </p>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        {adapters.map((adapter) => (
          <AdapterCard key={adapter.adapter_id} adapter={adapter} />
        ))}
      </div>

      <div className="rounded-lg border bg-muted/50 p-4">
        <h3 className="mb-2 text-sm font-semibold">Configuration Notes</h3>
        <ul className="space-y-1 text-sm text-muted-foreground">
          <li className="flex gap-2">
            <span className="text-primary">•</span>
            <span>
              <strong>Timeout:</strong> Maximum time (in seconds) to wait for a response from the adapter.
              Higher values reduce timeout errors but increase wait time.
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-primary">•</span>
            <span>
              <strong>Retries:</strong> Number of automatic retry attempts on failure. Exponential backoff
              is applied between retries.
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-primary">•</span>
            <span>
              <strong>Success Rate:</strong> Percentage of successful extractions in the last 24 hours.
              Green (≥95%), yellow (≥80%), red (&lt;80%).
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-primary">•</span>
            <span>
              <strong>Field Completeness:</strong> Average percentage of required fields successfully
              extracted per listing.
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
}
