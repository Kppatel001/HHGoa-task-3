import { Fingerprint } from "lucide-react";
import { Card, CardTitle, KeyValue } from "./ui/Card";
import { CopyButton } from "./ui/CopyButton";
import type { Fingerprint as FP } from "../types";

export function FingerprintCard({ fp }: { fp: FP }) {
  return (
    <Card glow="purple">
      <CardTitle
        icon={<Fingerprint size={16} className="text-accent-purple" />}
        right={<span className="chip bg-accent-purple/10 text-accent-purple">{fp.algorithm}</span>}
      >
        Content Fingerprint
      </CardTitle>
      <div className="rounded-lg border border-white/10 bg-base-900/60 p-3">
        <div className="mono break-all text-accent-purple">{fp.fingerprint}</div>
        <div className="mt-2 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">SHA-256 of canonical evidence</span>
          <CopyButton value={fp.fingerprint} label="Copy hash" />
        </div>
      </div>
      {fp.media_sha256 && <KeyValue k="Media SHA-256" v={fp.media_sha256} mono />}
      <details className="mt-3 text-xs text-slate-400">
        <summary className="cursor-pointer text-slate-300">Canonical evidence JSON</summary>
        <pre className="mono mt-2 overflow-x-auto rounded-lg bg-base-900/60 p-3 text-[11px] text-slate-300">
          {fp.canonical_json}
        </pre>
      </details>
    </Card>
  );
}
