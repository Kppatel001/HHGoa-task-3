import { useQuery } from "@tanstack/react-query";
import { Activity } from "lucide-react";
import { Card, KeyValue } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";
import { getSystemStatus } from "../api/verificationApi";

const LABELS: Record<string, string> = {
  face_recognition: "Face Recognition",
  search_service: "Search Service",
  blockchain_rpc: "Blockchain RPC",
  smart_contract: "Smart Contract",
  api: "API",
};

export function SystemStatusPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["status"],
    queryFn: getSystemStatus,
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <Activity className="text-accent-green" size={22} />
        <h1 className="text-2xl font-bold text-white">System Status</h1>
      </div>

      {isLoading && <p className="text-slate-500">Loading…</p>}

      {data && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(data.components).map(([key, comp]) => (
              <Card key={key}>
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-200">{LABELS[key] || key}</span>
                  <StatusBadge status={comp.status} />
                </div>
                <div className="space-y-0.5 text-xs">
                  {Object.entries(comp)
                    .filter(([k]) => k !== "status")
                    .map(([k, v]) => (
                      <KeyValue key={k} k={k} v={v == null ? "—" : String(v)} mono />
                    ))}
                </div>
              </Card>
            ))}
          </div>

          <Card>
            <div className="mb-2 text-sm font-semibold uppercase tracking-wider text-slate-300">
              Configuration
            </div>
            <KeyValue k="Face match threshold" v={data.config.face_match_threshold} />
            <KeyValue k="Demo mode" v={data.config.demo_mode ? "Yes (labeled dataset)" : "No (genuine search)"} />
            <KeyValue k="Block explorer" v={data.config.explorer_url || "— (local chain)"} mono />
          </Card>
        </>
      )}
    </div>
  );
}
