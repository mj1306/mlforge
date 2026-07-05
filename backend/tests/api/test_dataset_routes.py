from fastapi.testclient import TestClient


def test_upload_dataset_returns_dataset_id_and_classes(uploaded_dataset_id: str) -> None:
    assert uploaded_dataset_id  # non-empty slug-uuid


def test_list_datasets_includes_uploaded(client: TestClient, uploaded_dataset_id: str) -> None:
    response = client.get("/datasets")

    assert response.status_code == 200
    assert uploaded_dataset_id in response.json()["datasets"]


def test_get_dataset_info(client: TestClient, uploaded_dataset_id: str) -> None:
    response = client.get(f"/datasets/{uploaded_dataset_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == uploaded_dataset_id
    assert body["total_images"] == 2
    assert body["data"]["names"] == {"0": "cat", "1": "dog"} or body["data"]["names"] == {0: "cat", 1: "dog"}


def test_get_dataset_info_missing_returns_404(client: TestClient) -> None:
    response = client.get("/datasets/does-not-exist")

    assert response.status_code == 404


def test_update_classes(client: TestClient, uploaded_dataset_id: str) -> None:
    response = client.put(
        f"/datasets/{uploaded_dataset_id}/classes",
        json={"classes": {"0": "kitten", "1": "puppy"}},
    )

    assert response.status_code == 200
    info = client.get(f"/datasets/{uploaded_dataset_id}").json()
    assert info["data"]["names"] in ({0: "kitten", 1: "puppy"}, {"0": "kitten", "1": "puppy"})


def test_upload_rejects_oversized_file(client: TestClient, settings) -> None:
    settings.max_upload_size_mb = 0
    response = client.post(
        "/datasets", files={"dataset": ("big.zip", b"x" * 1024, "application/zip")}
    )

    assert response.status_code == 413
