import { Boxes, ExternalLink, XCircle, CheckCircle2 } from "lucide-react";
import { Card, CardTitle, KeyValue } from "./ui/Card";
import { CopyButton } from "./ui/CopyButton";
import { StatusBadge } from "./ui/StatusBadge";
import { shortHash } from "../lib/utils";
import type { BlockchainResult } from "../types";

export function BlockchainCard({ chain }: { chain: BlockchainResult }) {
  if (!chain.success) {
    return (
      <Card>
        <CardTitle icon={<Boxes size={16} className="text-accent-purple" />}>
          Blockchain Registration
        </CardTitle>
        <div className="flex items-start gap-2 rounded-lg border border-accent-red/30 bg-accent-red/5 p-3 text-sm text-accent-red">
          <XCircle size={18} className="mt-0.5 shrink-0" />
          <div>
            <div className="font-semibold">BLOCKCHAIN REGISTRATION FAILED</div>
            <p className="mt-1 text-xs text-accent-red/90">
              {chain.error || "Transaction was not registered on-chain."} The evidence
              fingerprint was still generated, but is not yet anchored on the chain.
            </p>
          </div>
        </div>
      </Card>
    );
  }
  return (
    <Card glow="purple">
      <CardTitle
        icon={<Boxes size={16} className="text-accent-purple" />}
        right={<StatusBadge status="confirmed" />}
      >
        Blockchain Registration
      </CardTitle>
      <div className="mb-3 flex items-center gap-2 rounded-lg border border-accent-green/30 bg-accent-green/5 px-3 py-2 text-sm text-accent-green">
        <CheckCircle2 size={16} /> Blockchain record created & confirmed
      </div>
      <KeyValue k="Record ID" v={chain.record_id ?? "—"} />
      <KeyValue k="Network (chainId)" v={chain.network_chain_id} />
      <KeyValue k="Block" v={chain.block_number ?? "—"} />
      <KeyValue k="Gas used" v={chain.gas_used ?? "—"} />
      <div className="mt-2 rounded-lg border border-white/10 bg-base-900/60 p-3">
        <div className="text-[11px] uppercase tracking-wider text-slate-500">Transaction hash</div>
        <div className="mono mt-1 break-all text-accent-blue">{chain.transaction_hash}</div>
        <div className="mt-2 flex items-center gap-2">
          {chain.transaction_hash && <CopyButton value={chain.transaction_hash} label="Copy tx" />}
          {chain.transaction_url ? (
            <a
              href={chain.transaction_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-xs text-slate-300 hover:bg-white/[0.07]"
            >
              <ExternalLink size={13} /> View transaction
            </a>
          ) : (
            <span className="text-[11px] text-slate-500">
              Local chain — no public explorer (tx: {shortHash(chain.transaction_hash)})
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}
