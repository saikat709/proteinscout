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

## Build (production .exe)
```bash
npm run tauri build
# output: src-tauri/target/release/bundle/nsis/ProteinScout_x.x.x_x64-setup.exe
```

Client runs the .exe, installs the app, first launch shows the setup wizard, downloads Pfam automatically — done.

## What's left to add

- Tauri sidecar for bundling Python + conda env into the .exe (needs pyinstaller wrapping)
- App icon (src-tauri/icons/)
- postcss.config.js for Tailwind
