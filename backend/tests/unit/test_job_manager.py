import asyncio

import pytest

from app.core.config import Settings
from app.domain.jobs.manager import JobManager
from app.domain.jobs.registry import InMemoryJobRegistry
from app.domain.schemas.job import JobStatus


@pytest.fixture
def manager() -> JobManager:
    registry = InMemoryJobRegistry()
    settings = Settings(training_max_workers=1, processing_max_workers=1)
    return JobManager(registry, settings)


async def _wait_for_terminal(registry: InMemoryJobRegistry, job_id, timeout: float = 2.0):
    async for _ in registry.subscribe(job_id):
        pass
    return registry.get(job_id)


@pytest.mark.asyncio
async def test_submit_training_success(manager: JobManager) -> None:
    def work(progress_callback, cancel_check):
        progress_callback({"epoch": 1})
        progress_callback({"epoch": 2})
        return {"final_metric": 0.9}

    record = manager.submit_training(work)
    registry = manager._registry  # test-only introspection
    final = await asyncio.wait_for(_wait_for_terminal(registry, record.id), timeout=2)

    assert final is not None
    assert final.status == JobStatus.SUCCEEDED
    assert final.result == {"final_metric": 0.9}
    assert final.progress == {"epoch": 2}


@pytest.mark.asyncio
async def test_submit_training_failure_captures_error(manager: JobManager) -> None:
    def work(progress_callback, cancel_check):
        raise ValueError("dataset path missing")

    record = manager.submit_training(work)
    registry = manager._registry
    final = await asyncio.wait_for(_wait_for_terminal(registry, record.id), timeout=2)

    assert final is not None
    assert final.status == JobStatus.FAILED
    assert final.error == "dataset path missing"


@pytest.mark.asyncio
async def test_submit_processing_respects_cancel(manager: JobManager) -> None:
    def work(progress_callback, cancel_check):
        while not cancel_check():
            pass
        return None

    record = manager.submit_processing(work)
    registry = manager._registry
    registry.request_cancel(record.id)
    final = await asyncio.wait_for(_wait_for_terminal(registry, record.id), timeout=2)

    assert final is not None
    assert final.status == JobStatus.CANCELLED
