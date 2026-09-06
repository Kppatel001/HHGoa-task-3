import { api } from "./client";
import type { BlockchainResult, BlockchainRecordRow, Fingerprint } from "../types";

export async function generateFingerprint(scanId: string): Promise<Fingerprint> {
  const { data } = await api.post<Fingerprint>(`/scan/${scanId}/fingerprint`);
  return data;
}

export async function registerBlockchain(scanId: string): Promise<BlockchainResult> {
  const { data } = await api.post<BlockchainResult>(`/scan/${scanId}/blockchain`);
  return data;
}

export async function listRecords(): Promise<{
  records: BlockchainRecordRow[];
  explorer?: string | null;
}> {
  const { data } = await api.get("/blockchain/records");
  return data;
}

export async function blockchainStatus() {
  const { data } = await api.get("/blockchain/status");
  return data;
}
