# ProteinScout — Desktop App
Tauri + React frontend · Python FastAPI backend · HMMER + Pfam domain scanner

## Tech Stack
- **UI**: Tauri 2 + React 18 + Tailwind CSS + shadcn/ui
- **Backend**: Python 3.11 + FastAPI + BioPython
- **Scanner**: HMMER3 + Pfam-A database
- **Bundler**: Tauri bundler → single `.exe` installer

## Prerequisites (dev machine only)
- Node.js 18+
- Rust (https://rustup.rs)
- Python 3.11+
- Miniconda (optional but recommended)

### macOS-specific requirements
Install Xcode Command Line Tools (required for HMMER compilation):
```bash
xcode-select --install
```

For Apple Silicon (M1/M2/M3) or Intel Macs, Homebrew is recommended:
```bash
# Install Homebrew if needed: https://brew.sh
brew install make gcc
```

For the compiled HMMER binary (optional — app can auto-download and compile):
```bash
brew tap brewsci/bio
brew install hmmer
```

## Project Structure
```
proteinscout/
├── src/                        # React frontend
│   ├── components/
│   │   ├── UploadZone.tsx
│   │   ├── ResultsTable.tsx
│   │   ├── SetupWizard.tsx
│   │   └── StatusBar.tsx
│   ├── hooks/
│   │   └── useScanner.ts
│   ├── lib/
│   │   └── api.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── src-tauri/                  # Tauri (Rust) shell
│   ├── src/
│   │   ├── main.rs
│   │   └── lib.rs
│   └── tauri.conf.json
├── backend/                    # Python FastAPI server
│   ├── main.py
│   ├── routers/
│   │   ├── scan.py
│   │   └── setup.py
│   ├── core/
│   │   ├── hmmer.py
│   │   └── pfam.py
│   └── requirements.txt
├── package.json
├── vite.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

## Dev Setup

### 1. Python backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload
```

### 2. Frontend
```bash
npm install
npm run tauri dev
```

### 3. First run — Pfam setup
On first launch the app shows a setup wizard that:
- Downloads Pfam-A.hmm.gz (~270 MB)
- Runs hmmpress automatically
- Stores DB in %APPDATA%\ProteinScout\data\

## Build (production binaries)

### All platforms (Windows / macOS / Linux)
```bash
npm run tauri:build
```

This builds and bundles:
- **Windows**: `.exe` installer (NSIS) at `src-tauri/target/release/bundle/nsis/`
- **macOS**: `.dmg` app bundle at `src-tauri/target/release/bundle/macos/`
- **Linux**: AppImage at `src-tauri/target/release/bundle/appimage/`

All bundles include the bundled Python FastAPI backend at runtime.

### macOS app signing & notarization (optional, for distribution)
For distribution outside App Store, you may need to sign and notarize the app. This requires:
- Apple Developer account
- Valid signing certificate on your Mac

Tauri will automatically sign if `APPLE_SIGNING_IDENTITY` is set:
```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name"
npm run tauri:build
```

For notarization (post-build):
```bash
xcrun notarytool submit proteinscout_0.1.0_aarch64.dmg \
  --apple-id your-email@example.com \
  --team-id YOUR_TEAM_ID \
  --password your-app-specific-password
```

See [Tauri macOS docs](https://tauri.app/v1/guides/building/macos/) for details.

## What's left to add

- Tauri sidecar for bundling Python + conda env into the .exe (needs pyinstaller wrapping)
- App icon (src-tauri/icons/)
- postcss.config.js for Tailwind
