import { useState, useCallback, useRef } from "react";
import {
  uploadAndScan,
  getScanStatus,
  ScanResult,
} from "../lib/api";

type ScanState = "idle" | "uploading" | "scanning" | "done" | "error";

export function useScanner() {
  const [state, setState]       = useState<ScanState>("idle");
  const [result, setResult]     = useState<ScanResult | null>(null);
  const [error, setError]       = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const pollRef                 = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);
  };

  const scan = useCallback(async (file: File, evalue: number) => {
    setError(null);
    setResult(null);
    setProgress(0);

    try {
      setState("uploading");
      const { job_id } = await uploadAndScan(file, evalue);

      setState("scanning");

      // Poll every 2 seconds
      pollRef.current = setInterval(async () => {
        try {
          const status = await getScanStatus(job_id);
          const pct = status.sequences_total > 0
            ? Math.round((status.sequences_done / status.sequences_total) * 100)
            : 0;
          setProgress(pct);

          if (status.status === "done") {
            stopPolling();
            setResult(status);
            setState("done");
          } else if (status.status === "error") {
            stopPolling();
            setError(status.error || "Unknown error");
            setState("error");
          }
        } catch {
          stopPolling();
          setError("Lost connection to backend");
          setState("error");
        }
      }, 2000);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || "Upload failed");
      setState("error");
    }
  }, []);

  const reset = useCallback(() => {
    stopPolling();
    setState("idle");
    setResult(null);
    setError(null);
    setProgress(0);
  }, []);

  return { state, result, error, progress, scan, reset };
}
