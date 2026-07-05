from pathlib import Path

import yaml

from app.utils.yaml_utils import generate_data_yaml


def _touch_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xd8\xff")  # minimal JPEG-ish bytes, content is irrelevant here


def test_generate_data_yaml_train_val_test_layout(tmp_path: Path) -> None:
    _touch_image(tmp_path / "train" / "images" / "a.jpg")
    _touch_image(tmp_path / "valid" / "images" / "b.jpg")
    _touch_image(tmp_path / "test" / "images" / "c.jpg")
    (tmp_path / "classes.txt").write_text("cat\n")

    yaml_path, class_names = generate_data_yaml(str(tmp_path))

    assert yaml_path == str(tmp_path / "data.yaml")
    assert class_names == {0: "cat"}
    content = yaml.safe_load(Path(yaml_path).read_text())
    assert content["train"] == "train/images"
    assert content["val"] == "valid/images"
    assert content["test"] == "test/images"


def test_generate_data_yaml_falls_back_to_images_folder(tmp_path: Path) -> None:
    _touch_image(tmp_path / "images" / "a.jpg")

    yaml_path, class_names = generate_data_yaml(str(tmp_path))

    assert yaml_path is not None
    content = yaml.safe_load(Path(yaml_path).read_text())
    assert content["train"] == "images"
    assert content["val"] == "images"  # no val found -> reuse train


def test_generate_data_yaml_no_val_reuses_train(tmp_path: Path) -> None:
    _touch_image(tmp_path / "train" / "a.jpg")

    _yaml_path, _classes = generate_data_yaml(str(tmp_path))
    content = yaml.safe_load((tmp_path / "data.yaml").read_text())

    assert content["val"] == content["train"]


def test_generate_data_yaml_no_images_returns_none(tmp_path: Path) -> None:
    (tmp_path / "readme.txt").write_text("nothing here")

    yaml_path, class_names = generate_data_yaml(str(tmp_path))

    assert yaml_path is None
    assert class_names is None
