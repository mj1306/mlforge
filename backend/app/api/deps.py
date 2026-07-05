from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings
from app.domain.jobs.manager import JobManager
from app.domain.jobs.registry import JobRegistry
from app.services.cvat_service import CvatService
from app.services.dataset_service import DatasetService
from app.services.processing_service import ProcessingService
from app.services.training_service import TrainingService

# Every service is constructed once in main.create_app() and stashed on
# app.state, so each test can build its own isolated app (own tmp_path
# Settings, own JobRegistry) instead of fighting a process-wide singleton.


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_job_registry(request: Request) -> JobRegistry:
    return request.app.state.job_registry


def get_job_manager(request: Request) -> JobManager:
    return request.app.state.job_manager


def get_dataset_service(request: Request) -> DatasetService:
    return request.app.state.dataset_service


def get_processing_service(request: Request) -> ProcessingService:
    return request.app.state.processing_service


def get_training_service(request: Request) -> TrainingService:
    return request.app.state.training_service


def get_cvat_service(request: Request) -> CvatService:
    return request.app.state.cvat_service


SettingsDep = Annotated[Settings, Depends(get_settings)]
JobRegistryDep = Annotated[JobRegistry, Depends(get_job_registry)]
JobManagerDep = Annotated[JobManager, Depends(get_job_manager)]
DatasetServiceDep = Annotated[DatasetService, Depends(get_dataset_service)]
ProcessingServiceDep = Annotated[ProcessingService, Depends(get_processing_service)]
TrainingServiceDep = Annotated[TrainingService, Depends(get_training_service)]
CvatServiceDep = Annotated[CvatService, Depends(get_cvat_service)]
