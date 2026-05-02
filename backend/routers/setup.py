"""
routers/setup.py — check installation status, trigger Pfam download
"""

import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core import pfam
from core.hmmer import find_hmmscan

router = APIRouter()

# In-memory task store (fine for desktop app)
_tasks: dict[str, dict] = {}


class SetupStatus(BaseModel):
    hmmer_available: bool
    pfam_ready: bool
    pfam_path: str
    pfam_size_gb: float


class DownloadProgress(BaseModel):
    status: str
    percent: int
    message: str


@router.get("/status", response_model=SetupStatus)
def get_status():
    try:
        find_hmmscan()
        hmmer_ok = True
    except FileNotFoundError:
        hmmer_ok = False

    return SetupStatus(
        hmmer_available=hmmer_ok,
        pfam_ready=pfam.is_pfam_ready(),
        pfam_path=pfam.get_pfam_path(),
        pfam_size_gb=pfam.pfam_size_gb(),
    )


@router.post("/download")
async def start_download():
    # If Pfam is already installed and indexed, return an immediate done task
    if pfam.is_pfam_ready():
        task_id = str(uuid.uuid4())
        _tasks[task_id] = {"status": "done", "percent": 100, "message": "Pfam already present"}
        return {"task_id": task_id}

    # If a download/index task is already running, return its task id so the frontend can poll it
    for tid, t in _tasks.items():
        if t.get("status") in ("downloading", "extracting", "indexing"):
            return {"task_id": tid}

    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"status": "downloading", "percent": 0, "message": "Starting…"}

    async def run():
        async def progress(status, percent, message):
            _tasks[task_id] = {"status": status, "percent": percent, "message": message}
            print(f"[Setup Task {task_id}] {status.upper()}: {percent}% - {message}")

        try:
            print(f"[Setup Task {task_id}] Starting download_and_index…")
            await pfam.download_and_index(progress)
            print(f"[Setup Task {task_id}] Download and index completed successfully!")
        except Exception as exc:
            error_msg = str(exc)
            print(f"[Setup Task {task_id}] ERROR: {type(exc).__name__}: {error_msg}")
            # Add helpful hints for common issues
            if "Timeout" in error_msg or "timeout" in error_msg:
                error_msg += " Check if the Pfam FTP server (ftp.ebi.ac.uk) is accessible."
            elif "Connection" in error_msg or "connection" in error_msg:
                error_msg += " Check your internet connection."
            elif "Resuming download" in error_msg or "resume" in error_msg.lower():
                error_msg += " The partial download will be kept — retry to continue."
            
            _tasks[task_id] = {"status": "error", "percent": 0, "message": error_msg}
            print(f"[Setup Task {task_id}] Task marked as error: {error_msg}")

    asyncio.create_task(run())
    return {"task_id": task_id}


@router.get("/download/{task_id}", response_model=DownloadProgress)
def get_download_progress(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return DownloadProgress(**task)
