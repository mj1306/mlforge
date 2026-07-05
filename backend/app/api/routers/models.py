from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import CurrentUserDep, TrainingServiceDep
from app.domain.schemas.training import TrainedModel
from app.services.training_service import ModelNotFoundError

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[TrainedModel])
async def list_models(user: CurrentUserDep, training_service: TrainingServiceDep) -> list[TrainedModel]:
    return training_service.list_models(user.id)


@router.get("/{model_name}/weights")
async def download_weights(
    model_name: str, user: CurrentUserDep, training_service: TrainingServiceDep
) -> FileResponse:
    try:
        weights = training_service.resolve_weights(user.id, model_name)
    except ModelNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Model not found: {exc}") from exc
    return FileResponse(str(weights), filename=f"{model_name}.pt")
