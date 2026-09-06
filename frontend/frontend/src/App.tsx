import { Routes, Route } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { Dashboard } from "./pages/Dashboard";
import { NewScan } from "./pages/NewScan";
import { History } from "./pages/History";
import { BlockchainRecords } from "./pages/BlockchainRecords";
import { SystemStatusPage } from "./pages/SystemStatusPage";

export default function App() {
  return (
    <div className="app-backdrop min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-7xl px-5 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scan" element={<NewScan />} />
          <Route path="/history" element={<History />} />
          <Route path="/records" element={<BlockchainRecords />} />
          <Route path="/status" element={<SystemStatusPage />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </main>
      <footer className="border-t border-white/10 py-6 text-center text-xs text-slate-600">
        FaceProof · Face Identification &amp; Blockchain Verification · Public content &amp;
        authorized images only · Prototype
      </footer>
    </div>
  );
}
