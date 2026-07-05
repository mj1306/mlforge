from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.domain.jobs.manager import JobManager
from app.domain.schemas.job import JobRecord
from app.domain.schemas.training import ModelConfig, TrainedModel
from app.services.dataset_service import DatasetService
from app.utils.file_utils import make_writable

DEFAULT_EPOCHS = 10
DEFAULT_BATCH = 16
DEFAULT_IMGSZ = 640
DEFAULT_LR0 = 0.01

WEIGHTS_SUBPATH = Path("weights") / "best.pt"


class ModelNotFoundError(Exception):
    pass


class TrainingService:
    def __init__(
        self, settings: Settings, dataset_service: DatasetService, job_manager: JobManager
    ) -> None:
        self.settings = settings
        self.dataset_service = dataset_service
        self.job_manager = job_manager

    def _user_models_dir(self, user_id: str) -> Path:
        return self.settings.models_dir / user_id

    def start(self, user_id: str, config: ModelConfig) -> JobRecord:
        info = self.dataset_service.get_info(user_id, config.dataset_id)  # raises DatasetNotFoundError if missing
        data_yaml_path = info.yaml_path
        make_writable(self.dataset_service.resolve_root(user_id, config.dataset_id))

        # Ultralytics writes each run to <project>/<name>; pinning project to
        # the user's models dir is what makes trained models per-user.
        project_dir = self._user_models_dir(user_id)
        run_name = f"{config.model.replace('.pt', '')}-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"

        def work(progress_callback, cancel_check) -> dict[str, Any]:
            from app.ml.yolo_trainer import YoloTrainingRunner

            runner = YoloTrainingRunner(config.model, config.hyperparams)
            return runner.train(
                data_yaml_path,
                epochs=config.epochs or DEFAULT_EPOCHS,
                batch=config.batch or DEFAULT_BATCH,
                imgsz=config.imgsz or DEFAULT_IMGSZ,
                lr0=config.lr0 or DEFAULT_LR0,
                project=str(project_dir),
                name=run_name,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )

        return self.job_manager.submit_training(work, owner_id=user_id)

    def list_models(self, user_id: str) -> list[TrainedModel]:
        models_dir = self._user_models_dir(user_id)
        if not models_dir.is_dir():
            return []
        models = []
        for run_dir in sorted(models_dir.iterdir()):
            weights = run_dir / WEIGHTS_SUBPATH
            if not weights.is_file():
                continue
            stat = weights.stat()
            models.append(
                TrainedModel(
                    name=run_dir.name,
                    created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                    size_bytes=stat.st_size,
                )
            )
        models.sort(key=lambda m: m.created_at, reverse=True)
        return models

    def resolve_weights(self, user_id: str, model_name: str) -> Path:
        # model_name comes from a URL path segment; reject anything that
        # could escape the user's models dir.
        if "/" in model_name or "\\" in model_name or model_name in (".", ".."):
            raise ModelNotFoundError(model_name)
        weights = self._user_models_dir(user_id) / model_name / WEIGHTS_SUBPATH
        if not weights.is_file():
            raise ModelNotFoundError(model_name)
        return weights
