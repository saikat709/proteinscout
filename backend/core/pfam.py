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


async def download_and_index(progress_callback) -> None:
    """Download Pfam-A.hmm.gz, extract, and run hmmpress."""
    APP_DATA.mkdir(parents=True, exist_ok=True)

    # Step 1: Download
    await progress_callback("downloading", 0, "Downloading Pfam-A database…")
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(PFAM_URL) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(PFAM_GZ, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 256):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = int(downloaded / total * 60)  # 0–60%
                        await progress_callback("downloading", pct, f"Downloading… {downloaded//1_000_000} MB")

    # Step 2: Extract
    await progress_callback("extracting", 62, "Extracting database…")
    with gzip.open(PFAM_GZ, "rb") as gz_in:
        with open(PFAM_HMM, "wb") as f_out:
            shutil.copyfileobj(gz_in, f_out)
    PFAM_GZ.unlink(missing_ok=True)  # free space

    # Step 3: hmmpress
    await progress_callback("indexing", 80, "Indexing database (this takes 2–3 min)…")
    from core.hmmer import find_hmmscan
    hmmscan_bin = find_hmmscan()
    hmmpress_bin = str(Path(hmmscan_bin).parent / "hmmpress")
    if os.name == "nt":
        hmmpress_bin += ".exe"

    proc = subprocess.run(
        [hmmpress_bin, "-f", str(PFAM_HMM)],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"hmmpress failed: {proc.stderr}")

    await progress_callback("done", 100, "Setup complete!")
