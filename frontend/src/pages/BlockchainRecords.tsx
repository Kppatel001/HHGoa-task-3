import { useQuery } from "@tanstack/react-query";
import { Boxes, ExternalLink } from "lucide-react";
import { Card, KeyValue } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";
import { CopyButton } from "../components/ui/CopyButton";
import { listRecords } from "../api/blockchainApi";
import { shortHash, formatDate } from "../lib/utils";

export function BlockchainRecords() {
  const { data, isLoading } = useQuery({ queryKey: ["records"], queryFn: listRecords, refetchInterval: 20000 });
  const records = data?.records ?? [];

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <Boxes className="text-accent-purple" size={22} />
        <h1 className="text-2xl font-bold text-white">Blockchain Records</h1>
      </div>

      {isLoading && <p className="text-slate-500">Loading…</p>}
      {!isLoading && records.length === 0 && (
        <Card>
          <p className="text-sm text-slate-400">
            No on-chain records yet. Run a scan to register an evidence fingerprint.
          </p>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {records.map((r, i) => (
          <Card key={i} glow="purple">
            <div className="mb-3 flex items-center justify-between">
              <div className="font-mono text-sm text-slate-300">
                FP-{String(r.record_id ?? i + 1).padStart(5, "0")}
              </div>
              <StatusBadge status={r.verification_status || (r.status === "confirmed" ? "confirmed" : r.status)} />
            </div>
            <div className="rounded-lg border border-white/10 bg-base-900/60 p-2.5">
              <div className="text-[10px] uppercase tracking-wider text-slate-500">Content fingerprint</div>
              <div className="mono break-all text-accent-purple">{shortHash(r.fingerprint, 16, 12)}</div>
            </div>
            <div className="mt-2">
              <KeyValue k="Transaction" v={shortHash(r.transaction_hash)} mono />
              <KeyValue k="Network (chainId)" v={r.network_chain_id} />
              <KeyValue k="Block" v={r.block_number ?? "—"} />
              <KeyValue k="Platform" v={r.platform || "—"} />
              <KeyValue k="Created" v={formatDate(r.created_at)} />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <CopyButton value={r.fingerprint} label="Copy hash" />
              {r.transaction_hash && <CopyButton value={r.transaction_hash} label="Copy tx" />}
              {r.transaction_url && (
                <a
                  href={r.transaction_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-xs text-slate-300 hover:bg-white/[0.07]"
                >
                  <ExternalLink size={13} /> View transaction
                </a>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
