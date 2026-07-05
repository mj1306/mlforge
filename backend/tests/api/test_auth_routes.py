from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD, register_and_login


def test_register_sets_session_and_me_works(anon_client: TestClient):
    response = anon_client.post(
        "/auth/register", json={"username": "alice", "password": "supersecret1"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "alice"
    assert "mlforge_session" in anon_client.cookies

    me = anon_client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "alice"


def test_register_duplicate_username_conflicts(anon_client: TestClient):
    body = {"username": "alice", "password": "supersecret1"}
    assert anon_client.post("/auth/register", json=body).status_code == 201
    # Same username again (case-insensitive) is a 409.
    assert anon_client.post(
        "/auth/register", json={"username": "ALICE", "password": "supersecret1"}
    ).status_code == 409


def test_register_rejects_bad_usernames_and_short_passwords(anon_client: TestClient):
    assert anon_client.post(
        "/auth/register", json={"username": "a", "password": "supersecret1"}
    ).status_code == 422
    assert anon_client.post(
        "/auth/register", json={"username": "has space", "password": "supersecret1"}
    ).status_code == 422
    assert anon_client.post(
        "/auth/register", json={"username": "alice", "password": "short"}
    ).status_code == 422


def test_login_wrong_password_rejected(app, anon_client: TestClient):
    register_and_login(app, "alice")
    response = anon_client.post(
        "/auth/login", json={"username": "alice", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert anon_client.get("/auth/me").status_code == 401


def test_login_then_logout(app, anon_client: TestClient):
    register_and_login(app, "alice")

    response = anon_client.post(
        "/auth/login", json={"username": "alice", "password": TEST_PASSWORD}
    )
    assert response.status_code == 200
    assert anon_client.get("/auth/me").status_code == 200

    assert anon_client.post("/auth/logout").status_code == 204
    assert anon_client.get("/auth/me").status_code == 401


def test_data_routes_require_auth(anon_client: TestClient):
    assert anon_client.get("/datasets").status_code == 401
    assert anon_client.get("/models").status_code == 401
    assert anon_client.get("/jobs").status_code == 401
    assert anon_client.get("/cvat/status").status_code == 401
    # Health stays public (used by the Docker healthcheck).
    assert anon_client.get("/health").status_code == 200


def test_users_cannot_see_each_others_datasets(app, uploaded_dataset_id: str):
    other = register_and_login(app, "mallory")
    assert other.get("/datasets").json() == {"datasets": []}
    assert other.get(f"/datasets/{uploaded_dataset_id}").status_code == 404


def test_users_cannot_see_each_others_jobs(app, client: TestClient, monkeypatch):
    # Avoid a real Ultralytics run: submit through the real manager but with
    # a stub runner.
    class StubRunner:
        def __init__(self, *args, **kwargs):
            pass

        def train(self, *args, **kwargs):
            return {"results_dir": "stub"}

    monkeypatch.setattr(
        "app.ml.yolo_trainer.YoloTrainingRunner", StubRunner
    )

    upload = client.post(
        "/datasets",
        files={"dataset": ("d.zip", _tiny_zip(), "application/zip")},
    )
    assert upload.status_code == 201, upload.text
    dataset_id = upload.json()["dataset_id"]

    started = client.post("/training/jobs", json={"dataset_id": dataset_id})
    assert started.status_code == 202, started.text
    job_id = started.json()["job_id"]

    assert client.get(f"/jobs/{job_id}").status_code == 200
    assert any(j["id"] == job_id for j in client.get("/jobs").json()["jobs"])

    other = register_and_login(app, "mallory")
    assert other.get(f"/jobs/{job_id}").status_code == 404
    assert other.get("/jobs").json() == {"jobs": []}
    assert other.post(f"/jobs/{job_id}/cancel").status_code == 404


def _tiny_zip() -> bytes:
    import io
    import zipfile

    import cv2
    import numpy as np

    img = (np.random.rand(32, 32, 3) * 255).astype("uint8")
    ok, encoded = cv2.imencode(".jpg", img)
    assert ok
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("classes.txt", "cat\n")
        zf.writestr("train/images/img1.jpg", encoded.tobytes())
        zf.writestr("train/labels/img1.txt", "0 0.5 0.5 0.2 0.2\n")
        zf.writestr("valid/images/img2.jpg", encoded.tobytes())
        zf.writestr("valid/labels/img2.txt", "0 0.4 0.4 0.1 0.1\n")
    return buffer.getvalue()
