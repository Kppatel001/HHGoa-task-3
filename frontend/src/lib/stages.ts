import type { StageStatus } from "../types";

export interface StageDef {
  key: string;
  label: string;
}

export const STAGES: StageDef[] = [
  { key: "upload", label: "Image Uploaded" },
  { key: "face", label: "Face Detection" },
  { key: "embedding", label: "Face Encoding" },
  { key: "search", label: "Web Search" },
  { key: "match", label: "Matching Content" },
  { key: "fingerprint", label: "Content Fingerprint" },
  { key: "blockchain", label: "Blockchain Registration" },
  { key: "verify", label: "Verification" },
];

export type StageMap = Record<string, StageStatus>;

export function initialStages(): StageMap {
  return Object.fromEntries(STAGES.map((s) => [s.key, "pending"])) as StageMap;
}

// Map backend SSE event names -> (stageKey, status)
export const EVENT_STAGE: Record<string, [string, StageStatus]> = {
  scan_started: ["upload", "success"],
  face_detection_started: ["face", "processing"],
  face_detection_completed: ["face", "success"],
  embedding_generated: ["embedding", "success"],
  search_started: ["search", "processing"],
  search_result_found: ["search", "processing"],
  candidate_analysis_started: ["match", "processing"],
  candidate_match_found: ["match", "success"],
  fingerprint_generated: ["fingerprint", "success"],
  blockchain_transaction_submitted: ["blockchain", "processing"],
  blockchain_confirmed: ["blockchain", "success"],
  blockchain_failed: ["blockchain", "failed"],
  verification_started: ["verify", "processing"],
  verification_completed: ["verify", "success"],
  pipeline_failed: ["verify", "failed"],
};
