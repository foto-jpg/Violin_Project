from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Engine(str, Enum):
    audiveris = "audiveris"
    oemer = "oemer"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    error = "error"


class ProcessRequest(BaseModel):
    engine: Engine = Engine.oemer


class JobState(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.queued
    engine: Engine
    tempo: Optional[float] = None
    musicxml_path: Optional[str] = None
    duration_sec: Optional[float] = None
    gpu_used: Optional[int] = None
    error: Optional[str] = None


class ProcessResponse(BaseModel):
    job_id: str
    status: JobStatus


class Note(BaseModel):
    measure: Optional[int] = None
    step: str
    accidental: str = ""
    name: str
    octave: int
    name_with_octave: str
    midi: int
    duration: float
    note_value: str = ""
    seconds: Optional[float] = None


class ResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    engine: Engine
    tempo: Optional[float] = None
    musicxml: Optional[str] = None
    notes: Optional[list[Note]] = None
    duration_sec: Optional[float] = None
    gpu_used: Optional[int] = None
    error: Optional[str] = None
