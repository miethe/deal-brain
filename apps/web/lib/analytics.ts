"use client";

type AnalyticsPayload = Record<string, unknown>;

export function track(event: string, payload: AnalyticsPayload = {}) {
  if (process.env.NODE_ENV !== "production") {
    // eslint-disable-next-line no-console
    console.info(`[analytics] ${event}`, payload);
  }
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("dealbrain-analytics", { detail: { event, payload } }));
  }
}

export type { AnalyticsPayload };
