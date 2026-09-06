import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ScanFace, Boxes, ShieldCheck, Search, Fingerprint, ArrowRight, Cpu } from "lucide-react";
import { Card } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Disclaimer } from "../components/Disclaimer";
import { getHealth } from "../api/verificationApi";

const PIPELINE = [
  { icon: ScanFace, label: "Face Detection", color: "text-accent-blue" },
  { icon: Search, label: "Web Discovery", color: "text-accent-blue" },
  { icon: ScanFace, label: "Candidate Match", color: "text-accent-purple" },
  { icon: Fingerprint, label: "Evidence Hash", color: "text-accent-purple" },
  { icon: Boxes, label: "Blockchain", color: "text-accent-purple" },
  { icon: ShieldCheck, label: "Verify", color: "text-accent-green" },
];

export function Dashboard() {
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 15000,
  });

  return (
    <div className="space-y-8">
      <Disclaimer />

      {/* Hero */}
      <section className="glass overflow-hidden p-8 shadow-glow">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl">
            <div className="chip mb-3 bg-accent-blue/10 text-accent-blue">
              <Cpu size={12} /> AI · Facial Recognition · Provenance
            </div>
            <h1 className="text-3xl font-bold leading-tight text-white sm:text-4xl">
              Verify Digital Identity &amp; Content Provenance
            </h1>
            <p className="mt-3 text-slate-400">
              Upload a face image, discover publicly available matching content, fingerprint the
              evidence, and verify its integrity on blockchain.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/scan" className="btn-primary">
                <ScanFace size={17} /> Start Face Scan
              </Link>
              <Link to="/records" className="btn-ghost">
                <Boxes size={16} /> View Verification Records
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            {Object.entries({
              API: health?.api,
              Face: health?.face_service,
              Search: health?.search_service,
              Blockchain: health?.blockchain,
            }).map(([k, v]) => (
              <div key={k} className="rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2.5">
                <div className="text-[10px] uppercase tracking-wider text-slate-500">{k}</div>
                <div className="mt-1">
                  <StatusBadge status={(v as string) || "offline"} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Pipeline strip */}
        <div className="mt-8 flex flex-wrap items-center gap-2">
          {PIPELINE.map((p, i) => (
            <div key={p.label} className="flex items-center gap-2">
              <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2">
                <p.icon size={15} className={p.color} />
                <span className="text-xs font-medium text-slate-200">{p.label}</span>
              </div>
              {i < PIPELINE.length - 1 && <ArrowRight size={14} className="text-slate-600" />}
            </div>
          ))}
        </div>
      </section>

      {/* Feature cards */}
      <section className="grid gap-4 md:grid-cols-3">
        <Feature
          icon={<ScanFace className="text-accent-blue" />}
          title="Face Detection & Encoding"
          body="InsightFace detects the target face and generates a 512-d embedding. Raw vectors never leave the server — only a non-invertible ID is shown."
        />
        <Feature
          icon={<Search className="text-accent-purple" />}
          title="Genuine Public Search"
          body="A real, pluggable search provider (Google Programmable Search) finds public candidates; each candidate face is genuinely compared with cosine similarity."
        />
        <Feature
          icon={<ShieldCheck className="text-accent-green" />}
          title="Blockchain Verification"
          body="Evidence is canonicalized, hashed with SHA-256, anchored on an EVM chain, then independently re-hashed and compared to detect tampering."
        />
      </section>
    </div>
  );
}

function Feature({ icon, title, body }: { icon: React.ReactNode; title: string; body: string }) {
  return (
    <Card>
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-white/[0.04]">
        {icon}
      </div>
      <h3 className="text-base font-semibold text-white">{title}</h3>
      <p className="mt-1.5 text-sm text-slate-400">{body}</p>
    </Card>
  );
}
