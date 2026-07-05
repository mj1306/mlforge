import logging
import os

import yaml

from app.utils.dataset_utils import extract_class_names
from app.utils.file_utils import find_images_recursive, make_writable

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


def generate_data_yaml(dataset_path: str) -> tuple[str, dict[int, str]] | tuple[None, None]:
    """Dynamically generate data.yaml for a YOLO dataset of unknown layout,
    heuristically locating train/val/test image folders."""
    try:
        contents = os.listdir(dataset_path)
    except OSError:
        logger.warning("Error listing directory %s", dataset_path, exc_info=True)
        return None, None

    train_path: str | None = None
    val_path: str | None = None
    test_path: str | None = None

    for root, _dirs, files in os.walk(dataset_path):
        rel_root = os.path.relpath(root, dataset_path)
        image_files = [f for f in files if f.lower().endswith(IMAGE_EXTENSIONS)]
        if not image_files:
            continue

        root_lower = root.lower()
        candidate = "." if rel_root == "." else rel_root.replace("\\", "/")

        if "train" in root_lower and not train_path:
            train_path = candidate
        elif any(x in root_lower for x in ("val", "valid", "validation")) and not val_path:
            val_path = candidate
        elif "test" in root_lower and not test_path:
            test_path = candidate

    if not train_path:
        images_dir = os.path.join(dataset_path, "images")
        if os.path.exists(images_dir) and find_images_recursive(images_dir):
            train_path = "images"

        if not train_path:
            root_images = [f for f in contents if f.lower().endswith(IMAGE_EXTENSIONS)]
            if root_images:
                train_path = "."

        if not train_path:
            for item in contents:
                item_path = os.path.join(dataset_path, item)
                if os.path.isdir(item_path) and find_images_recursive(item_path):
                    train_path = item
                    break

    if not train_path:
        logger.warning("Could not find any images in dataset %s", dataset_path)
        return None, None

    if not val_path:
        val_path = train_path

    class_names = extract_class_names(dataset_path)

    yaml_content = {
        "path": dataset_path.replace("\\", "/"),
        "train": train_path.replace("\\", "/"),
        "val": val_path.replace("\\", "/"),
        "names": class_names,
    }
    if test_path:
        yaml_content["test"] = test_path.replace("\\", "/")

    yaml_path = os.path.join(dataset_path, "data.yaml")
    try:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)
        make_writable(yaml_path)
        return yaml_path, class_names
    except OSError:
        logger.error("Error writing yaml file %s", yaml_path, exc_info=True)
        return None, None
