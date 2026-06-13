import asyncio
import os
import re
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from app.config import settings
from app.schemas.omr import Engine, JobStatus, ProcessResponse, ResultResponse
from app.services import job_store
from app.utils.files import save_upload, validate_upload
from loguru import logger

from app.utils.musicxml import musicxml_to_midi, parse_notes, read_musicxml

router = APIRouter()

# oemer needs a GPU to be practical - disabled on HF Free CPU deployments.
OEMER_DISABLED = os.getenv("DISABLE_OEMER") == "1"


def _run_job(job_id: str, engine: Engine, image_path: Path) -> None:
    job_store.update_job(job_id, status=JobStatus.running)
    start = time.monotonic()
    try:
        result_dir = settings.results_dir / job_id
        result_dir.mkdir(parents=True, exist_ok=True)

        gpu_used = None
        if engine == Engine.oemer:
            from app.services.oemer_engine import run_oemer
            xml_path, gpu_used = run_oemer(image_path, result_dir, settings.job_timeout_sec)
        else:
            from app.services.audiveris import run_audiveris
            xml_path = run_audiveris(image_path, result_dir, settings.job_timeout_sec)

        duration = time.monotonic() - start
        job_store.update_job(
            job_id,
            status=JobStatus.done,
            musicxml_path=str(xml_path),
            duration_sec=round(duration, 2),
            gpu_used=gpu_used,
        )
    except Exception as exc:
        duration = time.monotonic() - start
        job_store.update_job(
            job_id,
            status=JobStatus.error,
            duration_sec=round(duration, 2),
            error=str(exc),
        )


@router.post("/process", response_model=ProcessResponse)
async def process(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    engine: Engine = Form(Engine.audiveris),
    tempo: float = Form(120.0),
):
    if engine == Engine.oemer and OEMER_DISABLED:
        raise HTTPException(
            400,
            "oemer is disabled on this deployment (CPU-only). Use engine='audiveris'.",
        )

    content = await file.read()

    try:
        mime = validate_upload(content, file.filename or "")
    except ValueError as e:
        raise HTTPException(400, str(e))

    if job_store.is_any_running():
        raise HTTPException(429, "Another job is already running. Try again shortly.")

    job_id, image_path = save_upload(content, mime, settings.uploads_dir)
    job_store.create_job(job_id, engine.value)
    job_store.update_job(job_id, tempo=tempo)
    background_tasks.add_task(_run_job, job_id, engine, image_path)

    return ProcessResponse(job_id=job_id, status=JobStatus.queued)


@router.get("/result/{job_id}", response_model=ResultResponse)
async def result(job_id: str):
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    musicxml_content = None
    notes = None
    if job.status == JobStatus.done and job.musicxml_path:
        xml_path = Path(job.musicxml_path)
        if xml_path.exists():
            musicxml_content = read_musicxml(xml_path)
            try:
                notes = parse_notes(xml_path, tempo_bpm=job.tempo)
            except Exception as exc:
                logger.warning(f"parse_notes({xml_path}) failed: {exc}")

    return ResultResponse(
        job_id=job.job_id,
        status=job.status,
        engine=job.engine,
        tempo=job.tempo,
        musicxml=musicxml_content,
        notes=notes,
        duration_sec=job.duration_sec,
        gpu_used=job.gpu_used,
        error=job.error,
    )


@router.get("/download/{job_id}/{format}")
async def download(job_id: str, format: str):
    job = job_store.get_job(job_id)
    if job is None or job.status != JobStatus.done or not job.musicxml_path:
        raise HTTPException(404, "Result not ready")

    xml_path = Path(job.musicxml_path)

    if format == "musicxml":
        return FileResponse(xml_path, media_type="application/xml", filename=f"{job_id}.xml")

    if format == "midi":
        midi_path = xml_path.parent / f"{job_id}.mid"
        if not midi_path.exists():
            try:
                musicxml_to_midi(xml_path, midi_path)
            except Exception as e:
                raise HTTPException(500, f"MIDI conversion failed: {e}")
        return FileResponse(midi_path, media_type="audio/midi", filename=f"{job_id}.mid")

    raise HTTPException(400, f"Unknown format: {format}. Use 'musicxml' or 'midi'.")


@router.get("/musicxml/{job_id}")
async def musicxml(job_id: str):
    """Return decompressed, plain MusicXML text for in-browser rendering (OSMD).

    Audiveris exports .mxl (zipped) - serving the raw file breaks OSMD, so we
    unzip to plain XML here.
    """
    job = job_store.get_job(job_id)
    if job is None or job.status != JobStatus.done or not job.musicxml_path:
        raise HTTPException(404, "Result not ready")
    xml = read_musicxml(Path(job.musicxml_path))
    # Audiveris emits <direction> blocks with a non-standard
    # <symbol xsi:type="formatted-text"> and <sound tempo>; OSMD crashes on them
    # (parentMeasure.TempoExpressions). We don't render directions in the player,
    # so strip them for a clean load.
    xml = re.sub(r"<direction\b[^>]*>.*?</direction>", "", xml, flags=re.DOTALL)
    return Response(content=xml, media_type="application/xml")
