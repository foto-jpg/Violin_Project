import threading
from typing import Optional

from app.schemas.audio import AudioJobState, AudioJobStatus

_store: dict[str, AudioJobState] = {}
_lock = threading.Lock()


def create(job_id: str) -> AudioJobState:
    state = AudioJobState(job_id=job_id)
    with _lock:
        _store[job_id] = state
    return state


def get(job_id: str) -> Optional[AudioJobState]:
    return _store.get(job_id)


def update(job_id: str, **kwargs) -> Optional[AudioJobState]:
    with _lock:
        job = _store.get(job_id)
        if job is None:
            return None
        updated = job.model_copy(update=kwargs)
        _store[job_id] = updated
        return updated


def is_any_running() -> bool:
    return any(j.status == AudioJobStatus.running for j in _store.values())
