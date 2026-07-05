import cv2
import numpy as np

from app.domain.schemas.processing import ImageProcessingSettings


def apply_transformations(img: np.ndarray, settings: ImageProcessingSettings) -> np.ndarray:
    """Pure function: takes an image array in, returns a new transformed
    array. Never touches the filesystem -- callers decide where the result
    is written."""
    img = img.astype(np.float32)

    if settings.brightness != 100:
        img = img * (settings.brightness / 100.0)

    if settings.contrast != 100:
        factor = settings.contrast / 100.0
        img = 128 + factor * (img - 128)

    img = np.clip(img, 0, 255).astype(np.uint8)

    if settings.saturation != 100 or settings.hue != 0:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
        if settings.saturation != 100:
            hsv[:, :, 1] = hsv[:, :, 1] * (settings.saturation / 100.0)
        if settings.hue != 0:
            hsv[:, :, 0] = (hsv[:, :, 0] + settings.hue) % 180
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    if settings.grayscale:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    if settings.blur > 0:
        kernel_size = int(settings.blur * 2) * 2 + 1
        img = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

    if settings.rotation != 0:
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, settings.rotation, 1.0)
        img = cv2.warpAffine(img, matrix, (w, h))

    if settings.flipHorizontal:
        img = cv2.flip(img, 1)

    if settings.flipVertical:
        img = cv2.flip(img, 0)

    return img
