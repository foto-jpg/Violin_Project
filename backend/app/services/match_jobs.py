import threading
from typing import Optional

# Match results are plain dicts (the alignment output is already JSON-shaped).
_store: dict[str, dict] = {}
_lock = threading.Lock()


def create(job_id: str) -> dict:
    with _lock:
        _store[job_id] = {"job_id": job_id, "status": "queued"}
        return _store[job_id]


def get(job_id: str) -> Optional[dict]:
    return _store.get(job_id)


def set_state(job_id: str, **kwargs) -> None:
    with _lock:
        cur = _store.get(job_id, {"job_id": job_id})
        cur.update(kwargs)
        _store[job_id] = cur


def is_any_running() -> bool:
    return any(j.get("status") == "running" for j in _store.values())
