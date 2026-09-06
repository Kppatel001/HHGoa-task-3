import { api } from "./client";
import type { SearchSummary } from "../types";

export async function runSearch(scanId: string, query?: string): Promise<SearchSummary> {
  const { data } = await api.post<SearchSummary>(`/scan/${scanId}/search`, {
    query: query || null,
  });
  return data;
}

export async function getResults(scanId: string): Promise<SearchSummary> {
  const { data } = await api.get<SearchSummary>(`/scan/${scanId}/results`);
  return data;
}

export async function selectMatch(scanId: string, resultId: number) {
  const { data } = await api.post(`/scan/${scanId}/match`, { result_id: resultId });
  return data;
}
