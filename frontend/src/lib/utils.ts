import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function shortHash(h?: string | null, head = 8, tail = 6): string {
  if (!h) return "—";
  const clean = h.startsWith("0x") ? h.slice(2) : h;
  if (clean.length <= head + tail) return h;
  const prefix = h.startsWith("0x") ? "0x" : "";
  return `${prefix}${clean.slice(0, head)}…${clean.slice(-tail)}`;
}

export function pct(v?: number | null): string {
  if (v === null || v === undefined) return "—";
  return `${(v * 100).toFixed(2)}%`;
}

export function ms(v?: number | null): string {
  if (v === null || v === undefined) return "—";
  return v >= 1000 ? `${(v / 1000).toFixed(1)} s` : `${v} ms`;
}

export async function copy(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    /* clipboard unavailable */
  }
}

export function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}
