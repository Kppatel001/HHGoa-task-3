import { useCallback, useRef, useState } from "react";
import { eventsUrl, parseError } from "../api/client";
import { createScan, analyzeFace } from "../api/scanApi";
import { runSearch, selectMatch } from "../api/searchApi";
import { generateFingerprint, registerBlockchain } from "../api/blockchainApi";
import { verify, type TamperOverrides } from "../api/verificationApi";
import { EVENT_STAGE, initialStages, type StageMap } from "../lib/stages";
import type {
  BlockchainResult,
  FaceAnalysis,
  Fingerprint,
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
  fingerprint: null,
  blockchain: null,
  verification: null,
  error: null,
};

export function usePipeline() {
  const [state, setState] = useState<PipelineState>(EMPTY);
  const esRef = useRef<EventSource | null>(null);

  const patch = (p: Partial<PipelineState>) => setState((s) => ({ ...s, ...p }));
  const setStage = (key: string, status: StageMap[string]) =>
    setState((s) => ({ ...s, stages: { ...s.stages, [key]: status } }));

  const closeStream = () => {
    esRef.current?.close();
    esRef.current = null;
  };

  const openStream = (scanId: string) => {
    closeStream();
    const es = new EventSource(eventsUrl(scanId));
    es.onmessage = (msg) => {
      try {
        const ev = JSON.parse(msg.data) as PipelineEvent;
        setState((s) => {
          const stages = { ...s.stages };
          const mapping = EVENT_STAGE[ev.event];
          if (mapping) {
            const [key, status] = mapping;
            // Don't downgrade a completed stage back to processing.
            if (!(stages[key] === "success" && status === "processing")) {
              stages[key] = status;
            }
          }
          return { ...s, stages, events: [...s.events, ev] };
        });
      } catch {
        /* ignore keepalives */
      }
    };
    es.onerror = () => {
      /* stream ends when scan completes; ignore */
    };
    esRef.current = es;
  };

  const reset = useCallback(() => {
    closeStream();
    setState(EMPTY);
  }, []);

  const reVerify = useCallback(
    async (overrides?: TamperOverrides) => {
      if (!state.scanId) return;
      try {
        setStage("verify", "processing");
        const v = await verify(state.scanId, overrides);
        patch({ verification: v });
        setStage("verify", v.status === "VERIFIED" ? "success" : "failed");
      } catch (e) {
        patch({ error: parseError(e).message });
      }
    },
    [state.scanId]
  );

  const run = useCallback(async (file: File, query?: string) => {
    setState({ ...EMPTY, running: true, stages: initialStages() });
    let scanId = "";
    try {
      // 1) upload
      const created = await createScan(file);
      scanId = created.scan_id;
      patch({ scanId });
      setStage("upload", "success");
      openStream(scanId);

      // 2) face + embedding
      setStage("face", "processing");
      const face = await analyzeFace(scanId);
      patch({ face });
      setStage("face", face.warning ? "warning" : "success");
      setStage("embedding", "success");

      // 3) search + candidate matching
      setStage("search", "processing");
      const search = await runSearch(scanId, query);
      patch({ search });
      setStage("search", "success");

      if (search.best_candidate_id === null || search.best_candidate_id === undefined) {
        setStage("match", "failed");
        throw new Error("No sufficiently similar public result was found.");
      }
      setStage("match", search.potential_match ? "success" : "warning");

      // 4) select best evidence
      await selectMatch(scanId, search.best_candidate_id);

      // 5) fingerprint
      setStage("fingerprint", "processing");
      const fp = await generateFingerprint(scanId);
      patch({ fingerprint: fp });
      setStage("fingerprint", "success");

      // 6) blockchain
      setStage("blockchain", "processing");
      const chain = await registerBlockchain(scanId);
      patch({ blockchain: chain });
      setStage("blockchain", chain.success ? "success" : "failed");
      if (!chain.success) {
        throw new Error(chain.error || "Blockchain registration failed.");
      }

      // 7) verify
      setStage("verify", "processing");
      const v = await verify(scanId);
      patch({ verification: v });
      setStage("verify", v.status === "VERIFIED" ? "success" : "failed");
    } catch (e) {
      patch({ error: parseError(e).message });
    } finally {
      patch({ running: false });
      // Let SSE flush, then close.
      setTimeout(closeStream, 1200);
    }
  }, []);

  return { state, run, reset, reVerify };
}
