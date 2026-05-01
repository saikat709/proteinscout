import axios from "axios";

const BASE = "http://localhost:8000";

export const api = axios.create({ baseURL: BASE });

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DomainHit {
  seq_id: string;
  pfam_ac: string;
  pfam_name: string;
  description: string;
  start: number;
  end: number;
  score_dom: number;
  e_val_dom: number;
  e_val_seq: number;
}

export interface SequenceSummary {
  seq_id: string;
  num_domains: number;
  domains: string;
  inferred_type: string;
}

export interface ScanResult {
  job_id: string;
  status: "pending" | "running" | "done" | "error";
  sequences_total: number;
  sequences_done: number;
  hits: DomainHit[];
  summaries: SequenceSummary[];
  error?: string;
}

export interface SetupStatus {
  hmmer_available: boolean;
  pfam_ready: boolean;
  pfam_path: string;
  pfam_size_gb: number;
}

export interface DownloadProgress {
  status: "downloading" | "extracting" | "indexing" | "done" | "error";
  percent: number;
  message: string;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const checkSetup = () =>
  api.get<SetupStatus>("/setup/status").then((r) => r.data);

export const startPfamDownload = () =>
  api.post<{ task_id: string }>("/setup/download").then((r) => r.data);

export const getDownloadProgress = (taskId: string) =>
  api.get<DownloadProgress>(`/setup/download/${taskId}`).then((r) => r.data);

export const uploadAndScan = (file: File, evalue: number = 1e-5) => {
  const form = new FormData();
  form.append("file", file);
  form.append("evalue", String(evalue));
  return api.post<{ job_id: string }>("/scan/submit", form).then((r) => r.data);
};

export const getScanStatus = (jobId: string) =>
  api.get<ScanResult>(`/scan/status/${jobId}`).then((r) => r.data);

export const downloadResults = (jobId: string, format: "tsv" | "csv" = "tsv") =>
  `${BASE}/scan/download/${jobId}?format=${format}`;
