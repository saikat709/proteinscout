import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, X, SlidersHorizontal } from "lucide-react";
import clsx from "clsx";

interface Props {
  onScan: (file: File, evalue: number) => void;
  isScanning: boolean;
}

export default function UploadZone({ onScan, isScanning }: Props) {
  const [file, setFile]           = useState<File | null>(null);
  const [evalue, setEvalue]       = useState("1e-5");
  const [showOptions, setShowOptions] = useState(false);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/plain": [".faa", ".fasta", ".fa"] },
    maxFiles: 1,
    disabled: isScanning,
  });

  const handleScan = () => {
    if (file) onScan(file, parseFloat(evalue));
  };

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={clsx(
          "relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200",
          isDragActive
            ? "border-brand-500 bg-[var(--accent-dim)]"
            : file
            ? "border-[var(--border-light)] bg-[var(--bg-card)]"
            : "border-[var(--border)] bg-[var(--bg-card)] hover:border-[var(--border-light)] hover:bg-[var(--bg-card-hover)]",
          isScanning && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />

        <AnimatePresence mode="wait">
          {file ? (
            <motion.div
              key="file"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex flex-col items-center gap-3"
            >
              <div className="w-12 h-12 rounded-xl bg-brand-500/15 flex items-center justify-center">
                <FileText className="w-6 h-6 text-brand-400" />
              </div>
              <div>
                <p className="font-medium text-white text-sm">{file.name}</p>
                <p className="text-[var(--text-muted)] text-xs mt-0.5">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
              {!isScanning && (
                <button
                  onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  className="absolute top-3 right-3 p-1.5 rounded-lg hover:bg-white/5 text-[var(--text-muted)] hover:text-white transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-3"
            >
              <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
                <Upload className="w-6 h-6 text-[var(--text-muted)]" />
              </div>
              <div>
                <p className="text-white text-sm font-medium">
                  {isDragActive ? "Drop your file here" : "Drop your .faa file here"}
                </p>
                <p className="text-[var(--text-muted)] text-xs mt-1">
                  or click to browse — supports .faa, .fasta, .fa
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Options toggle */}
      <div className="flex items-center justify-between">
        <button
          className="btn-ghost text-xs"
          onClick={() => setShowOptions(!showOptions)}
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          Advanced options
        </button>

        <button
          className="btn-primary"
          disabled={!file || isScanning}
          onClick={handleScan}
        >
          {isScanning ? "Scanning…" : "Run Scan"}
        </button>
      </div>

      {/* Advanced options */}
      <AnimatePresence>
        {showOptions && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="card p-4 space-y-3">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <label className="text-sm font-medium text-[var(--text-primary)]">
                    E-value threshold
                  </label>
                  <p className="text-xs text-[var(--text-muted)] mt-0.5">
                    Lower = stricter (default: 1e-5)
                  </p>
                </div>
                <input
                  className="input w-32 text-right font-mono"
                  value={evalue}
                  onChange={(e) => setEvalue(e.target.value)}
                  placeholder="1e-5"
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
