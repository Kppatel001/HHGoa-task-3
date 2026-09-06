import { api } from "./client";
import type { SystemStatus, VerificationResult } from "../types";

export interface TamperOverrides {
  caption?: string;
  title?: string;
  author?: string;
}

export async function verify(
  scanId: string,
  overrides?: TamperOverrides
): Promise<VerificationResult> {
  const { data } = await api.post<VerificationResult>(
    `/scan/${scanId}/verify`,
    overrides ?? {}
  );
  return data;
}

export async function getHealth() {
  const { data } = await api.get("/health");
  return data;
}

export async function getSystemStatus(): Promise<SystemStatus> {
  const { data } = await api.get<SystemStatus>("/status");
  return data;
}
