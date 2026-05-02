import { useState } from "react";
import { Toaster } from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";
import { Dna, RotateCcw } from "lucide-react";
import SetupWizard from "./components/SetupWizard";
import UploadZone from "./components/UploadZone";
import ResultsTable from "./components/ResultsTable";
import StatusBar from "./components/StatusBar";
import { useScanner } from "./hooks/useScanner";

type View = "setup" | "main";

export default function App() {
  const [view, setView]   = useState<View>("setup");
  const { state, result, error, progress, done, total, scan, reset } = useScanner();

  return (
    <div className="relative min-h-screen overflow-hidden bg-(--bg-primary)">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-32 -left-24 h-80 w-80 rounded-full bg-brand-500/10 blur-3xl" />
        <div className="absolute top-24 -right-20 h-72 w-72 rounded-full bg-emerald-400/8 blur-3xl" />
        <div className="absolute inset-x-0 bottom-0 h-40 bg-linear-to-t from-black/30 to-transparent" />
      </div>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "var(--bg-card)",
            color: "var(--text-primary)",
            border: "1px solid var(--border)",
            fontSize: "13px",
          },
        }}
      />

      <AnimatePresence mode="wait">
        {view === "setup" ? (
          <motion.div key="setup" exit={{ opacity: 0 }} className="relative z-10">
            <SetupWizard onReady={() => setView("main")} />
          </motion.div>
        ) : (
          <motion.div
            key="main"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="relative z-10 flex flex-col min-h-screen"
          >
            {/* Header */}
            <header className="border-b border-white/8 bg-black/10 backdrop-blur-xl px-8 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-500/15 ring-1 ring-brand-500/20 flex items-center justify-center">
                  <Dna className="w-4 h-4 text-brand-400" />
                </div>
                <span className="font-semibold text-white">ProteinScout</span>
              </div>
              {(state === "done" || state === "error") && (
                <button className="btn-ghost text-sm" onClick={reset}>
                  <RotateCcw className="w-4 h-4" />
                  New scan
                </button>
              )}
            </header>

            {/* Main content */}
            <main className="flex-1 px-8 py-8 max-w-5xl mx-auto w-full space-y-6">
              <AnimatePresence mode="wait">
                {state === "idle" || state === "uploading" || state === "scanning" ? (
                  <motion.div
                    key="upload"
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="space-y-4"
                  >
                    <div>
                      <h2 className="text-xl font-semibold text-white">Scan sequences</h2>
                      <p className="text-(--text-secondary) text-sm mt-1">
                        Upload a protein FASTA file to annotate domains using HMMER + Pfam
                      </p>
                    </div>
                    <UploadZone
                      onScan={scan}
                      isScanning={state === "uploading" || state === "scanning"}
                    />
                    <StatusBar state={state} progress={progress} done={done} total={total} error={error} />
                  </motion.div>
                ) : state === "done" && result ? (
                  <motion.div
                    key="results"
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <div className="mb-6">
                      <h2 className="text-xl font-semibold text-white">Results</h2>
                      <p className="text-(--text-secondary) text-sm mt-1">
                        Domain annotations complete
                      </p>
                    </div>
                    <ResultsTable result={result} />
                  </motion.div>
                ) : (
                  <motion.div key="error" className="space-y-4">
                    <StatusBar state={state} progress={progress} done={done} total={total} error={error} />
                  </motion.div>
                )}
              </AnimatePresence>
            </main>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
