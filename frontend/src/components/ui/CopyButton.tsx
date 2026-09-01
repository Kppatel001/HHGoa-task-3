import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { copy } from "../../lib/utils";

export function CopyButton({ value, label }: { value: string; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        await copy(value);
        setDone(true);
        setTimeout(() => setDone(false), 1400);
      }}
      className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-xs text-slate-300 hover:bg-white/[0.07]"
      title="Copy"
    >
      {done ? <Check size={13} className="text-accent-green" /> : <Copy size={13} />}
      {label || (done ? "Copied" : "Copy")}
    </button>
  );
}
