from __future__ import annotations

import asyncio
import secrets
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from core.models import IdempotencyMode, TransferDirection, TransferProgressEvent, TransferReport


@dataclass
class JobState:
    job_id: str
    direction: TransferDirection
    idempotency: IdempotencyMode
    status: str = "queued"  # queued | running | done | error
    error: str | None = None
    report: TransferReport | None = None
    report_path: str | None = None
    last_events: deque = field(default_factory=lambda: deque(maxlen=200))
    matched: int = 0
    unmatched: int = 0
    skipped: int = 0
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    finished: asyncio.Event = field(default_factory=asyncio.Event)


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobState] = {}
        self._lock = threading.Lock()

    def create(self, direction: TransferDirection, idempotency: IdempotencyMode) -> JobState:
        with self._lock:
            job_id = secrets.token_urlsafe(16)
            job = JobState(job_id=job_id, direction=direction, idempotency=idempotency)
            self._jobs[job_id] = job
            return job

    def get(self, job_id: str) -> JobState | None:
        return self._jobs.get(job_id)

    def push_event(self, job: JobState, event: TransferProgressEvent) -> None:
        payload = event.model_dump()
        job.last_events.append(payload)
        if event.type == "track_matched":
            job.matched += 1
        elif event.type == "track_unmatched":
            job.unmatched += 1
        elif event.type == "track_skipped":
            job.skipped += 1
        try:
            job.queue.put_nowait(payload)
        except asyncio.QueueFull:  # pragma: no cover - queue is unbounded
            pass

    def snapshot(self, job: JobState) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "status": job.status,
            "direction": job.direction,
            "idempotency": job.idempotency,
            "last_events": list(job.last_events),
            "matched": job.matched,
            "unmatched": job.unmatched,
            "skipped": job.skipped,
            "report_path": job.report_path,
            "error": job.error,
        }


_manager = JobManager()


def get_jobs() -> JobManager:
    return _manager
