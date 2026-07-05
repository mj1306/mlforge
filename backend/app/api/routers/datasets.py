from fastapi import APIRouter, HTTPException, UploadFile

from app.api.deps import CurrentUserDep, DatasetServiceDep, SettingsDep
from app.domain.schemas.dataset import DatasetInfo, DatasetUploadResult, UpdateClassesRequest
from app.services.dataset_service import DatasetNotFoundError, DatasetUploadError

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetUploadResult, status_code=201)
async def upload_dataset(
    user: CurrentUserDep,
    dataset_service: DatasetServiceDep,
    settings: SettingsDep,
    dataset: UploadFile,
) -> DatasetUploadResult:
    content = await dataset.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="Dataset upload exceeds max_upload_size_mb")
    if not dataset.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename")
    try:
        return dataset_service.upload(user.id, dataset.filename, content)
    except DatasetUploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
async def list_datasets(user: CurrentUserDep, dataset_service: DatasetServiceDep) -> dict:
    return {"datasets": dataset_service.list_datasets(user.id)}


@router.get("/{dataset_id}", response_model=DatasetInfo)
async def get_dataset_info(
    dataset_id: str, user: CurrentUserDep, dataset_service: DatasetServiceDep
) -> DatasetInfo:
    try:
        return dataset_service.get_info(user.id, dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{dataset_id}/classes")
async def update_classes(
    dataset_id: str,
    body: UpdateClassesRequest,
    user: CurrentUserDep,
    dataset_service: DatasetServiceDep,
) -> dict:
    try:
        yaml_path = dataset_service.update_classes(user.id, dataset_id, body.classes)
    except DatasetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"yaml_path": yaml_path}
