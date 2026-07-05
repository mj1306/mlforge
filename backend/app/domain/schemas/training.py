from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    model: str = "yolov8n.yaml"
    dataset_id: str
    epochs: int | None = None
    batch: int | None = None
    imgsz: int | None = None
    lr0: float | None = None
    hyperparams: dict[str, Any] = Field(default_factory=dict)


class TrainedModel(BaseModel):
    name: str
    created_at: datetime
    size_bytes: int
