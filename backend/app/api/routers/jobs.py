import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUserDep, JobRegistryDep
from app.domain.jobs.registry import JobNotFoundError
from app.domain.schemas.auth import User
from app.domain.schemas.job import JobRecord

router = APIRouter(prefix="/jobs", tags=["jobs"])

KEEPALIVE_INTERVAL_S = 15


def _get_owned(job_registry, job_id: UUID, user: User) -> JobRecord:
    # 404 (not 403) for someone else's job, so job ids can't be probed.
    record = job_registry.get(job_id)
    if record is None or record.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return record


@router.get("")
async def list_jobs(user: CurrentUserDep, job_registry: JobRegistryDep) -> dict:
    records = job_registry.list_for_owner(user.id)
    return {"jobs": [record.model_dump(mode="json") for record in records]}


@router.get("/{job_id}")
async def get_job(job_id: UUID, user: CurrentUserDep, job_registry: JobRegistryDep) -> dict:
    return _get_owned(job_registry, job_id, user).model_dump(mode="json")


@router.get("/{job_id}/stream")
async def stream_job(
    job_id: UUID, user: CurrentUserDep, job_registry: JobRegistryDep
) -> StreamingResponse:
    _get_owned(job_registry, job_id, user)

    async def event_stream():
        try:
            subscription = job_registry.subscribe(job_id).__aiter__()
            while True:
                try:
                    event = await asyncio.wait_for(
                        subscription.__anext__(), timeout=KEEPALIVE_INTERVAL_S
                    )
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield f"data: {json.dumps(event)}\n\n"
        except StopAsyncIteration:
            return

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: UUID, user: CurrentUserDep, job_registry: JobRegistryDep) -> dict:
    _get_owned(job_registry, job_id, user)
    try:
        accepted = job_registry.request_cancel(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    return {"cancel_requested": accepted}
