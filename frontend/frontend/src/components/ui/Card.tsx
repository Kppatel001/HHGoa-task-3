import { cn } from "../../lib/utils";
import type { ReactNode } from "react";

export function Card({
  children,
  className,
  glow,
}: {
  children: ReactNode;
  className?: string;
  glow?: "blue" | "purple" | "none";
}) {
  return (
    <div
      className={cn(
        "glass glass-hover p-5",
        glow === "blue" && "shadow-glow",
        glow === "purple" && "shadow-glow-purple",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  icon,
  children,
  right,
}: {
  icon?: ReactNode;
  children: ReactNode;
  right?: ReactNode;
}) {
  return (
    <div className="mb-4 flex items-center justify-between">
      <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-300">
        {icon}
        {children}
      </div>
      {right}
    </div>
  );
}

export function KeyValue({ k, v, mono }: { k: string; v: ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5 text-sm">
      <span className="text-slate-400">{k}</span>
      <span className={cn("text-right text-slate-100", mono && "mono break-all")}>{v}</span>
    </div>
  );
}
