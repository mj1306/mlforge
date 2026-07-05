from fastapi import APIRouter

from app.api.deps import CurrentUserDep, CvatServiceDep
from app.domain.schemas.cvat import CvatStatus

# CVAT itself is one shared stack per machine (it has its own user accounts),
# but starting/stopping it still requires being logged in to MLForge.
router = APIRouter(prefix="/cvat", tags=["cvat"])


@router.get("/status", response_model=CvatStatus)
async def get_status(user: CurrentUserDep, cvat_service: CvatServiceDep) -> CvatStatus:
    return await cvat_service.status()


@router.post("/start", response_model=CvatStatus)
async def start_cvat(user: CurrentUserDep, cvat_service: CvatServiceDep) -> CvatStatus:
    return await cvat_service.start(owner_id=user.id)


@router.post("/stop", response_model=CvatStatus)
async def stop_cvat(user: CurrentUserDep, cvat_service: CvatServiceDep) -> CvatStatus:
    return await cvat_service.stop()
