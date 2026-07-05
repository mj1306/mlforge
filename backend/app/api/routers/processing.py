from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import ProcessingServiceDep
from app.domain.schemas.processing import ImageProcessingSettings, ProcessingResult
from app.services.dataset_service import DatasetNotFoundError
from app.services.processing_service import NoImagesFoundError

router = APIRouter(prefix="/datasets/{dataset_id}/processing", tags=["processing"])


@router.get("/random-image")
async def get_random_image(dataset_id: str, processing_service: ProcessingServiceDep) -> FileResponse:
    try:
        image_path = processing_service.get_random_image(dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NoImagesFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(str(image_path))


@router.get("/info")
async def get_processing_info(dataset_id: str, processing_service: ProcessingServiceDep) -> dict:
    try:
        total_images = processing_service.count_images(dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"dataset_id": dataset_id, "total_images": total_images}


@router.post("/apply", response_model=ProcessingResult)
async def apply_processing(
    dataset_id: str, settings: ImageProcessingSettings, processing_service: ProcessingServiceDep
) -> ProcessingResult:
    try:
        return processing_service.apply_processing(dataset_id, settings)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NoImagesFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
