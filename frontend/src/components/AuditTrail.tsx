import { Clock } from "lucide-react";
import { Card, CardTitle } from "./ui/Card";
import type { PipelineEvent } from "../types";

const LABELS: Record<string, string> = {
  scan_started: "Image uploaded",
  face_detection_started: "Face detection started",
  face_detection_completed: "Face detected",
  embedding_generated: "Embedding generated",
  search_started: "Public search started",
  search_result_found: "Candidate found",
  candidate_analysis_started: "Candidate face analysis started",
  candidate_match_found: "Potential match found",
  fingerprint_generated: "Evidence fingerprint generated",
  blockchain_transaction_submitted: "Blockchain transaction submitted",
  blockchain_confirmed: "Transaction confirmed",
  blockchain_failed: "Blockchain registration failed",
  verification_started: "Verification started",
  verification_completed: "Verification completed",
  pipeline_failed: "Pipeline failed",
};

function fmt(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return ts;
  }
}

export function AuditTrail({ events }: { events: PipelineEvent[] }) {
  if (!events.length) return null;
  return (
    <Card>
      <CardTitle icon={<Clock size={16} className="text-accent-blue" />}>Audit Trail</CardTitle>
      <ol className="relative ml-2 space-y-3 border-l border-white/10 pl-5">
        {events.map((e, i) => (
          <li key={i} className="relative">
            <span className="absolute -left-[23px] top-1 h-2.5 w-2.5 rounded-full bg-accent-blue/70 ring-4 ring-base-900" />
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-slate-200">{LABELS[e.event] || e.event}</span>
              <span className="mono text-[11px] text-slate-500">{fmt(e.ts)}</span>
            </div>
          </li>
        ))}
      </ol>
    </Card>
  );
}
