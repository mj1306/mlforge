import io
import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient


def _make_dataset_zip() -> bytes:
    img = (np.random.rand(32, 32, 3) * 255).astype("uint8")
    import cv2

    ok, encoded = cv2.imencode(".jpg", img)
    assert ok
    image_bytes = encoded.tobytes()

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("classes.txt", "cat\ndog\n")
        zf.writestr("train/images/img1.jpg", image_bytes)
        zf.writestr("train/labels/img1.txt", "0 0.5 0.5 0.2 0.2\n")
        zf.writestr("valid/images/img2.jpg", image_bytes)
        zf.writestr("valid/labels/img2.txt", "1 0.4 0.4 0.1 0.1\n")
    return buffer.getvalue()


@pytest.fixture
def uploaded_dataset_id(client: TestClient) -> str:
    zip_bytes = _make_dataset_zip()
    response = client.post(
        "/datasets",
        files={"dataset": ("sample.zip", zip_bytes, "application/zip")},
    )
    assert response.status_code == 201, response.text
    return response.json()["dataset_id"]
