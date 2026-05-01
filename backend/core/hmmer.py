"""
core/hmmer.py — runs hmmscan and parses domtblout
"""

import subprocess
import tempfile
import os
import sys
from pathlib import Path
from Bio.SearchIO import parse as sio_parse


def find_hmmscan() -> str:
    """Find hmmscan binary — checks PATH and common conda locations."""
    import shutil

    # 1. Try PATH
    path = shutil.which("hmmscan")
    if path:
        return path

    # 2. Try conda env bin (Windows: Scripts/)
    conda_prefix = os.environ.get("CONDA_PREFIX", "")
    for suffix in [r"Scripts\hmmscan.exe", r"bin\hmmscan"]:
        candidate = Path(conda_prefix) / suffix
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        "hmmscan not found. Install with: conda install -c bioconda hmmer"
    )


def run_hmmscan(
    faa_path: str,
    pfam_hmm: str,
    e_value: float = 1e-5,
    cpu: int = 4,
) -> list[dict]:
    """Run hmmscan against Pfam and return parsed domain hits."""

    hmmscan_bin = find_hmmscan()

    with tempfile.NamedTemporaryFile(suffix=".domtblout", delete=False) as tmp:
        domtblout = tmp.name

    try:
        cmd = [
            hmmscan_bin,
            "--domtblout", domtblout,
            "--cut_ga",
            "--noali",
            "--cpu", str(cpu),
            pfam_hmm,
            faa_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            # Fallback: use -E threshold
            cmd = [
                hmmscan_bin,
                "--domtblout", domtblout,
                "-E", str(e_value),
                "--noali",
                "--cpu", str(cpu),
                pfam_hmm,
                faa_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"hmmscan failed: {result.stderr}")

        return _parse_domtblout(domtblout)

    finally:
        if os.path.exists(domtblout):
            os.unlink(domtblout)


def _parse_domtblout(domtblout: str) -> list[dict]:
    rows = []
    with open(domtblout) as fh:
        for qresult in sio_parse(fh, "hmmer3-domtab"):
            seq_id = qresult.id
            for hit in qresult.hits:
                pfam_ac   = hit.accession.split(".")[0]
                pfam_name = hit.id
                pfam_desc = hit.description
                e_val_seq = hit.evalue
                score_seq = hit.bitscore

                for hsp in hit.hsps:
                    rows.append({
                        "seq_id":      seq_id,
                        "pfam_ac":     pfam_ac,
                        "pfam_name":   pfam_name,
                        "description": pfam_desc,
                        "start":       hsp.query_start + 1,
                        "end":         hsp.query_end,
                        "score_dom":   round(hsp.bitscore, 2),
                        "e_val_dom":   hsp.evalue,
                        "e_val_seq":   e_val_seq,
                        "accuracy":    round(hsp.acc_avg, 3),
                    })
    return rows
