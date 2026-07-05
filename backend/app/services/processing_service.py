import random
from pathlib import Path

import cv2

from app.core.config import Settings
from app.domain.schemas.processing import ImageProcessingSettings, ProcessingResult
from app.services.dataset_service import DatasetService
from app.services.image_transforms import apply_transformations
from app.utils.file_utils import IMAGE_EXTENSIONS

PROCESSED_DIRNAME = "processed"


class ProcessingError(Exception):
    pass


class NoImagesFoundError(ProcessingError):
    pass


def _find_images(root: Path) -> list[Path]:
    return [
        p
        for p in root.rglob("*")
        if p.suffix.lower() in IMAGE_EXTENSIONS and PROCESSED_DIRNAME not in p.relative_to(root).parts
    ]


class ProcessingService:
    def __init__(self, settings: Settings, dataset_service: DatasetService) -> None:
        self.settings = settings
        self.dataset_service = dataset_service

    def get_random_image(self, dataset_id: str) -> Path:
        root = self.dataset_service.resolve_root(dataset_id)
        images = _find_images(root)
        if not images:
            raise NoImagesFoundError(f"No images found in dataset {dataset_id}")
        return random.choice(images)

    def count_images(self, dataset_id: str) -> int:
        root = self.dataset_service.resolve_root(dataset_id)
        return len(_find_images(root))

    def apply_processing(
        self, dataset_id: str, settings: ImageProcessingSettings
    ) -> ProcessingResult:
        root = self.dataset_service.resolve_root(dataset_id)
        images = _find_images(root)
        if not images:
            raise NoImagesFoundError(f"No images found in dataset {dataset_id}")

        images_to_process = images if settings.applyToAll else images[: settings.applyToCount]

        output_dir = root / PROCESSED_DIRNAME
        output_dir.mkdir(parents=True, exist_ok=True)

        processed_count = 0
        errors: list[str] = []

        for img_path in images_to_process:
            try:
                img = cv2.imread(str(img_path))
                if img is None:
                    errors.append(f"Could not read {img_path.name}")
                    continue

                processed = apply_transformations(img, settings)

                relative = img_path.relative_to(root)
                out_path = output_dir / relative
                out_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(out_path), processed)
                processed_count += 1
            except (OSError, cv2.error) as exc:
                errors.append(f"Error processing {img_path.name}: {exc}")

        return ProcessingResult(
            processed_images=processed_count,
            total_requested=len(images_to_process),
            output_dir=str(output_dir),
            errors=errors,
        )
