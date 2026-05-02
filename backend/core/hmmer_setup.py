"""
core/hmmer_setup.py — Automatic HMMER binary download and setup
"""

import os
import gzip
import tarfile
import shutil
import asyncio
import subprocess
import platform
from pathlib import Path

# Store HMMER in app data like Pfam
APP_DATA = Path(os.environ.get("APPDATA", Path.home())) / "ProteinScout" / "data"
HMMER_DIR = APP_DATA / "hmmer"
HMMER_BIN_DIR = HMMER_DIR / "bin"

# HMMER 3.4 release - using official FTP or GitHub sources
HMMER_VERSION = "3.4"

# Platform-specific binary URLs - using multiple sources for reliability
def get_hmmer_url():
    """Get the download URL for the current platform."""
    system = platform.system()
    machine = platform.machine()
    
    print(f"[HMMER Download] Detecting platform: system={system}, machine={machine}")
    
    # Try eddylab.org first, with correct path
    if system == "Linux":
        if machine in ["x86_64", "amd64"]:
            # Try different URL formats
            urls = [
                f"http://eddylab.org/software/hmmer/hmmer-{HMMER_VERSION}-linux-intel-x86_64.tar.gz",
                f"http://eddylab.org/software/hmmer/{HMMER_VERSION}/hmmer-{HMMER_VERSION}-linux-intel-x86_64.tar.gz",
                f"https://github.com/EddyRuan/HMMER/releases/download/v{HMMER_VERSION}/hmmer-{HMMER_VERSION}-linux-intel-x86_64.tar.gz",
            ]
            return urls
        elif machine == "aarch64":
            urls = [
                f"http://eddylab.org/software/hmmer/hmmer-{HMMER_VERSION}-linux-arm64.tar.gz",
                f"http://eddylab.org/software/hmmer/{HMMER_VERSION}/hmmer-{HMMER_VERSION}-linux-arm64.tar.gz",
            ]
            return urls
    elif system == "Darwin":  # macOS
        urls = [
            f"http://eddylab.org/software/hmmer/hmmer-{HMMER_VERSION}-macosx-intel.tar.gz",
            f"http://eddylab.org/software/hmmer/{HMMER_VERSION}/hmmer-{HMMER_VERSION}-macosx-intel.tar.gz",
        ]
        return urls
    elif system == "Windows":
        urls = [
            f"http://eddylab.org/software/hmmer/hmmer-{HMMER_VERSION}-msvc-windows-intel-x86_64.zip",
            f"http://eddylab.org/software/hmmer/{HMMER_VERSION}/hmmer-{HMMER_VERSION}-msvc-windows-intel-x86_64.zip",
        ]
        return urls
    
    raise RuntimeError(f"Unsupported platform: {system} {machine}")


def is_hmmer_ready() -> bool:
    """Check if HMMER binaries are already set up."""
    hmmscan = HMMER_BIN_DIR / "hmmscan"
    if os.name == "nt":
        hmmscan = HMMER_BIN_DIR / "hmmscan.exe"
    
    exists = hmmscan.exists()
    print(f"[hmmer_setup] is_hmmer_ready check: {hmmscan} exists={exists}")
    
    if exists:
        # Also verify it's actually executable
        try:
            result = subprocess.run(
                [str(hmmscan), "-h"],
                capture_output=True,
                text=True,
                timeout=5
            )
            ok = result.returncode == 0
            print(f"[hmmer_setup] hmmscan executable test: returncode={result.returncode} (ok={ok})")
            return ok
        except Exception as e:
            print(f"[hmmer_setup] hmmscan executable test failed: {e}")
            return False
    
    return False


def get_hmmscan_path() -> str:
    """Get the path to hmmscan binary."""
    hmmscan = HMMER_BIN_DIR / "hmmscan"
    if os.name == "nt":
        hmmscan = HMMER_BIN_DIR / "hmmscan.exe"
    return str(hmmscan)


async def download_and_setup_hmmer(progress_callback) -> None:
    """Download and extract HMMER binaries."""
    import aiohttp
    
    HMMER_DIR.mkdir(parents=True, exist_ok=True)
    HMMER_BIN_DIR.mkdir(parents=True, exist_ok=True)
    
    hmmer_urls = get_hmmer_url()
    if not isinstance(hmmer_urls, list):
        hmmer_urls = [hmmer_urls]
    
    print(f"HMMER download URLs to try: {hmmer_urls}")
    
    # Download
    await progress_callback("hmmer_downloading", 0, "Downloading HMMER binaries…")
    
    archive_path = None
    downloaded_url = None
    
    # Try each URL until one works
    for hmmer_url in hmmer_urls:
        try:
            print(f"Trying to download from: {hmmer_url}")
            await progress_callback("hmmer_downloading", 5, f"Downloading from {hmmer_url.split('/')[-1]}…")
            
            archive_path = HMMER_DIR / ("hmmer.tar.gz" if hmmer_url.endswith(".tar.gz") else "hmmer.zip")
            
            timeout = aiohttp.ClientTimeout(total=300, connect=30, sock_read=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(hmmer_url) as resp:
                    if resp.status == 404:
                        print(f"URL returned 404, trying next URL…")
                        continue
                    elif resp.status != 200:
                        print(f"URL returned HTTP {resp.status}, trying next URL…")
                        continue
                    
                    print(f"Download started from {hmmer_url}")
                    total = int(resp.headers.get("Content-Length", 0))
                    downloaded = 0
                    
                    with open(archive_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(1024 * 256):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                pct = int(downloaded / total * 30)  # 0–30%
                                mb = downloaded // 1_000_000
                                total_mb = total // 1_000_000
                                await progress_callback("hmmer_downloading", pct, f"Downloading HMMER… {mb}/{total_mb} MB")
                    
                    downloaded_url = hmmer_url
                    print(f"HMMER download complete from {hmmer_url}: {archive_path.stat().st_size} bytes")
                    break
        
        except Exception as e:
            print(f"Download from {hmmer_url} failed: {type(e).__name__}: {str(e)}")
            if archive_path and archive_path.exists():
                archive_path.unlink()
            continue
    
    if not downloaded_url:
        error_msg = f"Failed to download HMMER from any source: {hmmer_urls}"
        print(error_msg)
        raise RuntimeError(error_msg)
    
    # Extract
    await progress_callback("hmmer_extracting", 35, "Extracting HMMER…")
    
    try:
        print(f"Extracting {archive_path}…")
        temp_extract = HMMER_DIR / "temp_extract"
        if temp_extract.exists():
            shutil.rmtree(temp_extract)
        temp_extract.mkdir(parents=True, exist_ok=True)
        
        if archive_path.suffix == ".gz":
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=temp_extract)
                
                # Find the hmmer-X.X directory (should be only actual directory)
                all_items = list(temp_extract.iterdir())
                hmmer_extracted = None
                for item in all_items:
                    if item.is_dir() and item.name.startswith("hmmer"):
                        hmmer_extracted = item
                        break
                
                if not hmmer_extracted and all_items:
                    # Fallback: use first directory
                    hmmer_extracted = [i for i in all_items if i.is_dir()][0] if any(i.is_dir() for i in all_items) else None
                
                if hmmer_extracted:
                    src_bin = hmmer_extracted / "bin"
                    print(f"Found HMMER directory: {hmmer_extracted}")
                    print(f"Looking for bin at: {src_bin}")
                    
                    if src_bin.exists():
                        print(f"Copying binaries from {src_bin} to {HMMER_BIN_DIR}…")
                        for binary in src_bin.iterdir():
                            if binary.is_file():
                                dst = HMMER_BIN_DIR / binary.name
                                print(f"  Copying {binary.name}…")
                                shutil.copy2(binary, dst)
                                # Make executable on Unix
                                if os.name != "nt":
                                    os.chmod(dst, 0o755)
                                    print(f"    Set executable: {dst}")
                    else:
                        print(f"ERROR: bin directory not found at {src_bin}")
                        raise RuntimeError(f"HMMER bin directory not found in archive")
                else:
                    print(f"ERROR: Could not find hmmer-X.X directory in archive")
                    print(f"Contents: {all_items}")
                    raise RuntimeError(f"HMMER directory not found in archive")
        
        elif archive_path.suffix == ".zip":
            import zipfile
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(path=temp_extract)
                
                all_items = list(temp_extract.iterdir())
                hmmer_extracted = None
                for item in all_items:
                    if item.is_dir() and item.name.startswith("hmmer"):
                        hmmer_extracted = item
                        break
                
                if not hmmer_extracted and all_items:
                    hmmer_extracted = [i for i in all_items if i.is_dir()][0] if any(i.is_dir() for i in all_items) else None
                
                if hmmer_extracted:
                    src_bin = hmmer_extracted / "bin"
                    if src_bin.exists():
                        for binary in src_bin.iterdir():
                            if binary.is_file():
                                dst = HMMER_BIN_DIR / binary.name
                                shutil.copy2(binary, dst)
                        print(f"Copied {len(list(HMMER_BIN_DIR.iterdir()))} binaries")
                    else:
                        raise RuntimeError(f"HMMER bin directory not found in archive")
                else:
                    raise RuntimeError(f"HMMER directory not found in archive")
        
        # Clean up temp
        shutil.rmtree(temp_extract, ignore_errors=True)
        archive_path.unlink()  # Clean up archive
        print("HMMER extraction complete")
        print(f"HMMER binaries in {HMMER_BIN_DIR}: {list(HMMER_BIN_DIR.glob('*'))}")
    
    except Exception as e:
        print(f"HMMER extraction error: {type(e).__name__}: {str(e)}")
        raise RuntimeError(f"HMMER extraction failed: {str(e)}")
    
    # Verify
    await progress_callback("hmmer_verifying", 50, "Verifying HMMER installation…")
    
    try:
        hmmscan = get_hmmscan_path()
        if not Path(hmmscan).exists():
            raise RuntimeError(f"hmmscan not found at {hmmscan} after extraction")
        
        # Test it
        result = subprocess.run(
            [hmmscan, "-h"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            raise RuntimeError(f"hmmscan test failed: {result.stderr}")
        
        print(f"HMMER verified at: {hmmscan}")
        print("HMMER setup complete!")
    
    except Exception as e:
        print(f"HMMER verification error: {type(e).__name__}: {str(e)}")
        raise RuntimeError(f"HMMER verification failed: {str(e)}")
