from enum import Enum

from pydantic import BaseModel


class CvatState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class CvatStatus(BaseModel):
    state: CvatState
    url: str | None = None
    job_id: str | None = None
    detail: str | None = None
