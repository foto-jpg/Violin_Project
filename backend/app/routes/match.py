import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.config import settings
from app.services import audio_jobs, job_store, match_jobs
from app.services.audio_align import align_audio_to_score
from app.utils.musicxml import parse_notes

router = APIRouter()


class MatchRequest(BaseModel):
    omr_job_id: str
    audio_job_id: str
    tempo: Optional[float] = None


@router.post("/match")
async def start_match(req: MatchRequest, background_tasks: BackgroundTasks):
    # Validate up front so the client gets immediate 404/409 feedback, then run
    # the (slow on CPU) DTW alignment in the background and poll for the result.
    omr = job_store.get_job(req.omr_job_id)
    if not omr or not omr.musicxml_path:
        raise HTTPException(404, f"OMR job {req.omr_job_id} not found / not finished")
    if omr.status.value != "done":
        raise HTTPException(409, f"OMR job is {omr.status.value}, not done")

    audio = audio_jobs.get(req.audio_job_id)
    if not audio:
        raise HTTPException(404, f"Audio job {req.audio_job_id} not found")
    if audio.status.value != "done":
        raise HTTPException(409, f"Audio job is {audio.status.value}, not done")

    tempo = req.tempo or audio.tempo or omr.tempo or 120.0
    job_id = uuid.uuid4().hex[:12]
    match_jobs.create(job_id)
    logger.info(
        f"/api/match queued {job_id} omr={req.omr_job_id} "
        f"audio={req.audio_job_id} tempo={tempo}"
    )
    background_tasks.add_task(_run_match, job_id, omr.musicxml_path, req.audio_job_id, tempo)
    return {"job_id": job_id, "status": "queued"}


@router.get("/match/result/{job_id}")
async def match_result(job_id: str):
    job = match_jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Match job not found")
    return job


def _run_match(job_id: str, musicxml_path: str, audio_job_id: str, tempo: float) -> None:
    match_jobs.set_state(job_id, status="running")
    try:
        expected = parse_notes(Path(musicxml_path), tempo_bpm=tempo)
        if not expected:
            raise RuntimeError("OMR result has no notes to align against")

        audio_dir = settings.data_dir / "audio_uploads"
        candidates = list(audio_dir.glob(f"{audio_job_id}.*"))
        if not candidates:
            raise RuntimeError(f"Audio file for job {audio_job_id} missing on disk")

        result = align_audio_to_score(candidates[0], expected, tempo_bpm=tempo)
        match_jobs.set_state(job_id, status="done", **result)
    except Exception as exc:
        logger.exception("match job failed")
        match_jobs.set_state(job_id, status="error", error=str(exc))
