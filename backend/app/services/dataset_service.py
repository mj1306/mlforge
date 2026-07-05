import logging
import re
import secrets
import zipfile
from pathlib import Path

import yaml

from app.core.config import Settings
from app.domain.schemas.dataset import DatasetInfo, DatasetUploadResult
from app.utils.dataset_utils import extract_class_names
from app.utils.file_utils import IMAGE_EXTENSIONS, delete_label_caches, make_writable
from app.utils.yaml_utils import generate_data_yaml

logger = logging.getLogger(__name__)

DATA_YAML_NAMES = {"data.yaml", "data.yml", "dataset.yaml"}


class DatasetError(Exception):
    pass


class DatasetNotFoundError(DatasetError):
    pass


class DatasetUploadError(DatasetError):
    pass


def _slugify(filename: str) -> str:
    stem = Path(filename).stem
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem).strip("-").lower()
    return slug or "dataset"


def _safe_extract(zip_path: Path, extract_to: Path) -> None:
    """Extract a zip archive guarding against path traversal ('zip slip'):
    reject any member whose resolved path would land outside extract_to."""
    extract_to = extract_to.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            target = (extract_to / member).resolve()
            if not str(target).startswith(str(extract_to)):
                raise DatasetUploadError(f"Unsafe path in archive: {member}")
        zf.extractall(extract_to)


class DatasetService:
    """All operations are scoped by owner: datasets live under
    dataset_dir/<user_id>/<dataset_id>, so one user's dataset ids simply do
    not resolve for another user (DatasetNotFoundError, surfaced as 404)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _user_root(self, user_id: str) -> Path:
        return self.settings.dataset_dir / user_id

    def upload(self, user_id: str, filename: str, content: bytes) -> DatasetUploadResult:
        dataset_id = f"{_slugify(filename)}-{secrets.token_hex(4)}"
        dataset_root = self._user_root(user_id) / dataset_id
        dataset_root.mkdir(parents=True, exist_ok=True)

        archive_path = dataset_root / filename
        archive_path.write_bytes(content)

        extract_root = dataset_root
        if filename.lower().endswith(".zip"):
            try:
                _safe_extract(archive_path, extract_root)
            except zipfile.BadZipFile as exc:
                raise DatasetUploadError(f"Invalid zip archive: {exc}") from exc
            make_writable(extract_root)
            archive_path.unlink(missing_ok=True)

        yaml_path = self._find_existing_yaml(extract_root)
        if yaml_path is None:
            generated_path, classes = generate_data_yaml(str(extract_root))
            if generated_path is None:
                raise DatasetUploadError(
                    "Could not generate data.yaml. Ensure the dataset contains images "
                    "under folders like 'train/images' or 'images/', with matching labels."
                )
            yaml_path = Path(generated_path)
        else:
            classes = self._load_classes(yaml_path, extract_root)

        delete_label_caches(extract_root)

        return DatasetUploadResult(
            dataset_id=dataset_id, yaml_path=str(yaml_path), classes=classes
        )

    def resolve_root(self, user_id: str, dataset_id: str) -> Path:
        root = self._user_root(user_id) / dataset_id
        if not root.is_dir():
            raise DatasetNotFoundError(dataset_id)
        return root

    def get_info(self, user_id: str, dataset_id: str) -> DatasetInfo:
        root = self.resolve_root(user_id, dataset_id)
        yaml_path = self._find_existing_yaml(root)
        if yaml_path is None:
            raise DatasetNotFoundError(f"No data.yaml found for dataset {dataset_id}")

        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        total_images = sum(1 for _ in root.rglob("*") if _.suffix.lower() in IMAGE_EXTENSIONS)

        return DatasetInfo(
            dataset_id=dataset_id, yaml_path=str(yaml_path), total_images=total_images, data=data
        )

    def list_datasets(self, user_id: str) -> list[str]:
        user_root = self._user_root(user_id)
        if not user_root.is_dir():
            return []
        return [
            entry.name
            for entry in user_root.iterdir()
            if entry.is_dir() and self._find_existing_yaml(entry) is not None
        ]

    def update_classes(self, user_id: str, dataset_id: str, classes: dict[int, str]) -> str:
        root = self.resolve_root(user_id, dataset_id)
        yaml_path = self._find_existing_yaml(root)
        if yaml_path is None:
            raise DatasetNotFoundError(f"No data.yaml found for dataset {dataset_id}")

        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        data["names"] = {int(k): v for k, v in classes.items()}
        yaml_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")
        delete_label_caches(root)
        return str(yaml_path)

    @staticmethod
    def _find_existing_yaml(root: Path) -> Path | None:
        for candidate in DATA_YAML_NAMES:
            direct = root / candidate
            if direct.is_file():
                return direct
        for path in root.rglob("*.yaml"):
            return path
        for path in root.rglob("*.yml"):
            return path
        return None

    @staticmethod
    def _load_classes(yaml_path: Path, dataset_root: Path) -> dict[int, str]:
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
            names = data.get("names")
            if isinstance(names, dict):
                return {int(k): v for k, v in names.items()}
            if isinstance(names, list):
                return dict(enumerate(names))
        except (OSError, yaml.YAMLError):
            logger.warning("Error loading existing yaml %s", yaml_path, exc_info=True)
        return extract_class_names(str(dataset_root))
