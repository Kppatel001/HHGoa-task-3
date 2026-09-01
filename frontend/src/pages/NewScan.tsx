import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ScanFace, RotateCcw, AlertTriangle, Loader2 } from "lucide-react";
import { FaceUploader } from "../components/FaceUploader";
import { PipelineProgress } from "../components/PipelineProgress";
import { FaceResultCard } from "../components/FaceResultCard";
import { SearchResults } from "../components/SearchResults";
import { FingerprintCard } from "../components/FingerprintCard";
import { BlockchainCard } from "../components/BlockchainCard";
import { VerificationPanel } from "../components/VerificationPanel";
import { AuditTrail } from "../components/AuditTrail";
import { Disclaimer } from "../components/Disclaimer";
import { usePipeline } from "../hooks/usePipeline";
import { getSystemStatus } from "../api/verificationApi";

export function NewScan() {
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState("");
  const { state, run, reset, reVerify } = usePipeline();
  const { data: status } = useQuery({ queryKey: ["status"], queryFn: getSystemStatus });

  const demoMode = status?.config?.demo_mode ?? true;
  const started = !!state.scanId;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">New Face Scan</h1>
          <p className="text-sm text-slate-400">
            FACE → SEARCH → MATCH → FINGERPRINT → BLOCKCHAIN → VERIFY
          </p>
        </div>
        {started && (
          <button
            className="btn-ghost"
            onClick={() => {
              reset();
              setFile(null);
            }}
          >
            <RotateCcw size={16} /> New scan
          </button>
        )}
      </div>

      <Disclaimer />

      {!started && (
        <div className="glass p-5">
          <FaceUploader file={file} onFile={setFile} disabled={state.running} />

          <div className="mt-4">
            <label className="text-xs font-medium uppercase tracking-wider text-slate-400">
              Search query {demoMode ? "(optional — demo dataset)" : "(required for genuine search)"}
            </label>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                demoMode
                  ? "Demo mode uses the labeled local dataset"
                  : "Keywords describing the authorized public subject/content"
              }
              className="mt-1.5 w-full rounded-lg border border-white/10 bg-base-900/60 px-3 py-2.5 text-sm text-slate-100 outline-none focus:border-accent-blue/50"
            />
            {!demoMode && (
              <p className="mt-1.5 flex items-center gap-1.5 text-[11px] text-slate-500">
                <AlertTriangle size={12} /> Google Programmable Search cannot search by a raw face;
                provide keywords for the authorized public content to find.
              </p>
            )}
          </div>

          <div className="mt-5 flex gap-3">
            <button
              className="btn-primary"
              disabled={!file || state.running || (!demoMode && !query.trim())}
              onClick={() => file && run(file, query.trim() || undefined)}
            >
              {state.running ? <Loader2 size={16} className="animate-spin" /> : <ScanFace size={16} />}
              Analyze Face
            </button>
          </div>
        </div>
      )}

      {started && (
        <div className="space-y-6">
          <PipelineProgress stages={state.stages} />

          {state.error && (
            <div className="flex items-start gap-2 rounded-lg border border-accent-red/30 bg-accent-red/5 px-4 py-3 text-sm text-accent-red">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" />
              <div>{state.error}</div>
            </div>
          )}

          {state.face && <FaceResultCard face={state.face} />}
          {state.search && <SearchResults search={state.search} />}

          <div className="grid gap-6 lg:grid-cols-2">
            {state.fingerprint && <FingerprintCard fp={state.fingerprint} />}
            {state.blockchain && <BlockchainCard chain={state.blockchain} />}
          </div>

          {state.verification && (
            <VerificationPanel result={state.verification} onReverify={reVerify} busy={state.running} />
          )}

          <AuditTrail events={state.events} />
        </div>
      )}
    </div>
  );
}
