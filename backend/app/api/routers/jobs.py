import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import JobRegistryDep
from app.domain.jobs.registry import JobNotFoundError

router = APIRouter(prefix="/jobs", tags=["jobs"])

KEEPALIVE_INTERVAL_S = 15


@router.get("/{job_id}")
async def get_job(job_id: UUID, job_registry: JobRegistryDep) -> dict:
    record = job_registry.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return record.model_dump(mode="json")


@router.get("/{job_id}/stream")
async def stream_job(job_id: UUID, job_registry: JobRegistryDep) -> StreamingResponse:
    if job_registry.get(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")

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
async def cancel_job(job_id: UUID, job_registry: JobRegistryDep) -> dict:
    try:
        accepted = job_registry.request_cancel(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    return {"cancel_requested": accepted}
