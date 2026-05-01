import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Database, Download, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { checkSetup, startPfamDownload, getDownloadProgress, SetupStatus, DownloadProgress } from "../lib/api";

interface Props {
  onReady: () => void;
}

export default function SetupWizard({ onReady }: Props) {
  const [setup, setSetup]         = useState<SetupStatus | null>(null);
  const [step, setStep]           = useState<"checking" | "ready" | "needs-download" | "downloading" | "done" | "error">("checking");
  const [progress, setProgress]   = useState<DownloadProgress | null>(null);
  const [taskId, setTaskId]        = useState<string | null>(null);
  const setupReady = Boolean(setup?.pfam_ready && setup?.hmmer_available);

  // Check setup on mount
  useEffect(() => {
    checkSetup()
      .then((s) => {
        setSetup(s);
        if (s.pfam_ready && s.hmmer_available) {
          setStep("ready");
          setTimeout(onReady, 800);
        } else {
          setStep("needs-download");
        }
      })
      .catch(() => setStep("error"));
  }, []);

  // Poll download progress
  useEffect(() => {
    if (!taskId) return;
    const interval = setInterval(async () => {
      const p = await getDownloadProgress(taskId);
      setProgress(p);
      if (p.status === "done") {
        clearInterval(interval);
        setStep("done");
        setTimeout(onReady, 1200);
      } else if (p.status === "error") {
        clearInterval(interval);
        setStep("error");
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [taskId]);

  const handleDownload = async () => {
    setStep("downloading");
    setProgress({ status: "downloading", percent: 0, message: "Starting download…" });
    const { task_id } = await startPfamDownload();
    setTaskId(task_id);
  };

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center px-6 py-10 sm:px-8">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-[-5rem] top-12 h-72 w-72 rounded-full bg-brand-500/12 blur-3xl" />
        <div className="absolute right-[-6rem] top-1/3 h-80 w-80 rounded-full bg-emerald-400/10 blur-3xl" />
      </div>
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-2xl overflow-hidden rounded-[1.5rem] border border-white/10 bg-[rgba(17,17,24,0.72)] p-6 shadow-2xl shadow-black/30 backdrop-blur-xl sm:p-8"
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,197,94,0.12),transparent_50%)]" />

        <div className="relative grid gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="text-center lg:text-left">
            <div className="mb-6 flex justify-center lg:justify-start">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-500/15 ring-1 ring-brand-500/20">
                <Database className="w-8 h-8 text-brand-400" />
              </div>
            </div>

            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.24em] text-[var(--text-secondary)]">
              Setup required
            </div>

            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              ProteinScout
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--text-secondary)] sm:text-base">
              Protein domain annotation powered by HMMER + Pfam. Finish the one-time setup, then scan FASTA files in a cleaner, faster workspace.
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {[
                { label: "Local scan", value: "HMMER" },
                { label: "Domain DB", value: "Pfam-A" },
                { label: "Workflow", value: "Fast setup" },
              ].map((item) => (
                <div key={item.label} className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-left">
                  <div className="text-[11px] uppercase tracking-[0.2em] text-[var(--text-muted)]">{item.label}</div>
                  <div className="mt-1 text-sm font-medium text-white">{item.value}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[1.25rem] border border-white/10 bg-black/20 p-5 sm:p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-xs uppercase tracking-[0.24em] text-[var(--text-muted)]">Status</div>
                <div className="mt-1 text-lg font-medium text-white">
                  {step === "checking" ? "Checking environment" : step === "downloading" ? "Downloading Pfam" : setupReady ? "Ready to launch" : "Setup required"}
                </div>
              </div>
              <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-[var(--text-secondary)]">
                {setup?.hmmer_available && setup?.pfam_ready ? "Configured" : "Not ready"}
              </div>
            </div>

            <div className="mt-5 space-y-3 rounded-2xl border border-white/8 bg-[var(--bg-secondary)]/80 p-4 text-sm">
              <div className="flex items-center justify-between gap-4">
                <span className="text-[var(--text-secondary)]">HMMER binary</span>
                {setup?.hmmer_available
                  ? <span className="badge badge-green">Ready</span>
                  : <span className="badge badge-gray">Missing</span>}
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-[var(--text-secondary)]">Pfam-A database</span>
                {setup?.pfam_ready
                  ? <span className="badge badge-green">Ready</span>
                  : <span className="badge badge-gray">~270 MB download</span>}
              </div>
            </div>

            {step === "checking" && (
              <div className="mt-5 flex flex-col items-center gap-3 text-[var(--text-secondary)]">
                <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
                <span className="text-sm">Checking installation…</span>
              </div>
            )}

            {step === "ready" && (
              <div className="mt-5 flex flex-col items-center gap-3 text-emerald-400">
                <CheckCircle2 className="w-7 h-7" />
                <span className="text-sm">All set! Launching…</span>
              </div>
            )}

            {step === "needs-download" && (
              <div className="mt-5 flex flex-col gap-4">
                <p className="text-sm leading-6 text-[var(--text-secondary)]">
                  The Pfam database needs to be downloaded once. After that, scans run locally.
                </p>
                <button className="btn-primary w-full justify-center" onClick={handleDownload}>
                  <Download className="w-4 h-4" />
                  Download &amp; Setup
                </button>
              </div>
            )}

            {step === "downloading" && progress && (
              <div className="mt-5 flex flex-col gap-4 w-full">
                <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
                <div className="space-y-1">
                  <p className="text-sm text-[var(--text-secondary)]">{progress.message}</p>
                  <p className="text-xs uppercase tracking-[0.2em] text-[var(--text-muted)]">
                    Download progress
                  </p>
                </div>
                <div className="w-full overflow-hidden rounded-full bg-[var(--bg-secondary)] h-2">
                  <motion.div
                    className="h-2 rounded-full bg-brand-500"
                    animate={{ width: `${progress.percent}%` }}
                    transition={{ duration: 0.4 }}
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-[var(--text-muted)]">
                  <span>{progress.status}</span>
                  <span>{progress.percent}%</span>
                </div>
              </div>
            )}

            {step === "done" && (
              <div className="mt-5 flex flex-col items-center gap-3 text-emerald-400">
                <CheckCircle2 className="w-7 h-7" />
                <span className="text-sm">Setup complete! Launching…</span>
              </div>
            )}

            {step === "error" && (
              <div className="mt-5 flex flex-col items-center gap-3 text-red-400">
                <AlertCircle className="w-7 h-7" />
                <span className="text-sm">Setup failed. Is the backend running?</span>
                <button className="btn-ghost text-xs" onClick={() => setStep("checking")}>
                  Retry
                </button>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
