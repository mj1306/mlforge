import asyncio

import pytest

from app.domain.jobs.registry import InMemoryJobRegistry, JobNotFoundError
from app.domain.schemas.job import JobKind, JobStatus


def test_create_and_get() -> None:
    registry = InMemoryJobRegistry()
    record = registry.create(JobKind.TRAINING)

    fetched = registry.get(record.id)

    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.status == JobStatus.PENDING


def test_get_missing_returns_none() -> None:
    registry = InMemoryJobRegistry()
    assert registry.get(__import__("uuid").uuid4()) is None


def test_update_status_sets_timestamps() -> None:
    registry = InMemoryJobRegistry()
    record = registry.create(JobKind.PROCESSING)

    registry.update_status(record.id, JobStatus.RUNNING)
    running = registry.get(record.id)
    assert running is not None
    assert running.started_at is not None
    assert running.finished_at is None

    registry.update_status(record.id, JobStatus.SUCCEEDED, result={"ok": True})
    done = registry.get(record.id)
    assert done is not None
    assert done.status == JobStatus.SUCCEEDED
    assert done.finished_at is not None
    assert done.result == {"ok": True}


def test_update_status_unknown_job_raises() -> None:
    registry = InMemoryJobRegistry()
    with pytest.raises(JobNotFoundError):
        registry.update_status(__import__("uuid").uuid4(), JobStatus.RUNNING)


def test_update_progress_merges() -> None:
    registry = InMemoryJobRegistry()
    record = registry.create(JobKind.TRAINING)

    registry.update_progress(record.id, {"epoch": 1})
    registry.update_progress(record.id, {"batch": 5})

    fetched = registry.get(record.id)
    assert fetched is not None
    assert fetched.progress == {"epoch": 1, "batch": 5}


def test_request_cancel() -> None:
    registry = InMemoryJobRegistry()
    record = registry.create(JobKind.TRAINING)

    assert registry.is_cancel_requested(record.id) is False
    assert registry.request_cancel(record.id) is True
    assert registry.is_cancel_requested(record.id) is True


def test_request_cancel_on_terminal_job_is_noop() -> None:
    registry = InMemoryJobRegistry()
    record = registry.create(JobKind.TRAINING)
    registry.update_status(record.id, JobStatus.SUCCEEDED)

    assert registry.request_cancel(record.id) is False


@pytest.mark.asyncio
async def test_subscribe_yields_snapshot_then_updates() -> None:
    registry = InMemoryJobRegistry()
    record = registry.create(JobKind.TRAINING)

    events: list[dict] = []

    async def consume() -> None:
        async for event in registry.subscribe(record.id):
            events.append(event)

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.01)  # let the subscriber register and see the initial snapshot

    registry.update_progress(record.id, {"epoch": 1})
    await asyncio.sleep(0.01)

    registry.update_status(record.id, JobStatus.SUCCEEDED)
    await asyncio.wait_for(task, timeout=1)

    assert len(events) == 3
    assert events[0]["status"] == JobStatus.PENDING.value
    assert events[1]["progress"] == {"epoch": 1}
    assert events[2]["status"] == JobStatus.SUCCEEDED.value


@pytest.mark.asyncio
async def test_subscribe_on_already_terminal_job_yields_only_snapshot() -> None:
    registry = InMemoryJobRegistry()
    record = registry.create(JobKind.TRAINING)
    registry.update_status(record.id, JobStatus.FAILED, error="boom")

    events = [event async for event in registry.subscribe(record.id)]

    assert len(events) == 1
    assert events[0]["status"] == JobStatus.FAILED.value
    assert events[0]["error"] == "boom"


@pytest.mark.asyncio
async def test_subscribe_unknown_job_raises() -> None:
    registry = InMemoryJobRegistry()
    with pytest.raises(JobNotFoundError):
        async for _ in registry.subscribe(__import__("uuid").uuid4()):
            pass
