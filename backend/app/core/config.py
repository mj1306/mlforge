from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    dataset_dir: Path = Path("./data/datasets")
    models_dir: Path = Path("./data/models")
    logs_dir: Path = Path("./data/logs")

    # NoDecode stops pydantic-settings from trying to JSON-decode this env
    # var before our validator runs (it would otherwise reject a plain
    # comma-separated string like "http://a,http://b" as invalid JSON).
    cors_allow_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    max_upload_size_mb: int = 2048

    training_max_workers: int = 1
    processing_max_workers: int = 2

    # Points at the vendored upstream CVAT compose file (plain file, copied
    # from cvat-ai/cvat -- see docker/cvat/docker-compose.yml's header
    # comment). Health-checked over HTTP, not over the docker network, so
    # this URL must be reachable from wherever the backend process runs:
    # localhost for bare-metal dev, http://host.docker.internal:8080 when the
    # backend itself is inside the Docker Compose stack (see docker-compose.yml).
    cvat_url: str = "http://localhost:8080"
    # Default suits running the backend bare-metal from backend/ (dev mode).
    # docker-compose.yml overrides this to /app/docker/cvat/docker-compose.yml,
    # matching where docker/cvat is bind-mounted inside the container.
    cvat_compose_file: Path = Path("../docker/cvat/docker-compose.yml")
    cvat_startup_timeout_s: int = 120

    def ensure_dirs(self) -> None:
        for directory in (self.dataset_dir, self.models_dir, self.logs_dir):
            directory.mkdir(parents=True, exist_ok=True)
