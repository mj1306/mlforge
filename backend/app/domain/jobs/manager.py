import asyncio
import logging
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
from typing import Any

from app.core.config import Settings
from app.domain.jobs.registry import JobRegistry
from app.domain.schemas.job import JobKind, JobRecord, JobStatus

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[dict[str, Any]], None]
CancelCheck = Callable[[], bool]
Work = Callable[[ProgressCallback, CancelCheck], dict[str, Any] | None]


class JobManager:
    """Bridges synchronous worker-thread work functions to the async
    JobRegistry. One executor per job kind so a single GPU training slot
    (max_workers=1) never blocks CPU-bound processing jobs from running
    concurrently."""

    def __init__(self, registry: JobRegistry, settings: Settings) -> None:
        self._registry = registry
        self._training_pool = ThreadPoolExecutor(
            max_workers=settings.training_max_workers, thread_name_prefix="training"
        )
        self._processing_pool = ThreadPoolExecutor(
            max_workers=settings.processing_max_workers, thread_name_prefix="processing"
        )

    def submit_training(self, work: Work, owner_id: str | None = None) -> JobRecord:
        return self._submit(JobKind.TRAINING, self._training_pool, work, owner_id)

    def submit_processing(self, work: Work, owner_id: str | None = None) -> JobRecord:
        return self._submit(JobKind.PROCESSING, self._processing_pool, work, owner_id)

    def submit_cvat_lifecycle(self, work: Work, owner_id: str | None = None) -> JobRecord:
        return self._submit(JobKind.CVAT_LIFECYCLE, self._processing_pool, work, owner_id)

    def _submit(
        self, kind: JobKind, pool: ThreadPoolExecutor, work: Work, owner_id: str | None = None
    ) -> JobRecord:
        record = self._registry.create(kind, owner_id=owner_id)
        loop = asyncio.get_running_loop()

        def progress_callback(event: dict[str, Any]) -> None:
            loop.call_soon_threadsafe(self._registry.update_progress, record.id, event)

        def cancel_check() -> bool:
            return self._registry.is_cancel_requested(record.id)

        def run() -> None:
            # call_soon_threadsafe only forwards positional args, so keyword
            # args (error=/result=) must be bound via partial before crossing
            # the thread boundary -- otherwise the TypeError is swallowed
            # silently inside the executor's un-awaited Future.
            loop.call_soon_threadsafe(
                partial(self._registry.update_status, record.id, JobStatus.RUNNING)
            )
            try:
                result = work(progress_callback, cancel_check)
            except Exception as exc:  # noqa: BLE001 -- surfaced into job record, not swallowed
                logger.exception("Job %s (%s) failed", record.id, kind)
                loop.call_soon_threadsafe(
                    partial(
                        self._registry.update_status,
                        record.id,
                        JobStatus.FAILED,
                        error=str(exc),
                    )
                )
                return
            final_status = (
                JobStatus.CANCELLED if cancel_check() else JobStatus.SUCCEEDED
            )
            loop.call_soon_threadsafe(
                partial(
                    self._registry.update_status, record.id, final_status, result=result
                )
            )

        future = pool.submit(run)
        future.add_done_callback(self._log_unhandled_exception)
        return record

    @staticmethod
    def _log_unhandled_exception(future: Future) -> None:
        # run() catches everything work() raises, but a bug in run() itself
        # (e.g. in the registry calls) would otherwise vanish silently since
        # nothing ever calls future.result().
        exc = future.exception()
        if exc is not None:
            logger.exception("Unhandled exception in job worker thread", exc_info=exc)
