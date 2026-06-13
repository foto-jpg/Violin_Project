import os
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from loguru import logger

from app.config import settings
from app.schemas.audio import (
    AudioJobState,
    AudioJobStatus,
    AudioProcessResponse,
    NoteEvent,
)
from app.services import audio_jobs

router = APIRouter()

ALLOWED_AUDIO_EXT = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".webm", ".opus"}
MAX_AUDIO_BYTES = 50 * 1024 * 1024
# CREPE on CPU runs ~1.5x audio length; cap clip length on constrained deploys.
MAX_AUDIO_SECONDS = int(os.getenv("MAX_AUDIO_SECONDS", "0"))  # 0 = no limit


def _audio_uploads_dir() -> Path:
    p = settings.data_dir / "audio_uploads"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _run_job(job_id: str, audio_path: Path, tempo: float | None) -> None:
    audio_jobs.update(job_id, status=AudioJobStatus.running)
    start = time.monotonic()
    try:
        from app.services.audio_engine import analyze_audio
        result = analyze_audio(audio_path, tempo_bpm=tempo)
        audio_jobs.update(
            job_id,
            status=AudioJobStatus.done,
            audio_duration_sec=result["duration_sec"],
            sample_rate=result["sample_rate"],
            device=result["device"],
            model=result.get("model"),
            num_frames=result["num_frames"],
            num_voiced_frames=result["num_voiced_frames"],
            note_events=[NoteEvent(**e) for e in result["note_events"]],
            process_duration_sec=round(time.monotonic() - start, 2),
        )
    except Exception as exc:
        logger.exception("audio job failed")
        audio_jobs.update(
            job_id,
            status=AudioJobStatus.error,
            error=str(exc),
            process_duration_sec=round(time.monotonic() - start, 2),
        )


@router.post("/process", response_model=AudioProcessResponse)
async def process(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tempo: float = Form(120.0),
):
    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty upload")
    if len(content) > MAX_AUDIO_BYTES:
        raise HTTPException(400, f"File exceeds 50 MB ({len(content) // 1024 // 1024} MB)")
    ext = Path(file.filename or "").suffix.lower()
    is_audio_mime = (file.content_type or "").startswith("audio/")
    if ext not in ALLOWED_AUDIO_EXT and not is_audio_mime:
        raise HTTPException(400, f"Unsupported audio file: {file.filename} ({file.content_type})")

    if audio_jobs.is_any_running():
        raise HTTPException(429, "Another audio job is running. Try again shortly.")

    job_id = uuid.uuid4().hex[:12]
    audio_path = _audio_uploads_dir() / f"{job_id}{ext or '.wav'}"
    audio_path.write_bytes(content)

    if MAX_AUDIO_SECONDS > 0:
        try:
            import soundfile as sf
            duration = sf.info(str(audio_path)).duration
            if duration > MAX_AUDIO_SECONDS:
                audio_path.unlink(missing_ok=True)
                raise HTTPException(
                    400,
                    f"Audio too long: {duration:.0f}s (max {MAX_AUDIO_SECONDS}s on this deployment)",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Could not read audio duration ({audio_path.name}): {e}")

    audio_jobs.create(job_id)
    audio_jobs.update(job_id, tempo=tempo)
    background_tasks.add_task(_run_job, job_id, audio_path, tempo)
    return AudioProcessResponse(job_id=job_id, status=AudioJobStatus.queued)


@router.get("/result/{job_id}", response_model=AudioJobState)
async def result(job_id: str):
    job = audio_jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job


_AUDIO_MIME = {
    ".wav": "audio/wav", ".mp3": "audio/mpeg", ".m4a": "audio/mp4",
    ".aac": "audio/aac", ".flac": "audio/flac", ".ogg": "audio/ogg",
    ".webm": "audio/webm", ".opus": "audio/opus",
}


@router.get("/file/{job_id}")
async def get_audio_file(job_id: str):
    """Stream the uploaded audio back for in-browser playback (score player)."""
    candidates = list(_audio_uploads_dir().glob(f"{job_id}.*"))
    if not candidates:
        raise HTTPException(404, "Audio file not found")
    path = candidates[0]
    return FileResponse(path, media_type=_AUDIO_MIME.get(path.suffix.lower(), "application/octet-stream"))
