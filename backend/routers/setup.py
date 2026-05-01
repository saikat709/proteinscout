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
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"status": "downloading", "percent": 0, "message": "Starting…"}

    async def run():
        async def progress(status, percent, message):
            _tasks[task_id] = {"status": status, "percent": percent, "message": message}

        try:
            await pfam.download_and_index(progress)
        except Exception as exc:
            _tasks[task_id] = {"status": "error", "percent": 0, "message": str(exc)}

    asyncio.create_task(run())
    return {"task_id": task_id}


@router.get("/download/{task_id}", response_model=DownloadProgress)
def get_download_progress(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return DownloadProgress(**task)
