import { Search, ExternalLink, ShieldAlert, CheckCircle2 } from "lucide-react";
import { Card, CardTitle } from "./ui/Card";
import { StatusBadge } from "./ui/StatusBadge";
import { pct, ms } from "../lib/utils";
import { cn } from "../lib/utils";
import type { SearchSummary } from "../types";

export function SearchResults({ search }: { search: SearchSummary }) {
  const best = search.best_candidate_id;
  return (
    <Card>
      <CardTitle
        icon={<Search size={16} className="text-accent-blue" />}
        right={
          <div className="flex items-center gap-2">
            <StatusBadge
              status={search.genuine ? "online" : "warning"}
              label={search.genuine ? `Genuine · ${search.provider}` : "DEMO DATASET"}
            />
          </div>
        }
      >
        Web Search & Candidate Matching
      </CardTitle>

      <div className="mb-4 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
        <Stat label="Results" value={String(search.results_found)} />
        <Stat label="Threshold" value={pct(search.threshold)} />
        <Stat label="Search time" value={ms(search.search_time_ms)} />
        <Stat
          label="Outcome"
          value={search.potential_match ? "Potential match" : "No match ≥ threshold"}
        />
      </div>

      <div className="space-y-3">
        {search.candidates.length === 0 && (
          <p className="text-sm text-slate-400">No candidates returned.</p>
        )}
        {search.candidates.map((c) => {
          const isBest = c.id === best;
          const above = c.similarity != null && c.similarity >= search.threshold;
          return (
            <div
              key={c.id}
              className={cn(
                "flex gap-3 rounded-xl border p-3 transition",
                isBest
                  ? "border-accent-green/40 bg-accent-green/[0.04]"
                  : "border-white/10 bg-white/[0.02]"
              )}
            >
              <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg bg-base-700">
                {c.image_url && !c.image_url.startsWith("file://") ? (
                  <img src={c.image_url} alt="" className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full w-full items-center justify-center text-[10px] text-slate-500">
                    DEMO
                  </div>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  {isBest && <CheckCircle2 size={15} className="text-accent-green" />}
                  <span className="truncate text-sm font-medium text-slate-100">
                    {c.title || c.platform || c.domain}
                  </span>
                </div>
                <p className="mt-0.5 line-clamp-1 text-xs text-slate-400">
                  {c.description || "Publicly accessible content"}
                </p>
                <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                  <span className="chip bg-white/5">{c.platform || c.domain}</span>
                  {c.published_at && <span>{c.published_at}</span>}
                  {c.face_compared ? (
                    <span className={cn("chip", above ? "bg-accent-green/10 text-accent-green" : "bg-white/5 text-slate-300")}>
                      Face similarity {pct(c.similarity)}
                    </span>
                  ) : (
                    <span className="chip bg-white/5 text-slate-500">
                      <ShieldAlert size={11} /> {c.error || "no face compared"}
                    </span>
                  )}
                </div>
              </div>
              {c.url && (
                <a
                  href={c.url}
                  target="_blank"
                  rel="noreferrer"
                  className="self-center rounded-md border border-white/10 p-2 text-slate-300 hover:bg-white/10"
                  title="Open original"
                >
                  <ExternalLink size={15} />
                </a>
              )}
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-[11px] text-slate-500">
        A similarity score indicates a <span className="text-slate-300">potential</span> face
        match and content-match confidence — never a definitive identification.
      </p>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2">
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="text-sm font-semibold text-slate-100">{value}</div>
    </div>
  );
}
