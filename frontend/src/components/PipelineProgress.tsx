import { motion } from "framer-motion";
import {
  Upload,
  ScanFace,
  Fingerprint,
  Search,
  Link2,
  Boxes,
  ShieldCheck,
  Loader2,
  Check,
  X,
  AlertTriangle,
  Circle,
} from "lucide-react";
import { STAGES, type StageMap } from "../lib/stages";
import type { StageStatus } from "../types";
import { cn } from "../lib/utils";

const ICONS: Record<string, typeof Upload> = {
  upload: Upload,
  face: ScanFace,
  embedding: Fingerprint,
  search: Search,
  match: Link2,
  fingerprint: Fingerprint,
  blockchain: Boxes,
  verify: ShieldCheck,
};

function StatusGlyph({ s }: { s: StageStatus }) {
  if (s === "processing") return <Loader2 size={14} className="animate-spin text-accent-blue" />;
  if (s === "success") return <Check size={14} className="text-accent-green" />;
  if (s === "failed") return <X size={14} className="text-accent-red" />;
  if (s === "warning") return <AlertTriangle size={14} className="text-accent-amber" />;
  return <Circle size={10} className="text-slate-600" />;
}

const RING: Record<StageStatus, string> = {
  pending: "border-white/10 bg-white/[0.02] text-slate-500",
  processing: "border-accent-blue/50 bg-accent-blue/10 text-accent-blue shadow-glow",
  success: "border-accent-green/40 bg-accent-green/10 text-accent-green",
  warning: "border-accent-amber/40 bg-accent-amber/10 text-accent-amber",
  failed: "border-accent-red/40 bg-accent-red/10 text-accent-red",
};

export function PipelineProgress({ stages }: { stages: StageMap }) {
  return (
    <div className="glass p-5">
      <div className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-300">
        Pipeline
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {STAGES.map((stage, i) => {
          const s = stages[stage.key] ?? "pending";
          const Icon = ICONS[stage.key];
          return (
            <motion.div
              key={stage.key}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className={cn(
                "relative flex flex-col gap-2 rounded-xl border p-3 transition-colors",
                RING[s]
              )}
            >
              <div className="flex items-center justify-between">
                <Icon size={18} />
                <StatusGlyph s={s} />
              </div>
              <div className="text-xs font-medium leading-tight text-slate-200">
                {stage.label}
              </div>
              <div className="text-[10px] uppercase tracking-wider opacity-70">{s}</div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
