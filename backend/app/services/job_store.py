import threading
from typing import Optional
from app.schemas.omr import JobState, JobStatus

_store: dict[str, JobState] = {}
_lock = threading.Lock()


def create_job(job_id: str, engine: str) -> JobState:
    from app.schemas.omr import Engine
    state = JobState(job_id=job_id, engine=Engine(engine))
    with _lock:
        _store[job_id] = state
    return state


def get_job(job_id: str) -> Optional[JobState]:
    return _store.get(job_id)


def update_job(job_id: str, **kwargs) -> Optional[JobState]:
    with _lock:
        job = _store.get(job_id)
        if job is None:
            return None
        updated = job.model_copy(update=kwargs)
        _store[job_id] = updated
        return updated


def is_any_running() -> bool:
    return any(j.status == JobStatus.running for j in _store.values())
