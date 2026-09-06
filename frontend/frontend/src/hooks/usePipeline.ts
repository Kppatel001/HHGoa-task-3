import { useCallback, useState } from "react";
import { parseError } from "../api/client";
import { runPipeline } from "../api/scanApi";
import { initialStages, STAGES, type StageMap } from "../lib/stages";
import type {
  BlockchainResult,
  FaceAnalysis,
  Fingerprint,
  MatchResult,
  PipelineEvent,
  SearchSummary,
  VerificationResult,
} from "../types";

export interface PipelineState {
  scanId: string | null;
  running: boolean;
  stages: StageMap;
  events: PipelineEvent[];
  face: FaceAnalysis | null;
  search: SearchSummary | null;
  match: MatchResult | null;
  fingerprint: Fingerprint | null;
  blockchain: BlockchainResult | null;
  verification: VerificationResult | null;
  error: string | null;
}

const EMPTY: PipelineState = {
  scanId: null,
  running: false,
  stages: initialStages(),
  events: [],
  face: null,
  search: null,
  match: null,
  fingerprint: null,
  blockchain: null,
  verification: null,
  error: null,
};

function allStages(status: StageMap[string]): StageMap {
  return Object.fromEntries(STAGES.map((s) => [s.key, status])) as StageMap;
}

// Derive stage statuses from a completed /api/pipeline response.
function stagesFromResult(d: any): StageMap {
  const s = { ...initialStages() };
  s.upload = "success";
  if (d?.face?.face_detected) { s.face = d.face.warning ? "warning" : "success"; s.embedding = "success"; }
  else if (d?.face) s.face = "failed";
  if (d?.search) s.search = "success";
  // Matching is informational, never fatal: a public match OR "original content"
  // both let the pipeline continue, so the stage is a success in both cases.
  if (d?.match) {
    if (d.match.status === "original_content" || d.match.matched || d.match.status === "potential_match") {
      s.match = "success";
    } else {
      s.match = "warning";
    }
  }
  if (d?.fingerprint) s.fingerprint = "success";
  if (d?.blockchain) s.blockchain = d.blockchain.success ? "success" : "failed";
  if (d?.verification) s.verify = d.verification.status === "VERIFIED" ? "success" : "failed";
  return s;
}

export function usePipeline() {
  const [state, setState] = useState<PipelineState>(EMPTY);
  const patch = (p: Partial<PipelineState>) => setState((s) => ({ ...s, ...p }));

  const reset = useCallback(() => setState(EMPTY), []);

  const apply = (d: any) =>
    patch({
      scanId: d.scan_id ?? null,
      face: d.face ?? null,
      search: d.search ?? null,
      match: d.match ?? null,
      fingerprint: d.fingerprint ?? null,
      blockchain: d.blockchain ?? null,
      verification: d.verification ?? null,
      events: d.events ?? [],
      stages: stagesFromResult(d),
    });

  const run = useCallback(async (file: File, query?: string) => {
    setState({ ...EMPTY, running: true, scanId: "pending", stages: allStages("processing") });
    try {
      const d = await runPipeline(file, query, false);
      if (d && d.notice) {
        // Expected outcome (no face / no match / search unavailable) — 200 + notice.
        const s = { ...initialStages() };
        const code = d.notice.code;
        if (code === "no_face" || code === "invalid_image") {
          s.upload = "success"; s.face = "failed";
        } else if (code === "no_match") {
          s.upload = "success"; s.face = "success"; s.embedding = "success"; s.search = "success"; s.match = "failed";
        } else if (code === "search_unavailable") {
          s.upload = "success"; s.face = "success"; s.embedding = "success"; s.search = "failed";
        }
        patch({
          scanId: d.scan_id ?? null,
          face: d.face ?? null,
          search: d.search ?? null,
          events: d.events ?? [],
          error: d.notice.message,
          stages: s,
        });
      } else {
        apply(d);
      }
    } catch (e) {
      const err = parseError(e);
      const s = { ...initialStages() };
      if (err.code === "no_face" || err.code === "invalid_image") {
        s.upload = "success"; s.face = "failed";
      } else if (err.code === "no_match") {
        s.upload = "success"; s.face = "success"; s.embedding = "success"; s.search = "success"; s.match = "failed";
      } else if (err.code === "search_unavailable") {
        s.upload = "success"; s.face = "success"; s.embedding = "success"; s.search = "failed";
      }
      patch({ error: err.message, stages: s });
    } finally {
      patch({ running: false });
    }
  }, []);

  // Re-run the whole pipeline; with a tamper override it returns TAMPERED.
  const reVerify = useCallback(
    async (overrides?: { caption?: string }) => {
      // We need the original image to re-run; the caller keeps it and passes it in.
      // Here we just flip verification using a fresh tamper run when possible.
      patch({ stages: { ...state.stages, verify: "processing" } });
      try {
        const file = (window as any).__faceproofLastFile as File | undefined;
        if (!file) return;
        const d = await runPipeline(file, state.search?.provider === "google_cse" ? undefined : undefined, !!overrides);
        patch({
          verification: d.verification ?? null,
          blockchain: d.blockchain ?? state.blockchain,
          stages: { ...state.stages, verify: d.verification?.status === "VERIFIED" ? "success" : "failed" },
        });
      } catch (e) {
        patch({ error: parseError(e).message });
      }
    },
    [state.stages, state.search, state.blockchain]
  );

  // remember the last uploaded file for the tamper re-run
  const runAndRemember = useCallback(
    async (file: File, query?: string) => {
      (window as any).__faceproofLastFile = file;
      await run(file, query);
    },
    [run]
  );

  return { state, run: runAndRemember, reset, reVerify };
}
