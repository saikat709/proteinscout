"""
routers/scan.py — upload .faa, run hmmscan, return results
"""

import uuid
import asyncio
import tempfile
import os
import csv
import io
from pathlib import Path
from collections import defaultdict

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from Bio import SeqIO

from core.hmmer import run_hmmscan
from core.pfam import get_pfam_path, is_pfam_ready

router = APIRouter()

# In-memory job store
_jobs: dict[str, dict] = {}

DOMAIN_SIGNATURES = {
    "Kinase":         ["PF00069", "PF07714"],
    "Protease":       ["PF00089", "PF00082"],
    "DNA-binding":    ["PF00105", "PF00096"],
    "Transporter":    ["PF00083", "PF01061"],
    "Receptor":       ["PF00002", "PF00001"],
    "Oxidoreductase": ["PF00067", "PF00106"],
    "Structural":     ["PF00041", "PF07679"],
}


def infer_type(pfam_acs: list[str]) -> str:
    ac_set = set(pfam_acs)
    for cat, markers in DOMAIN_SIGNATURES.items():
        if ac_set & set(markers):
            return cat
    return "Unknown / other"


def summarise(hits: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for h in hits:
        grouped[h["seq_id"]].append(h)
    summaries = []
    for seq_id, seq_hits in grouped.items():
        acs   = [h["pfam_ac"]   for h in seq_hits]
        names = [h["pfam_name"] for h in seq_hits]
        summaries.append({
            "seq_id":        seq_id,
            "num_domains":   len(seq_hits),
            "domains":       "; ".join(f"{n} ({a})" for n, a in zip(names, acs)),
            "inferred_type": infer_type(acs),
        })
    return summaries


class ScanResult(BaseModel):
    job_id: str
    status: str
    sequences_total: int
    sequences_done: int
    hits: list[dict]
    summaries: list[dict]
    error: str | None = None


@router.post("/submit")
async def submit_scan(
    file: UploadFile = File(...),
    evalue: float    = Form(1e-5),
):
    if not is_pfam_ready():
        raise HTTPException(400, "Pfam database not ready. Complete setup first.")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "pending",
        "sequences_total": 0,
        "sequences_done": 0,
        "hits": [],
        "summaries": [],
        "error": None,
    }

    # Save uploaded file to temp
    contents = await file.read()
    tmp = tempfile.NamedTemporaryFile(suffix=".faa", delete=False)
    tmp.write(contents)
    tmp.close()

    # Count sequences
    seqs = list(SeqIO.parse(tmp.name, "fasta"))
    _jobs[job_id]["sequences_total"] = len(seqs)

    async def run():
        try:
            _jobs[job_id]["status"] = "running"
            hits = await asyncio.to_thread(
                run_hmmscan,
                tmp.name,
                get_pfam_path(),
                evalue,
            )
            _jobs[job_id]["hits"]             = hits
            _jobs[job_id]["summaries"]        = summarise(hits)
            _jobs[job_id]["sequences_done"]   = len(seqs)
            _jobs[job_id]["status"]           = "done"
        except Exception as exc:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"]  = str(exc)
        finally:
            os.unlink(tmp.name)

    asyncio.create_task(run())
    return {"job_id": job_id}


@router.get("/status/{job_id}", response_model=ScanResult)
def get_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return ScanResult(job_id=job_id, **job)


@router.get("/download/{job_id}")
def download_results(job_id: str, format: str = "tsv"):
    job = _jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(404, "Results not ready")

    delimiter = "\t" if format == "tsv" else ","
    output    = io.StringIO()
    hits      = job["hits"]

    if hits:
        writer = csv.DictWriter(output, fieldnames=list(hits[0].keys()), delimiter=delimiter)
        writer.writeheader()
        writer.writerows(hits)

    output.seek(0)
    media_type = "text/tab-separated-values" if format == "tsv" else "text/csv"
    filename   = f"results_{job_id[:8]}.{format}"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
