from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        dataset_dir=tmp_path / "datasets",
        models_dir=tmp_path / "models",
        logs_dir=tmp_path / "logs",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings=settings)
    app.state.settings.ensure_dirs()
    return TestClient(app)
