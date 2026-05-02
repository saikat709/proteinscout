"""
core/pfam.py — Pfam database paths, download, and indexing
"""

import os
import gzip
import shutil
import asyncio
import subprocess
from pathlib import Path

# Store Pfam in %APPDATA%\ProteinScout\data\ on Windows
APP_DATA = Path(os.environ.get("APPDATA", Path.home())) / "ProteinScout" / "data"
PFAM_GZ  = APP_DATA / "Pfam-A.hmm.gz"
PFAM_HMM = APP_DATA / "Pfam-A.hmm"
PFAM_URL = "https://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz"

# Index files created by hmmpress
INDEX_EXTS = [".h3f", ".h3i", ".h3m", ".h3p"]


def get_pfam_path() -> str:
    return str(PFAM_HMM)


def is_pfam_ready() -> bool:
    if not PFAM_HMM.exists():
        return False
    return all((PFAM_HMM.parent / (PFAM_HMM.name + ext)).exists() for ext in INDEX_EXTS)


def pfam_size_gb() -> float:
    if PFAM_HMM.exists():
        return round(PFAM_HMM.stat().st_size / 1e9, 2)
    return 0.0


async def _download_with_progress(resp, filepath, file_mode, progress_callback):
    """Helper to download response content with progress updates."""
    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    
    with open(filepath, file_mode) as f:
        async for chunk in resp.content.iter_chunked(1024 * 256):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = int(downloaded / total * 60)  # 0–60%
                mb = downloaded // 1_000_000
                total_mb = total // 1_000_000
                await progress_callback("downloading", pct, f"Downloading… {mb}/{total_mb} MB")


async def download_and_index(progress_callback) -> None:
    """Download Pfam-A.hmm.gz, extract, and run hmmpress."""
    APP_DATA.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Pfam to {PFAM_HMM}…")

    # Step 1: Download
    await progress_callback("downloading", 0, "Downloading Pfam-A database…")
    import aiohttp
    
    # Check for partial download and resume
    resume_from = 0
    if PFAM_GZ.exists():
        resume_from = PFAM_GZ.stat().st_size
        print(f"Resuming download from {resume_from} bytes…")
    
    headers = {}
    if resume_from > 0:
        headers["Range"] = f"bytes={resume_from}-"
        file_mode = "ab"  # append mode for resume
    else:
        file_mode = "wb"  # overwrite mode for new download
    
    try:
        # Set a timeout of 5 minutes for the download session
        timeout = aiohttp.ClientTimeout(total=300, connect=30, sock_read=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(PFAM_URL, headers=headers) as resp:
                if resp.status == 416:  # Range Not Satisfiable
                    print("Server doesn't support resume, restarting from beginning…")
                    PFAM_GZ.unlink(missing_ok=True)
                    resume_from = 0
                    file_mode = "wb"
                    headers = {}
                    async with session.get(PFAM_URL) as resp2:
                        await _download_with_progress(resp2, PFAM_GZ, file_mode, progress_callback)
                else:
                    await _download_with_progress(resp, PFAM_GZ, file_mode, progress_callback)
        print(f"Download complete. File size: {PFAM_GZ.stat().st_size} bytes")
    except asyncio.TimeoutError:
        raise RuntimeError(f"Download timeout after 5 minutes. Partial file saved to {PFAM_GZ} — you can retry to resume.")
    except Exception as e:
        print(f"Download error: {type(e).__name__}: {str(e)}")
        raise RuntimeError(f"Download failed: {str(e)}. Partial file saved to {PFAM_GZ} — you can retry to resume.")

    # Step 2: Extract
    await progress_callback("extracting", 62, "Extracting database…")
    if not PFAM_GZ.exists():
        raise RuntimeError(f"Downloaded file not found at {PFAM_GZ}")
    
    try:
        print(f"Extracting {PFAM_GZ} to {PFAM_HMM}…")
        with gzip.open(PFAM_GZ, "rb") as gz_in:
            with open(PFAM_HMM, "wb") as f_out:
                shutil.copyfileobj(gz_in, f_out)
        uncompressed_size = PFAM_HMM.stat().st_size
        print(f"Extraction complete. Uncompressed size: {uncompressed_size} bytes")
        PFAM_GZ.unlink(missing_ok=True)  # free space
    except Exception as e:
        print(f"Extraction error: {type(e).__name__}: {str(e)}")
        raise RuntimeError(f"Extraction failed: {str(e)}")

    # Step 3: hmmpress
    await progress_callback("indexing", 80, "Indexing database (this takes 2–3 min)…")
    from core.hmmer import find_hmmscan
    
    try:
        print("Looking for hmmscan binary…")
        hmmscan_bin = find_hmmscan()
        print(f"Found hmmscan at: {hmmscan_bin}")
    except FileNotFoundError as e:
        print(f"Could not find hmmscan: {str(e)}")
        raise RuntimeError(f"hmmscan not found. Install with: conda install -c bioconda hmmer")
    
    hmmpress_bin = str(Path(hmmscan_bin).parent / "hmmpress")
    if os.name == "nt":
        hmmpress_bin += ".exe"
    
    print(f"hmmpress binary path: {hmmpress_bin}")
    if not Path(hmmpress_bin).exists():
        raise RuntimeError(f"hmmpress not found at {hmmpress_bin}")

    print(f"Running hmmpress: {hmmpress_bin} -f {PFAM_HMM}…")
    try:
        proc = subprocess.run(
            [hmmpress_bin, "-f", str(PFAM_HMM)],
            capture_output=True, text=True, timeout=600  # 10 min timeout
        )
        print(f"hmmpress exit code: {proc.returncode}")
        if proc.stdout:
            print(f"hmmpress stdout: {proc.stdout[:500]}")
        if proc.returncode != 0:
            print(f"hmmpress stderr: {proc.stderr}")
            raise RuntimeError(f"hmmpress failed: {proc.stderr}")
    except subprocess.TimeoutExpired:
        print("hmmpress indexing timed out")
        raise RuntimeError("hmmpress indexing timed out (exceeded 10 minutes)")
    except Exception as e:
        print(f"Indexing error: {type(e).__name__}: {str(e)}")
        raise RuntimeError(f"Indexing failed: {str(e)}")

    print("Setup complete!")
    await progress_callback("done", 100, "Setup complete!")
