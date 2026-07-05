from fastapi import APIRouter, HTTPException, Response

from app.api.deps import CurrentUserDep, TrainingServiceDep
from app.domain.schemas.training import ModelConfig
from app.services.dataset_service import DatasetNotFoundError

router = APIRouter(prefix="/training", tags=["training"])


@router.post("/jobs", status_code=202)
async def start_training(
    config: ModelConfig,
    response: Response,
    user: CurrentUserDep,
    training_service: TrainingServiceDep,
) -> dict:
    try:
        record = training_service.start(user.id, config)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response.headers["Location"] = f"/jobs/{record.id}"
    return {"job_id": str(record.id)}
