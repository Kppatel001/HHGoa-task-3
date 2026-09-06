export interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface FaceAnalysis {
  face_detected: boolean;
  face_count: number;
  confidence: number;
  bbox?: BBox;
  embedding_dimension: number;
  embedding_id: string;
  model: string;
  quality: string;
  processing_time_ms: number;
  image_width: number;
  image_height: number;
  warning?: string | null;
}

export interface Candidate {
  id: number;
  url: string;
  domain: string;
  platform?: string;
  title?: string | null;
  description?: string | null;
  image_url?: string | null;
  author?: string | null;
  published_at?: string | null;
  similarity?: number | null;
  face_compared: boolean;
  error?: string | null;
  raw_metadata?: Record<string, unknown>;
}

export interface SearchSummary {
  provider: string;
  genuine: boolean;
  results_found: number;
  threshold: number;
  potential_match: boolean;
  best_candidate_id?: number | null;
  search_time_ms: number;
  status: string;
  candidates: Candidate[];
}

export interface MatchResult {
  status: "potential_match" | "below_threshold" | "original_content";
  matched: boolean;
  similarity?: number | null;
  source_url?: string | null;
  platform?: string | null;
  note?: string | null;
}

export interface Fingerprint {
  algorithm: string;
  fingerprint: string;
  short: string;
  canonical_json: string;
  media_sha256?: string | null;
}

export interface BlockchainResult {
  success: boolean;
  status: string;
  record_id?: number | null;
  transaction_hash?: string | null;
  transaction_url?: string | null;
  block_number?: number | null;
  network_chain_id: number;
  fingerprint: string;
  timestamp?: number | null;
  gas_used?: number | null;
  error?: string | null;
}

export type VerificationStatus = "VERIFIED" | "TAMPERED" | "NOT_VERIFIED";

export interface VerificationResult {
  verified: boolean;
  status: VerificationStatus;
  current_hash: string;
  blockchain_hash?: string | null;
  match: boolean;
  onchain_verified?: boolean | null;
  integrity_percent: number;
  verified_at: string;
  detail: string;
}

export interface PipelineEvent {
  event: string;
  detail: Record<string, unknown>;
  ts: string;
}

export interface BlockchainRecordRow {
  record_id?: number | null;
  scan_id: string;
  fingerprint: string;
  transaction_hash: string;
  transaction_url?: string | null;
  block_number?: number | null;
  network_chain_id: number;
  platform: string;
  status: string;
  verification_status: string;
  created_at: string;
}

export interface SystemStatus {
  components: Record<string, { status: string; [k: string]: unknown }>;
  config: {
    face_match_threshold: number;
    explorer_url?: string | null;
    demo_mode: boolean;
  };
}

export type StageStatus = "pending" | "processing" | "success" | "warning" | "failed";
