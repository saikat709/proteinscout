import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Download, Search, ChevronUp, ChevronDown } from "lucide-react";
import { ScanResult, downloadResults } from "../lib/api";

interface Props {
  result: ScanResult;
}

const TYPE_BADGE: Record<string, string> = {
  Kinase:         "badge-purple",
  Protease:       "badge-blue",
  "DNA-binding":  "badge-green",
  Transporter:    "badge-blue",
  Receptor:       "badge-purple",
  Oxidoreductase: "badge-green",
  Structural:     "badge-gray",
  "Unknown / other": "badge-gray",
};

export default function ResultsTable({ result }: Props) {
  const [search, setSearch]       = useState("");
  const [sortCol, setSortCol]     = useState<"seq_id" | "num_domains" | "inferred_type">("seq_id");
  const [sortDir, setSortDir]     = useState<"asc" | "desc">("asc");
  const [tab, setTab]             = useState<"summary" | "domains">("summary");

  const handleSort = (col: typeof sortCol) => {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("asc"); }
  };

  const SortIcon = ({ col }: { col: string }) =>
    sortCol === col
      ? sortDir === "asc" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
      : <ChevronUp className="w-3 h-3 opacity-20" />;

  const filteredSummaries = useMemo(() => {
    const q = search.toLowerCase();
    return result.summaries
      .filter(s =>
        s.seq_id.toLowerCase().includes(q) ||
        s.domains.toLowerCase().includes(q) ||
        s.inferred_type.toLowerCase().includes(q)
      )
      .sort((a, b) => {
        const v = sortDir === "asc" ? 1 : -1;
        if (sortCol === "num_domains") return (a.num_domains - b.num_domains) * v;
        return a[sortCol].localeCompare(b[sortCol]) * v;
      });
  }, [result.summaries, search, sortCol, sortDir]);

  const filteredHits = useMemo(() => {
    const q = search.toLowerCase();
    return result.hits.filter(h =>
      h.seq_id.toLowerCase().includes(q) ||
      h.pfam_ac.toLowerCase().includes(q) ||
      h.pfam_name.toLowerCase().includes(q) ||
      h.description.toLowerCase().includes(q)
    );
  }, [result.hits, search]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Sequences", value: result.sequences_total },
          { label: "Domain hits", value: result.hits.length },
          { label: "Annotated", value: result.summaries.filter(s => s.num_domains > 0).length },
        ].map(stat => (
          <div key={stat.label} className="card px-4 py-3">
            <p className="text-2xl font-semibold text-white">{stat.value}</p>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3">
        {/* Tabs */}
        <div className="flex bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-1 gap-1">
          {(["summary", "domains"] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                tab === t
                  ? "bg-brand-500/20 text-brand-400"
                  : "text-[var(--text-secondary)] hover:text-white"
              }`}
            >
              {t === "summary" ? "By sequence" : "All domains"}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input
            className="input pl-9"
            placeholder="Filter by sequence ID, domain, type…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {/* Export */}
        <a
          href={downloadResults(result.job_id, "tsv")}
          download
          className="btn-ghost"
        >
          <Download className="w-4 h-4" />
          Export TSV
        </a>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          {tab === "summary" ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-[var(--text-muted)]">
                  {[
                    { key: "seq_id", label: "Sequence ID" },
                    { key: "num_domains", label: "Domains" },
                    { key: "inferred_type", label: "Type" },
                  ].map(col => (
                    <th
                      key={col.key}
                      className="px-4 py-3 text-left font-medium cursor-pointer hover:text-white select-none"
                      onClick={() => handleSort(col.key as any)}
                    >
                      <span className="flex items-center gap-1.5">
                        {col.label}
                        <SortIcon col={col.key} />
                      </span>
                    </th>
                  ))}
                  <th className="px-4 py-3 text-left font-medium">Domains found</th>
                </tr>
              </thead>
              <tbody>
                {filteredSummaries.map((s, i) => (
                  <tr
                    key={s.seq_id}
                    className={`border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-card-hover)] transition-colors ${
                      i % 2 === 0 ? "" : "bg-white/[0.01]"
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-brand-400">{s.seq_id}</td>
                    <td className="px-4 py-3 text-white font-medium">{s.num_domains}</td>
                    <td className="px-4 py-3">
                      <span className={`badge ${TYPE_BADGE[s.inferred_type] ?? "badge-gray"}`}>
                        {s.inferred_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[var(--text-secondary)] text-xs max-w-sm truncate">
                      {s.domains || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-[var(--text-muted)]">
                  {["Sequence ID", "Pfam AC", "Name", "Description", "Start", "End", "E-value"].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredHits.map((h, i) => (
                  <tr
                    key={`${h.seq_id}-${h.pfam_ac}-${i}`}
                    className={`border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg-card-hover)] transition-colors ${
                      i % 2 === 0 ? "" : "bg-white/[0.01]"
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-brand-400">{h.seq_id}</td>
                    <td className="px-4 py-3 font-mono text-xs text-purple-400">{h.pfam_ac}</td>
                    <td className="px-4 py-3 font-medium text-white text-xs">{h.pfam_name}</td>
                    <td className="px-4 py-3 text-[var(--text-secondary)] text-xs max-w-xs truncate">{h.description}</td>
                    <td className="px-4 py-3 text-[var(--text-secondary)] text-xs">{h.start}</td>
                    <td className="px-4 py-3 text-[var(--text-secondary)] text-xs">{h.end}</td>
                    <td className="px-4 py-3 font-mono text-xs text-amber-400">{h.e_val_dom.toExponential(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </motion.div>
  );
}
