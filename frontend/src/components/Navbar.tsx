import { NavLink } from "react-router-dom";
import { ScanFace, LayoutDashboard, History, Boxes, Activity, ShieldCheck } from "lucide-react";
import { cn } from "../lib/utils";

const LINKS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/scan", label: "New Scan", icon: ScanFace },
  { to: "/history", label: "Verification History", icon: History },
  { to: "/records", label: "Blockchain Records", icon: Boxes },
  { to: "/status", label: "System Status", icon: Activity },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-base-900/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3">
        <NavLink to="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-accent-blue to-accent-purple shadow-glow">
            <ShieldCheck size={20} className="text-base-900" />
          </div>
          <div className="leading-tight">
            <div className="text-base font-bold tracking-tight text-white">FaceProof</div>
            <div className="text-[10px] uppercase tracking-widest text-slate-400">
              AI · Face ID · Blockchain
            </div>
          </div>
        </NavLink>

        <nav className="hidden items-center gap-1 md:flex">
          {LINKS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition",
                  isActive
                    ? "bg-white/[0.06] text-white"
                    : "text-slate-400 hover:bg-white/[0.03] hover:text-slate-200"
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
