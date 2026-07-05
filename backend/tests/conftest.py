from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

TEST_USERNAME = "testuser"
TEST_PASSWORD = "password-123"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        dataset_dir=tmp_path / "datasets",
        models_dir=tmp_path / "models",
        logs_dir=tmp_path / "logs",
        auth_db_path=tmp_path / "auth.db",
    )


@pytest.fixture
def app(settings: Settings):
    app = create_app(settings=settings)
    app.state.settings.ensure_dirs()
    return app


@pytest.fixture
def anon_client(app) -> TestClient:
    """A client with no session -- for auth tests themselves."""
    return TestClient(app)


def register_and_login(app, username: str, password: str = TEST_PASSWORD) -> TestClient:
    """Each TestClient keeps its own cookie jar, so two clients against the
    same app behave like two different logged-in users."""
    client = TestClient(app)
    response = client.post("/auth/register", json={"username": username, "password": password})
    assert response.status_code == 201, response.text
    return client


@pytest.fixture
def client(app) -> TestClient:
    """The default fixture used across the API tests: a logged-in user."""
    return register_and_login(app, TEST_USERNAME)
