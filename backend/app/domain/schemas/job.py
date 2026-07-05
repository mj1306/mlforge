from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class JobKind(str, Enum):
    TRAINING = "training"
    PROCESSING = "processing"
    CVAT_LIFECYCLE = "cvat_lifecycle"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED)


class JobRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    kind: JobKind
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    progress: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    result: dict[str, Any] | None = None
    cancel_requested: bool = False
