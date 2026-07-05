import logging
import os

logger = logging.getLogger(__name__)

CLASS_FILE_NAMES = {"classes.txt", "names.txt", "obj.names", "coco.names", "class.names"}


def extract_class_names(dataset_path: str) -> dict[int, str]:
    """Extract class names either from a class-definition file (classes.txt
    etc) or, failing that, by scanning YOLO label files for the highest
    class id and synthesizing placeholder names for the full range."""
    for root, _dirs, files in os.walk(dataset_path):
        for file in files:
            if file in CLASS_FILE_NAMES:
                class_file = os.path.join(root, file)
                try:
                    with open(class_file, encoding="utf-8") as f:
                        classes = [line.strip() for line in f if line.strip()]
                    return dict(enumerate(classes))
                except OSError:
                    logger.warning("Error reading class file %s", class_file, exc_info=True)
                    continue

    max_class_id = -1
    label_paths: list[str] = []
    for root, _dirs, files in os.walk(dataset_path):
        prioritize = "label" in root.lower()
        for file in files:
            if file.endswith(".txt") and not file.startswith("."):
                if prioritize:
                    label_paths.insert(0, os.path.join(root, file))
                else:
                    label_paths.append(os.path.join(root, file))

    for label_path in label_paths:
        try:
            with open(label_path, encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        try:
                            class_id = int(float(parts[0]))
                            max_class_id = max(max_class_id, class_id)
                        except (ValueError, IndexError):
                            continue
        except OSError:
            continue

    if max_class_id >= 0:
        return {i: f"class_{i}" for i in range(max_class_id + 1)}

    return {0: "object"}
