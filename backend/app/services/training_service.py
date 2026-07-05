from typing import Any

from app.core.config import Settings
from app.domain.jobs.manager import JobManager
from app.domain.schemas.job import JobRecord
from app.domain.schemas.training import ModelConfig
from app.services.dataset_service import DatasetService
from app.utils.file_utils import make_writable

DEFAULT_EPOCHS = 10
DEFAULT_BATCH = 16
DEFAULT_IMGSZ = 640
DEFAULT_LR0 = 0.01


class TrainingService:
    def __init__(
        self, settings: Settings, dataset_service: DatasetService, job_manager: JobManager
    ) -> None:
        self.settings = settings
        self.dataset_service = dataset_service
        self.job_manager = job_manager

    def start(self, config: ModelConfig) -> JobRecord:
        info = self.dataset_service.get_info(config.dataset_id)  # raises DatasetNotFoundError if missing
        data_yaml_path = info.yaml_path
        make_writable(self.dataset_service.resolve_root(config.dataset_id))

        def work(progress_callback, cancel_check) -> dict[str, Any]:
            from app.ml.yolo_trainer import YoloTrainingRunner

            runner = YoloTrainingRunner(config.model, config.hyperparams)
            return runner.train(
                data_yaml_path,
                epochs=config.epochs or DEFAULT_EPOCHS,
                batch=config.batch or DEFAULT_BATCH,
                imgsz=config.imgsz or DEFAULT_IMGSZ,
                lr0=config.lr0 or DEFAULT_LR0,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )

        return self.job_manager.submit_training(work)
