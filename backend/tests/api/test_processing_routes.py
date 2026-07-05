from pathlib import Path

from fastapi.testclient import TestClient


def test_processing_info_counts_images(client: TestClient, uploaded_dataset_id: str) -> None:
    response = client.get(f"/datasets/{uploaded_dataset_id}/processing/info")

    assert response.status_code == 200
    assert response.json()["total_images"] == 2


def test_random_image_returns_a_file(client: TestClient, uploaded_dataset_id: str) -> None:
    response = client.get(f"/datasets/{uploaded_dataset_id}/processing/random-image")

    assert response.status_code == 200
    assert len(response.content) > 0


def test_random_image_missing_dataset_404(client: TestClient) -> None:
    response = client.get("/datasets/does-not-exist/processing/random-image")

    assert response.status_code == 404


def test_apply_processing_is_non_destructive(
    client: TestClient, uploaded_dataset_id: str, settings
) -> None:
    dataset_root = settings.dataset_dir / uploaded_dataset_id
    original_bytes = (dataset_root / "train" / "images" / "img1.jpg").read_bytes()

    response = client.post(
        f"/datasets/{uploaded_dataset_id}/processing/apply",
        json={
            "brightness": 150,
            "contrast": 100,
            "saturation": 100,
            "hue": 0,
            "blur": 0,
            "sharpness": 0,
            "rotation": 0,
            "flipHorizontal": False,
            "flipVertical": False,
            "grayscale": False,
            "applyToCount": 0,
            "applyToAll": True,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["processed_images"] == 2

    # originals must be untouched
    assert (dataset_root / "train" / "images" / "img1.jpg").read_bytes() == original_bytes

    # processed output exists in a separate, versioned location
    processed_dir = Path(body["output_dir"])
    assert processed_dir.is_dir()
    assert any(processed_dir.rglob("*.jpg"))


def test_apply_processing_missing_dataset_404(client: TestClient) -> None:
    response = client.post(
        "/datasets/does-not-exist/processing/apply",
        json={
            "brightness": 100,
            "contrast": 100,
            "saturation": 100,
            "hue": 0,
            "blur": 0,
            "sharpness": 0,
            "rotation": 0,
            "flipHorizontal": False,
            "flipVertical": False,
            "grayscale": False,
            "applyToCount": 1,
            "applyToAll": False,
        },
    )

    assert response.status_code == 404
