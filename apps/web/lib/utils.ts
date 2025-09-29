import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  const headers = new Headers(init?.headers);
  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });
  const text = await response.text();
  let parsed: unknown;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch (error) {
      parsed = text;
    }
  }

  if (!response.ok) {
    let detail = text || `API request failed: ${response.status}`;
    if (parsed && typeof parsed === "object") {
      const candidate = (parsed as Record<string, unknown>).detail ?? (parsed as Record<string, unknown>).message;
      if (typeof candidate === "string") {
        detail = candidate;
      }
    } else if (typeof parsed === "string") {
      detail = parsed;
    }
    throw new ApiError(detail, response.status, parsed);
  }

  if (parsed === undefined) {
    return undefined as T;
  }
  return parsed as T;
}
