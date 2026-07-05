from pathlib import Path

from app.utils.dataset_utils import extract_class_names


def test_extract_class_names_from_classes_file(tmp_path: Path) -> None:
    (tmp_path / "classes.txt").write_text("person\ncar\ndog\n")

    result = extract_class_names(str(tmp_path))

    assert result == {0: "person", 1: "car", 2: "dog"}


def test_extract_class_names_scans_label_files_when_no_class_file(tmp_path: Path) -> None:
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()
    (labels_dir / "img1.txt").write_text("0 0.5 0.5 0.1 0.1\n2 0.4 0.4 0.2 0.2\n")
    (labels_dir / "img2.txt").write_text("1 0.3 0.3 0.1 0.1\n")

    result = extract_class_names(str(tmp_path))

    assert result == {0: "class_0", 1: "class_1", 2: "class_2"}


def test_extract_class_names_defaults_to_single_object_class(tmp_path: Path) -> None:
    (tmp_path / "readme.txt").write_text("not a label file")

    result = extract_class_names(str(tmp_path))

    assert result == {0: "object"}


def test_extract_class_names_ignores_malformed_label_lines(tmp_path: Path) -> None:
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()
    (labels_dir / "img1.txt").write_text("not-a-number 0.5 0.5 0.1 0.1\n0 0.1 0.1 0.1 0.1\n")

    result = extract_class_names(str(tmp_path))

    assert result == {0: "class_0"}
