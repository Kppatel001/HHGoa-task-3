import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { History as HistoryIcon } from "lucide-react";
import { Card } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";
import { listRecords } from "../api/blockchainApi";
import { shortHash, formatDate } from "../lib/utils";

const FILTERS = ["all", "verified", "tampered", "not_verified", "pending", "failed"] as const;
type Filter = (typeof FILTERS)[number];

export function History() {
  const [filter, setFilter] = useState<Filter>("all");
  const { data, isLoading } = useQuery({ queryKey: ["records"], queryFn: listRecords });
  const records = data?.records ?? [];

  const filtered = records.filter((r) => {
    if (filter === "all") return true;
    if (filter === "verified") return r.verification_status === "VERIFIED";
    if (filter === "tampered") return r.verification_status === "TAMPERED";
    if (filter === "not_verified") return r.verification_status === "NOT_VERIFIED" || !r.verification_status;
    if (filter === "pending") return r.status === "pending";
    if (filter === "failed") return r.status === "failed";
    return true;
  });

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <HistoryIcon className="text-accent-blue" size={22} />
        <h1 className="text-2xl font-bold text-white">Verification History</h1>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`chip capitalize ${
              filter === f ? "bg-accent-blue/15 text-accent-blue" : "bg-white/5 text-slate-400"
            }`}
          >
            {f.replace("_", " ")}
          </button>
        ))}
      </div>

      <Card className="overflow-x-auto p-0">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Platform</th>
              <th className="px-4 py-3">Fingerprint</th>
              <th className="px-4 py-3">Record</th>
              <th className="px-4 py-3">Blockchain</th>
              <th className="px-4 py-3">Verification</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  Loading…
                </td>
              </tr>
            )}
            {!isLoading && filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No records yet — run a scan from the New Scan page.
                </td>
              </tr>
            )}
            {filtered.map((r, i) => (
              <tr key={i} className="hover:bg-white/[0.02]">
                <td className="px-4 py-3 text-slate-300">{formatDate(r.created_at)}</td>
                <td className="px-4 py-3 text-slate-300">{r.platform || "—"}</td>
                <td className="px-4 py-3 mono text-accent-purple">{shortHash(r.fingerprint)}</td>
                <td className="px-4 py-3 text-slate-300">{r.record_id ?? "—"}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={r.status === "confirmed" ? "confirmed" : r.status} />
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={r.verification_status || "NOT_VERIFIED"} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
