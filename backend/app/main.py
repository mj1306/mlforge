from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import cvat, datasets, health, jobs, processing, training
from app.core.config import Settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.domain.jobs.manager import JobManager
from app.domain.jobs.registry import InMemoryJobRegistry
from app.services.cvat_service import CvatService
from app.services.dataset_service import DatasetService
from app.services.processing_service import ProcessingService
from app.services.training_service import TrainingService


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    app.state.settings.ensure_dirs()
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    app = FastAPI(
        title="MLForge Backend",
        version="2.0.0",
        description="Machine learning model training API",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.job_registry = InMemoryJobRegistry()
    app.state.job_manager = JobManager(app.state.job_registry, settings)
    app.state.dataset_service = DatasetService(settings)
    app.state.processing_service = ProcessingService(settings, app.state.dataset_service)
    app.state.training_service = TrainingService(
        settings, app.state.dataset_service, app.state.job_manager
    )
    app.state.cvat_service = CvatService(settings, app.state.job_manager)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(datasets.router)
    app.include_router(processing.router)
    app.include_router(training.router)
    app.include_router(jobs.router)
    app.include_router(cvat.router)

    return app


app = create_app()
