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
    const { task_id } = await startPfamDownload();
    setTaskId(task_id);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-8">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-10 w-full max-w-md text-center"
      >
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-2xl bg-brand-500/15 flex items-center justify-center">
            <Database className="w-8 h-8 text-brand-400" />
          </div>
        </div>

        <h1 className="text-2xl font-semibold text-white mb-2">ProteinScout</h1>
        <p className="text-[var(--text-secondary)] text-sm mb-8">
          Protein domain annotation powered by HMMER + Pfam
        </p>

        {/* States */}
        {step === "checking" && (
          <div className="flex flex-col items-center gap-3 text-[var(--text-secondary)]">
            <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
            <span className="text-sm">Checking installation…</span>
          </div>
        )}

        {step === "ready" && (
          <div className="flex flex-col items-center gap-3 text-emerald-400">
            <CheckCircle2 className="w-7 h-7" />
            <span className="text-sm">All set! Launching…</span>
          </div>
        )}

        {step === "needs-download" && (
          <div className="flex flex-col items-center gap-5">
            <div className="text-left w-full bg-[var(--bg-secondary)] rounded-xl p-4 text-sm space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-secondary)]">HMMER binary</span>
                {setup?.hmmer_available
                  ? <span className="badge badge-green">Ready</span>
                  : <span className="badge badge-gray">Missing</span>}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-secondary)]">Pfam-A database</span>
                {setup?.pfam_ready
                  ? <span className="badge badge-green">Ready</span>
                  : <span className="badge badge-gray">~270 MB download</span>}
              </div>
            </div>
            <p className="text-[var(--text-secondary)] text-sm">
              The Pfam database needs to be downloaded once (~3 GB after indexing).
            </p>
            <button className="btn-primary w-full justify-center" onClick={handleDownload}>
              <Download className="w-4 h-4" />
              Download &amp; Setup
            </button>
          </div>
        )}

        {step === "downloading" && progress && (
          <div className="flex flex-col items-center gap-4 w-full">
            <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
            <p className="text-sm text-[var(--text-secondary)]">{progress.message}</p>
            <div className="w-full bg-[var(--bg-secondary)] rounded-full h-2">
              <motion.div
                className="h-2 rounded-full bg-brand-500"
                animate={{ width: `${progress.percent}%` }}
                transition={{ duration: 0.4 }}
              />
            </div>
            <span className="text-xs text-[var(--text-muted)]">{progress.percent}%</span>
          </div>
        )}

        {step === "done" && (
          <div className="flex flex-col items-center gap-3 text-emerald-400">
            <CheckCircle2 className="w-7 h-7" />
            <span className="text-sm">Setup complete! Launching…</span>
          </div>
        )}

        {step === "error" && (
          <div className="flex flex-col items-center gap-3 text-red-400">
            <AlertCircle className="w-7 h-7" />
            <span className="text-sm">Setup failed. Is the backend running?</span>
            <button className="btn-ghost text-xs" onClick={() => setStep("checking")}>
              Retry
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
