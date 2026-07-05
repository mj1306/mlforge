import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")


def make_writable(path: str | Path) -> None:
    """Recursively make all files/folders writable. Uploaded dataset
    archives are sometimes extracted with restrictive permissions that
    Ultralytics can't read back."""
    try:
        for root, dirs, files in os.walk(path):
            for d in dirs:
                try:
                    os.chmod(os.path.join(root, d), 0o777)
                except OSError:
                    pass
            for f in files:
                try:
                    os.chmod(os.path.join(root, f), 0o666)
                except OSError:
                    pass
    except OSError:
        logger.warning("Could not make all files writable under %s", path, exc_info=True)


def delete_label_caches(dataset_path: str | Path) -> int:
    """Delete all .cache files so YOLO regenerates them with the correct
    class count. Returns the number of cache files removed."""
    deleted = 0
    for root, _dirs, files in os.walk(dataset_path):
        for file in files:
            if file.endswith(".cache"):
                cache_path = os.path.join(root, file)
                try:
                    os.remove(cache_path)
                    deleted += 1
                except OSError:
                    logger.warning("Failed to delete cache file %s", cache_path, exc_info=True)
    return deleted


def find_images_recursive(path: str | Path) -> list[str]:
    image_files = []
    for root, _dirs, files in os.walk(path):
        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                image_files.append(os.path.join(root, file))
    return image_files
