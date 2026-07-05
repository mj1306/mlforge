from pydantic import BaseModel


class DatasetUploadResult(BaseModel):
    dataset_id: str
    yaml_path: str
    classes: dict[int, str]


class DatasetInfo(BaseModel):
    dataset_id: str
    yaml_path: str
    total_images: int
    data: dict


class DatasetSummary(BaseModel):
    dataset_id: str


class UpdateClassesRequest(BaseModel):
    classes: dict[int, str]
