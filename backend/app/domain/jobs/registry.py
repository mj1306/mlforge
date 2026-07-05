import asyncio
import threading
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID

from app.domain.schemas.job import JobKind, JobRecord, JobStatus


class JobRegistry(Protocol):
    def create(self, kind: JobKind) -> JobRecord: ...

    def get(self, job_id: UUID) -> JobRecord | None: ...

    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        *,
        error: str | None = None,
        result: dict[str, Any] | None = None,
    ) -> None: ...

    def update_progress(self, job_id: UUID, progress: dict[str, Any]) -> None: ...

    def subscribe(self, job_id: UUID) -> AsyncIterator[dict[str, Any]]: ...

    def request_cancel(self, job_id: UUID) -> bool: ...

    def is_cancel_requested(self, job_id: UUID) -> bool: ...


class JobNotFoundError(KeyError):
    pass


class InMemoryJobRegistry:
    """Single-process job store. Not persisted across restarts -- acceptable
    for a single-node, local-first app; swap the Protocol implementation if
    that ever needs to change."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, JobRecord] = {}
        self._lock = threading.Lock()
        self._subscribers: dict[UUID, list[asyncio.Queue[dict[str, Any]]]] = {}

    def create(self, kind: JobKind) -> JobRecord:
        record = JobRecord(kind=kind)
        with self._lock:
            self._jobs[record.id] = record
            self._subscribers[record.id] = []
        return record

    def get(self, job_id: UUID) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _require(self, job_id: UUID) -> JobRecord:
        record = self._jobs.get(job_id)
        if record is None:
            raise JobNotFoundError(str(job_id))
        return record

    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        *,
        error: str | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            record = self._require(job_id)
            record.status = status
            if status == JobStatus.RUNNING and record.started_at is None:
                record.started_at = datetime.now(timezone.utc)
            if status.is_terminal:
                record.finished_at = datetime.now(timezone.utc)
            if error is not None:
                record.error = error
            if result is not None:
                record.result = result
        self._publish(job_id, record)

    def update_progress(self, job_id: UUID, progress: dict[str, Any]) -> None:
        with self._lock:
            record = self._require(job_id)
            record.progress = {**record.progress, **progress}
        self._publish(job_id, record)

    def _publish(self, job_id: UUID, record: JobRecord) -> None:
        snapshot = record.model_dump(mode="json")
        with self._lock:
            queues = list(self._subscribers.get(job_id, []))
        for queue in queues:
            queue.put_nowait(snapshot)

    async def subscribe(self, job_id: UUID) -> AsyncIterator[dict[str, Any]]:
        with self._lock:
            record = self._require(job_id)
            queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
            self._subscribers.setdefault(job_id, []).append(queue)
            snapshot = record.model_dump(mode="json")

        try:
            yield snapshot
            if record.status.is_terminal:
                return
            while True:
                event = await queue.get()
                yield event
                if event["status"] in (
                    JobStatus.SUCCEEDED,
                    JobStatus.FAILED,
                    JobStatus.CANCELLED,
                ):
                    break
        finally:
            with self._lock:
                subscribers = self._subscribers.get(job_id, [])
                if queue in subscribers:
                    subscribers.remove(queue)

    def request_cancel(self, job_id: UUID) -> bool:
        with self._lock:
            record = self._require(job_id)
            if record.status.is_terminal:
                return False
            record.cancel_requested = True
        return True

    def is_cancel_requested(self, job_id: UUID) -> bool:
        with self._lock:
            record = self._jobs.get(job_id)
            return bool(record and record.cancel_requested)
