"""
ProteinScout — FastAPI backend
Run: uvicorn main:app --port 8000 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import scan, setup

app = FastAPI(title="ProteinScout API", version="0.1.0")

# Allow Tauri/Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:1420",
        "tauri://localhost",
        "http://tauri.localhost",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router,  prefix="/scan",  tags=["scan"])
app.include_router(setup.router, prefix="/setup", tags=["setup"])


@app.get("/health")
def health():
    return {"status": "ok"}
