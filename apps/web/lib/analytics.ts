"use client";

import { telemetry } from "./telemetry";

type AnalyticsPayload = Record<string, unknown>;

export function track(event: string, payload: AnalyticsPayload = {}) {
  telemetry.info(`analytics.${event}`, payload);

  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("dealbrain-analytics", { detail: { event, payload } }));
  }
}

export type { AnalyticsPayload };
