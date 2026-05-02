"""
routers/setup.py — check installation status, trigger Pfam + HMMER setup
"""

import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core import pfam
from core import hmmer_setup
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
    print("[Setup Status] Checking environment…")
    
    # Check HMMER
    hmmer_ok = False
    try:
        hmmscan = find_hmmscan()
        print(f"[Setup Status] Found hmmscan at: {hmmscan}")
        hmmer_ok = True
    except FileNotFoundError as e:
        print(f"[Setup Status] hmmscan not found via find_hmmscan(): {e}")
        # Check if it's ready to be downloaded/setup
        hmmer_ok = hmmer_setup.is_hmmer_ready()
        print(f"[Setup Status] HMMER ready (via is_hmmer_ready): {hmmer_ok}")

    # Check Pfam
    pfam_ok = pfam.is_pfam_ready()
    print(f"[Setup Status] Pfam ready: {pfam_ok}")
    
    pfam_path = pfam.get_pfam_path()
    pfam_size = pfam.pfam_size_gb()
    
    print(f"[Setup Status] Final status: hmmer={hmmer_ok}, pfam={pfam_ok}, pfam_path={pfam_path}, pfam_size={pfam_size}")

    return SetupStatus(
        hmmer_available=hmmer_ok,
        pfam_ready=pfam_ok,
        pfam_path=pfam_path,
        pfam_size_gb=pfam_size,
    )


@router.post("/download")
async def start_download():
    # If both are ready, return immediate done task
    if pfam.is_pfam_ready() and hmmer_setup.is_hmmer_ready():
        task_id = str(uuid.uuid4())
        _tasks[task_id] = {"status": "done", "percent": 100, "message": "All dependencies ready"}
        return {"task_id": task_id}

    # If a download/index task is already running, return its task id so the frontend can poll it
    for tid, t in _tasks.items():
        if t.get("status") in ("hmmer_downloading", "hmmer_extracting", "hmmer_verifying", "downloading", "extracting", "indexing"):
            return {"task_id": tid}

    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"status": "hmmer_downloading", "percent": 0, "message": "Starting setup…"}

    async def run():
        async def progress(status, percent, message):
            _tasks[task_id] = {"status": status, "percent": percent, "message": message}
            print(f"[Setup Task {task_id}] {status.upper()}: {percent}% - {message}")

        try:
            print(f"[Setup Task {task_id}] Starting full setup…")
            
            # First: Download and setup HMMER if needed
            if not hmmer_setup.is_hmmer_ready():
                print(f"[Setup Task {task_id}] HMMER not ready, downloading…")
                try:
                    await hmmer_setup.download_and_setup_hmmer(progress)
                    print(f"[Setup Task {task_id}] HMMER setup complete")
                except Exception as e:
                    print(f"[Setup Task {task_id}] HMMER setup failed: {type(e).__name__}: {str(e)}")
                    raise
            else:
                print(f"[Setup Task {task_id}] HMMER already ready")
            
            # Then: Download and setup Pfam if needed
            if not pfam.is_pfam_ready():
                print(f"[Setup Task {task_id}] Pfam not ready, downloading…")
                try:
                    await pfam.download_and_index(progress)
                    print(f"[Setup Task {task_id}] Pfam setup complete")
                except Exception as e:
                    print(f"[Setup Task {task_id}] Pfam setup failed: {type(e).__name__}: {str(e)}")
                    raise
            else:
                print(f"[Setup Task {task_id}] Pfam already ready")
            
            print(f"[Setup Task {task_id}] Full setup completed successfully!")
            await progress("done", 100, "All dependencies ready!")
        
        except Exception as exc:
            error_msg = str(exc)
            print(f"[Setup Task {task_id}] ERROR: {type(exc).__name__}: {error_msg}")
            # Add helpful hints for common issues
            if "Timeout" in error_msg or "timeout" in error_msg:
                error_msg += " Check your internet connection."
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
