import { ShieldCheck, ShieldX, ShieldQuestion, ArrowRight, FlaskConical, RotateCcw } from "lucide-react";
import { Card } from "./ui/Card";
import { cn, shortHash } from "../lib/utils";
import type { VerificationResult } from "../types";
import type { TamperOverrides } from "../api/verificationApi";

const STYLE = {
  VERIFIED: {
    icon: ShieldCheck,
    ring: "border-accent-green/50 bg-accent-green/[0.06] shadow-[0_0_50px_-12px_rgba(52,211,153,0.5)]",
    text: "text-accent-green",
    title: "VERIFIED",
  },
  TAMPERED: {
    icon: ShieldX,
    ring: "border-accent-red/50 bg-accent-red/[0.06] shadow-[0_0_50px_-12px_rgba(248,113,113,0.5)]",
    text: "text-accent-red",
    title: "TAMPER DETECTED",
  },
  NOT_VERIFIED: {
    icon: ShieldQuestion,
    ring: "border-white/15 bg-white/[0.03]",
    text: "text-slate-300",
    title: "NOT VERIFIED",
  },
} as const;

export function VerificationPanel({
  result,
  onReverify,
  busy,
}: {
  result: VerificationResult;
  onReverify?: (o?: TamperOverrides) => void;
  busy?: boolean;
}) {
  const s = STYLE[result.status];
  const Icon = s.icon;
  return (
    <Card className={cn("border-2", s.ring)}>
      <div className="flex flex-col items-center gap-2 py-2 text-center">
        <Icon size={44} className={s.text} />
        <div className={cn("text-2xl font-bold tracking-wide", s.text)}>{s.title}</div>
        <p className="max-w-md text-sm text-slate-400">{result.detail}</p>
      </div>

      <div className="mt-4 space-y-2">
        <HashRow label="Current hash" value={result.current_hash} tone="blue" />
        <div className="flex justify-center">
          <ArrowRight size={16} className="rotate-90 text-slate-600" />
        </div>
        <HashRow label="Blockchain hash" value={result.blockchain_hash} tone="purple" />
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
        <Metric label="Comparison" value={result.match ? "MATCH" : "MISMATCH"} good={result.match} />
        <Metric
          label="On-chain check"
          value={result.onchain_verified == null ? "—" : result.onchain_verified ? "PASS" : "FAIL"}
          good={!!result.onchain_verified}
        />
        <Metric label="Integrity" value={`${result.integrity_percent}%`} good={result.integrity_percent === 100} />
      </div>

      {onReverify && (
        <div className="mt-5 flex flex-wrap justify-center gap-3 border-t border-white/10 pt-4">
          <button
            className="btn-ghost"
            disabled={busy}
            onClick={() =>
              onReverify({ caption: "TAMPERED — content modified after registration" })
            }
          >
            <FlaskConical size={15} /> Simulate tampering
          </button>
          <button className="btn-ghost" disabled={busy} onClick={() => onReverify(undefined)}>
            <RotateCcw size={15} /> Re-verify original
          </button>
        </div>
      )}
      <p className="mt-3 text-center text-[11px] text-slate-500">
        Verified at {new Date(result.verified_at).toLocaleString()} · hash {shortHash(result.current_hash)}
      </p>
    </Card>
  );
}

function HashRow({
  label,
  value,
  tone,
}: {
  label: string;
  value?: string | null;
  tone: "blue" | "purple";
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-base-900/60 p-2.5">
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className={cn("mono break-all", tone === "blue" ? "text-accent-blue" : "text-accent-purple")}>
        {value || "—"}
      </div>
    </div>
  );
}

function Metric({ label, value, good }: { label: string; value: string; good: boolean }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] px-2 py-2">
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className={cn("text-sm font-bold", good ? "text-accent-green" : "text-accent-red")}>
        {value}
      </div>
    </div>
  );
}
