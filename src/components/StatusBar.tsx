import { motion, AnimatePresence } from "framer-motion";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";

interface Props {
  state: "idle" | "uploading" | "scanning" | "done" | "error";
  progress: number;
  error: string | null;
}

export default function StatusBar({ state, progress, error }: Props) {
  if (state === "idle") return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 8 }}
        className="card px-5 py-4"
      >
        {state === "uploading" && (
          <div className="flex items-center gap-3 text-[var(--text-secondary)]">
            <Loader2 className="w-4 h-4 animate-spin text-brand-400 shrink-0" />
            <span className="text-sm">Uploading file…</span>
          </div>
        )}

        {state === "scanning" && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 text-[var(--text-secondary)]">
                <Loader2 className="w-4 h-4 animate-spin text-brand-400 shrink-0" />
                <span className="text-sm">Running HMMER scan…</span>
              </div>
              <span className="text-sm font-medium text-brand-400">{progress}%</span>
            </div>
            <div className="w-full bg-[var(--bg-secondary)] rounded-full h-1.5">
              <motion.div
                className="h-1.5 rounded-full bg-brand-500"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.4, ease: "easeOut" }}
              />
            </div>
          </div>
        )}

        {state === "done" && (
          <div className="flex items-center gap-3 text-emerald-400">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span className="text-sm font-medium">Scan complete</span>
          </div>
        )}

        {state === "error" && (
          <div className="flex items-center gap-3 text-red-400">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="text-sm">{error || "An error occurred"}</span>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
