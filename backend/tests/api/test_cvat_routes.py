from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.schemas.cvat import CvatState, CvatStatus


@pytest.fixture(autouse=True)
def _patch_cvat_service(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    service = client.app.state.cvat_service
    monkeypatch.setattr(service, "status", AsyncMock(return_value=CvatStatus(state=CvatState.STOPPED)))
    monkeypatch.setattr(
        service, "start", AsyncMock(return_value=CvatStatus(state=CvatState.STARTING, job_id="abc"))
    )
    monkeypatch.setattr(service, "stop", AsyncMock(return_value=CvatStatus(state=CvatState.STOPPED)))


def test_get_status(client: TestClient) -> None:
    response = client.get("/cvat/status")

    assert response.status_code == 200
    assert response.json()["state"] == "stopped"


def test_start_cvat(client: TestClient) -> None:
    response = client.post("/cvat/start")

    assert response.status_code == 200
    assert response.json()["state"] == "starting"
    assert response.json()["job_id"] == "abc"


def test_stop_cvat(client: TestClient) -> None:
    response = client.post("/cvat/stop")

    assert response.status_code == 200
    assert response.json()["state"] == "stopped"
