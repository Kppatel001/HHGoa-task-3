import { cn } from "../../lib/utils";
import type { StageStatus } from "../../types";

const MAP: Record<string, { label: string; cls: string; dot: string }> = {
  online: { label: "Online", cls: "bg-accent-green/10 text-accent-green", dot: "bg-accent-green" },
  cold: { label: "Cold", cls: "bg-accent-amber/10 text-accent-amber", dot: "bg-accent-amber" },
  offline: { label: "Offline", cls: "bg-accent-red/10 text-accent-red", dot: "bg-accent-red" },
  pending: { label: "Pending", cls: "bg-white/5 text-slate-400", dot: "bg-slate-500" },
  processing: { label: "Processing", cls: "bg-accent-blue/10 text-accent-blue", dot: "bg-accent-blue animate-pulseGlow" },
  success: { label: "Success", cls: "bg-accent-green/10 text-accent-green", dot: "bg-accent-green" },
  warning: { label: "Warning", cls: "bg-accent-amber/10 text-accent-amber", dot: "bg-accent-amber" },
  failed: { label: "Failed", cls: "bg-accent-red/10 text-accent-red", dot: "bg-accent-red" },
  confirmed: { label: "Confirmed", cls: "bg-accent-purple/10 text-accent-purple", dot: "bg-accent-purple" },
  VERIFIED: { label: "Verified", cls: "bg-accent-green/10 text-accent-green", dot: "bg-accent-green" },
  TAMPERED: { label: "Tampered", cls: "bg-accent-red/10 text-accent-red", dot: "bg-accent-red" },
  NOT_VERIFIED: { label: "Not verified", cls: "bg-white/5 text-slate-400", dot: "bg-slate-500" },
};

export function StatusBadge({
  status,
  label,
}: {
  status: StageStatus | string;
  label?: string;
}) {
  const m = MAP[status] || MAP.pending;
  return (
    <span className={cn("chip", m.cls)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", m.dot)} />
      {label || m.label}
    </span>
  );
}
