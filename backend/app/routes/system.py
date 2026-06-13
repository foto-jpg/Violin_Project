import os
import shutil

from fastapi import APIRouter
from app.services.gpu_selector import get_all_gpu_status

router = APIRouter()


@router.get("/health")
async def health():
    audiveris_bin = os.getenv("AUDIVERIS_BIN")
    audiveris_ok = bool(audiveris_bin) or shutil.which("docker") is not None
    oemer_ok = os.getenv("DISABLE_OEMER") != "1" and shutil.which("oemer") is not None
    return {
        "status": "ok",
        "audiveris_available": audiveris_ok,
        "oemer_available": oemer_ok,
    }


@router.get("/gpu-status")
async def gpu_status():
    if os.getenv("DISABLE_GPU") == "1":
        return {"mode": "cpu", "gpus": [], "message": "GPU disabled on this deployment"}
    return get_all_gpu_status()
