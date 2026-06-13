import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import settings
from app.routes import audio, match, omr, system

settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.results_dir.mkdir(parents=True, exist_ok=True)
settings.logs_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="OMR Demo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    # On constrained CPU deployments, cap torch threads (HF Free has 2 vCPU).
    if os.getenv("DISABLE_GPU") == "1":
        try:
            import torch
            torch.set_num_threads(int(os.getenv("OMP_NUM_THREADS", "2")))
            logger.info(f"CPU mode: torch threads = {torch.get_num_threads()}")
        except ImportError:
            pass
    cache_dir = Path(os.getenv("HF_HOME", "/tmp/hf_cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)


# API routers FIRST - registered before the SPA catch-all so /api/* always wins.
app.include_router(omr.router, prefix="/api/omr")
app.include_router(audio.router, prefix="/api/audio")
app.include_router(match.router, prefix="/api")
app.include_router(system.router, prefix="/api")


# Static frontend (Next.js export) - mounted only when STATIC_DIR is set (HF).
# No effect locally, where the frontend runs as its own Next.js server.
_static_dir = os.getenv("STATIC_DIR", "")
STATIC_DIR = Path(_static_dir) if _static_dir else None
if STATIC_DIR and STATIC_DIR.exists():
    logger.info(f"Mounting static frontend from {STATIC_DIR}")
    _next_assets = STATIC_DIR / "_next"
    if _next_assets.exists():
        app.mount("/_next", StaticFiles(directory=_next_assets), name="next-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        folder_index = STATIC_DIR / full_path / "index.html"
        if folder_index.is_file():               # Next.js trailingSlash routes
            return FileResponse(folder_index)
        root_index = STATIC_DIR / "index.html"
        if root_index.is_file():
            return FileResponse(root_index)
        return {"error": "not found", "path": full_path}
else:
    logger.info("No STATIC_DIR - API-only mode (frontend served separately)")
