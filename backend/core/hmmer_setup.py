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

# Store HMMER in app data like Pfam. Choose platform-appropriate location.
if platform.system() == "Windows":
    APP_DATA = Path(os.environ.get("APPDATA", Path.home())) / "ProteinScout" / "data"
elif platform.system() == "Darwin":
    APP_DATA = Path.home() / "Library" / "Application Support" / "ProteinScout" / "data"
else:
    APP_DATA = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "ProteinScout" / "data"
HMMER_DIR = APP_DATA / "hmmer"
HMMER_BIN_DIR = HMMER_DIR / "bin"

# HMMER 3.4 release - source distribution
HMMER_VERSION = "3.4"
HMMER_SOURCE_URL = f"http://eddylab.org/software/hmmer/hmmer-{HMMER_VERSION}.tar.gz"

def get_hmmer_url():
    """Get the HMMER source download URL (same for all platforms)."""
    print(f"[HMMER Download] Source URL: {HMMER_SOURCE_URL}")
    return [HMMER_SOURCE_URL]


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
    
    # Check for required build tools
    print("[HMMER Setup] Checking for required build tools…")
    required_tools = ["make", "gcc"]
    for tool in required_tools:
        result = subprocess.run(
            [tool, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            # Show platform-appropriate guidance
            if platform.system() == "Darwin":
                install_msg = (
                    "Required build tool '{tool}' not found. "
                    "On macOS install Xcode command line tools: `xcode-select --install`, or "
                    "use Homebrew: `brew install make gcc`"
                )
            elif platform.system() == "Windows":
                install_msg = (
                    "Required build tool '{tool}' not found. "
                    "On Windows install MSYS2 or appropriate build toolchain (e.g., via https://www.msys2.org/)"
                )
            else:
                install_msg = (
                    "Required build tool '{tool}' not found. "
                    "Please install build-essential: sudo apt install build-essential"
                )
            raise RuntimeError(install_msg.format(tool=tool))
    print("[HMMER Setup] Build tools found: make, gcc")
    
    HMMER_DIR.mkdir(parents=True, exist_ok=True)
    HMMER_BIN_DIR.mkdir(parents=True, exist_ok=True)
    
    hmmer_urls = get_hmmer_url()
    if not isinstance(hmmer_urls, list):
        hmmer_urls = [hmmer_urls]
    
    print(f"HMMER download URLs to try: {hmmer_urls}")
    
    # Download
    await progress_callback("hmmer_downloading", 0, "Downloading HMMER source…")
    
    archive_path = None
    downloaded_url = None
    
    # Try each URL until one works
    for hmmer_url in hmmer_urls:
        try:
            print(f"Trying to download from: {hmmer_url}")
            await progress_callback("hmmer_downloading", 5, f"Downloading HMMER source…")
            
            archive_path = HMMER_DIR / "hmmer.tar.gz"
            
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
                                await progress_callback("hmmer_downloading", pct, f"Downloading HMMER source… {mb}/{total_mb} MB")
                    
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
    await progress_callback("hmmer_extracting", 35, "Extracting HMMER source…")
    
    try:
        print(f"Extracting {archive_path}…")
        temp_extract = HMMER_DIR / "temp_extract"
        if temp_extract.exists():
            shutil.rmtree(temp_extract)
        temp_extract.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=temp_extract)
            
            # Find the hmmer-X.X directory
            all_items = list(temp_extract.iterdir())
            hmmer_source = None
            for item in all_items:
                if item.is_dir() and "hmmer" in item.name.lower():
                    hmmer_source = item
                    break
            
            if not hmmer_source and all_items:
                hmmer_source = [i for i in all_items if i.is_dir()][0] if any(i.is_dir() for i in all_items) else None
            
            if not hmmer_source:
                raise RuntimeError("Could not find hmmer directory in archive")
            
            print(f"Found HMMER source directory: {hmmer_source}")
            
            # Compile HMMER
            await progress_callback("hmmer_compiling", 40, "Compiling HMMER (this may take a minute)…")
            print(f"Configuring HMMER…")
            
            configure_result = subprocess.run(
                ["./configure", "--prefix", str(HMMER_DIR)],
                cwd=str(hmmer_source),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if configure_result.returncode != 0:
                print(f"Configure failed: {configure_result.stderr}")
                raise RuntimeError(f"HMMER configure failed: {configure_result.stderr[:500]}")
            
            print(f"Building HMMER…")
            make_result = subprocess.run(
                ["make", "-j4"],
                cwd=str(hmmer_source),
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if make_result.returncode != 0:
                print(f"Make failed: {make_result.stderr}")
                raise RuntimeError(f"HMMER compilation failed: {make_result.stderr[:500]}")
            
            print(f"Installing HMMER…")
            install_result = subprocess.run(
                ["make", "install"],
                cwd=str(hmmer_source),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if install_result.returncode != 0:
                print(f"Install failed: {install_result.stderr}")
                raise RuntimeError(f"HMMER installation failed: {install_result.stderr[:500]}")
            
            # make install already places the binaries in HMMER_DIR/bin,
            # so there is nothing to copy here. Just ensure they are executable.
            if HMMER_BIN_DIR.exists():
                for binary in HMMER_BIN_DIR.iterdir():
                    if binary.is_file() and binary.name.startswith("hmm"):
                        os.chmod(binary, 0o755)
                        print(f"  Ready {binary.name}")
        
        # Clean up temp
        shutil.rmtree(temp_extract, ignore_errors=True)
        archive_path.unlink()  # Clean up archive
        print("HMMER compilation and installation complete")
        print(f"HMMER binaries in {HMMER_BIN_DIR}: {list(HMMER_BIN_DIR.glob('hmm*'))}")
    
    except subprocess.TimeoutExpired:
        print("HMMER compilation timed out")
        raise RuntimeError("HMMER compilation timed out (exceeded time limit)")
    except Exception as e:
        print(f"HMMER extraction/compilation error: {type(e).__name__}: {str(e)}")
        raise RuntimeError(f"HMMER compilation failed: {str(e)}")
    
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
