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
