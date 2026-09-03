import { api } from "./client";
import type { FaceAnalysis } from "../types";

export interface ScanCreated {
  scan_id: string;
  status: string;
}

export async function createScan(file: File): Promise<ScanCreated> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<ScanCreated>("/scan", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function analyzeFace(scanId: string): Promise<FaceAnalysis> {
  const { data } = await api.post<FaceAnalysis>(`/scan/${scanId}/face`);
  return data;
}

export async function getScan(scanId: string) {
  const { data } = await api.get(`/scan/${scanId}`);
  return data;
}

// Single-request full pipeline (works on stateless/serverless hosts too):
// upload -> face -> search -> match -> fingerprint -> blockchain -> verify.
export async function runPipeline(file: File, query?: string, simulateTamper = false) {
  const form = new FormData();
  form.append("file", file);
  if (query) form.append("query", query);
  form.append("simulate_tamper", String(simulateTamper));
  const { data } = await api.post("/pipeline", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
