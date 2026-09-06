import { ShieldAlert } from "lucide-react";

export function Disclaimer() {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-accent-amber/25 bg-accent-amber/[0.04] px-4 py-2.5 text-xs text-amber-200/90">
      <ShieldAlert size={15} className="mt-0.5 shrink-0 text-accent-amber" />
      <p>
        Use only images you own or have permission to process. Search results are limited to
        publicly accessible content. A similarity score indicates a <b>potential</b> match, not a
        definitive identity — this tool is for content provenance, not surveillance.
      </p>
    </div>
  );
}
