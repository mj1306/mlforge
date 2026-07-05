import time

import pytest
from fastapi.testclient import TestClient


class _FakeRunner:
    """Stands in for YoloTrainingRunner so the training route can be
    exercised end-to-end without a real Ultralytics/GPU training run."""

    def __init__(self, model: str, hyperparams: dict) -> None:
        self.model = model
        self.hyperparams = hyperparams

    def train(
        self,
        data_yaml_path,
        *,
        epochs,
        batch,
        imgsz,
        lr0,
        project=None,
        name=None,
        progress_callback,
        cancel_check,
    ):
        progress_callback({"stage": "preparing", "epoch": 0})
        progress_callback({"stage": "training", "epoch": 1})
        return {"results_dir": "/fake/results"}


@pytest.fixture(autouse=True)
def _patch_yolo_trainer(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.ml.yolo_trainer as yolo_trainer_module

    monkeypatch.setattr(yolo_trainer_module, "YoloTrainingRunner", _FakeRunner)


def test_start_training_reaches_succeeded(client: TestClient, uploaded_dataset_id: str) -> None:
    response = client.post(
        "/training/jobs",
        json={"model": "yolov8n.yaml", "dataset_id": uploaded_dataset_id, "epochs": 1},
    )
    assert response.status_code == 202, response.text
    job_id = response.json()["job_id"]
    assert response.headers["location"] == f"/jobs/{job_id}"

    deadline = time.monotonic() + 5
    job = None
    while time.monotonic() < deadline:
        job = client.get(f"/jobs/{job_id}").json()
        if job["status"] in ("succeeded", "failed"):
            break
        time.sleep(0.02)

    assert job is not None
    assert job["status"] == "succeeded", job
    assert job["result"] == {"results_dir": "/fake/results"}
    assert job["progress"]["epoch"] == 1


def test_start_training_missing_dataset_404(client: TestClient) -> None:
    response = client.post(
        "/training/jobs",
        json={"model": "yolov8n.yaml", "dataset_id": "does-not-exist", "epochs": 1},
    )

    assert response.status_code == 404


def test_job_stream_replays_snapshot_and_terminal_event(
    client: TestClient, uploaded_dataset_id: str
) -> None:
    response = client.post(
        "/training/jobs",
        json={"model": "yolov8n.yaml", "dataset_id": uploaded_dataset_id, "epochs": 1},
    )
    job_id = response.json()["job_id"]

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if client.get(f"/jobs/{job_id}").json()["status"] == "succeeded":
            break
        time.sleep(0.02)

    with client.stream("GET", f"/jobs/{job_id}/stream") as stream:
        raw = next(stream.iter_lines())

    assert raw.startswith("data: ")


def test_stream_unknown_job_404(client: TestClient) -> None:
    response = client.get("/jobs/00000000-0000-0000-0000-000000000000/stream")

    assert response.status_code == 404
