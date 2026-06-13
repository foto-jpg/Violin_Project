from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class AudioJobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    error = "error"


class NoteEvent(BaseModel):
    start_sec: float
    duration_sec: float
    midi: int
    frequency: float
    step: str
    accidental: str = ""
    name: str
    octave: int
    name_with_octave: str
    confidence: float
    beats: Optional[float] = None
    note_value: str = ""


class AudioJobState(BaseModel):
    job_id: str
    status: AudioJobStatus = AudioJobStatus.queued
    tempo: Optional[float] = None
    audio_duration_sec: Optional[float] = None
    sample_rate: Optional[int] = None
    device: Optional[str] = None
    model: Optional[str] = None
    num_frames: Optional[int] = None
    num_voiced_frames: Optional[int] = None
    note_events: Optional[list[NoteEvent]] = None
    process_duration_sec: Optional[float] = None
    error: Optional[str] = None


class AudioProcessResponse(BaseModel):
    job_id: str
    status: AudioJobStatus
