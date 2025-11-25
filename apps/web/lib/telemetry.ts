"use client";

type TelemetryDestination = "console" | "endpoint" | "all" | "disabled";
type TelemetryLevel = "debug" | "info" | "warn" | "error";

export interface TelemetryPayload {
  [key: string]: unknown;
}

interface TelemetryEvent {
  timestamp: string;
  level: TelemetryLevel;
  event: string;
  payload?: TelemetryPayload;
  session_id?: string;
  user?: TelemetryPayload;
}

const DESTINATION: TelemetryDestination =
  (process.env.NEXT_PUBLIC_TELEMETRY_DESTINATION as TelemetryDestination) || "console";
const ENDPOINT = process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT || "/api/telemetry/logs";
const SESSION_STORAGE_KEY = "dealbrain.telemetry.sessionId";

function ensureSessionId(): string | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    const existing = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (existing) return existing;
    const sessionId = crypto.randomUUID();
    window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    return sessionId;
  } catch {
    return undefined;
  }
}

async function postEvent(endpoint: string, event: TelemetryEvent): Promise<void> {
  if (typeof window === "undefined") return;
  const body = JSON.stringify(event);

  if (typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
    const blob = new Blob([body], { type: "application/json" });
    navigator.sendBeacon(endpoint, blob);
    return;
  }

  try {
    await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    });
  } catch {
    // Swallow network errors to avoid impacting UX.
  }
}

function logToConsole(level: TelemetryLevel, event: string, payload?: TelemetryPayload) {
  const message = `[telemetry] ${event}`;
  const data = payload ?? {};
  switch (level) {
    case "debug":
      console.debug(message, data);
      break;
    case "info":
      console.info(message, data);
      break;
    case "warn":
      console.warn(message, data);
      break;
    case "error":
      console.error(message, data);
      break;
  }
}

class TelemetryClient {
  private readonly destination: TelemetryDestination;
  private readonly endpoint: string;
  private readonly sessionId?: string;

  constructor(destination: TelemetryDestination = DESTINATION, endpoint: string = ENDPOINT) {
    this.destination = destination;
    this.endpoint = endpoint;
    this.sessionId = ensureSessionId();
  }

  debug(event: string, payload?: TelemetryPayload): void {
    this.dispatch("debug", event, payload);
  }

  info(event: string, payload?: TelemetryPayload): void {
    this.dispatch("info", event, payload);
  }

  warn(event: string, payload?: TelemetryPayload): void {
    this.dispatch("warn", event, payload);
  }

  error(event: string, payload?: TelemetryPayload): void {
    this.dispatch("error", event, payload);
  }

  private dispatch(level: TelemetryLevel, event: string, payload?: TelemetryPayload): void {
    if (this.destination === "disabled") return;

    const entry: TelemetryEvent = {
      timestamp: new Date().toISOString(),
      level,
      event,
      payload,
      session_id: this.sessionId,
    };

    if (this.destination === "console" || this.destination === "all" || typeof window === "undefined") {
      logToConsole(level, event, payload);
    }

    if (
      (this.destination === "endpoint" || this.destination === "all") &&
      typeof window !== "undefined"
    ) {
      postEvent(this.endpoint, entry);
    }
  }
}

export const telemetry = new TelemetryClient();

