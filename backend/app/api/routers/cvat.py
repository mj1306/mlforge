from fastapi import APIRouter

from app.api.deps import CvatServiceDep
from app.domain.schemas.cvat import CvatStatus

router = APIRouter(prefix="/cvat", tags=["cvat"])


@router.get("/status", response_model=CvatStatus)
async def get_status(cvat_service: CvatServiceDep) -> CvatStatus:
    return await cvat_service.status()


@router.post("/start", response_model=CvatStatus)
async def start_cvat(cvat_service: CvatServiceDep) -> CvatStatus:
    return await cvat_service.start()


@router.post("/stop", response_model=CvatStatus)
async def stop_cvat(cvat_service: CvatServiceDep) -> CvatStatus:
    return await cvat_service.stop()
