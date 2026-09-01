import axios from "axios";

// Same-origin "/api" in dev is proxied to the backend by Vite (see vite.config).
// Override with VITE_API_BASE_URL for a deployed backend.
const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";

export const api = axios.create({ baseURL, timeout: 180000 });

export interface ApiError {
  code: string;
  message: string;
}

export function parseError(err: unknown): ApiError {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (detail && typeof detail === "object" && "message" in detail) {
      return detail as ApiError;
    }
    if (typeof detail === "string") return { code: "error", message: detail };
    return { code: "network", message: err.message };
  }
  return { code: "unknown", message: String(err) };
}

// EventSource URL for SSE (bypasses axios). Respects VITE_API_BASE_URL.
export function eventsUrl(scanId: string): string {
  return `${baseURL}/scan/${scanId}/events`;
}
