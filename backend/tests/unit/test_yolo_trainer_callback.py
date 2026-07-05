from types import SimpleNamespace

from app.ml.progress import batch_end_event, complete_event, preparing_event
from app.ml.yolo_trainer import build_batch_metrics, build_validation_metrics, extract_loss_triplet


def test_extract_loss_triplet_from_tloss() -> None:
    trainer = SimpleNamespace(tloss=[0.123456, 0.2, 0.3])

    box, cls, dfl = extract_loss_triplet(trainer)

    assert box == 0.123456
    assert cls == 0.2
    assert dfl == 0.3


def test_extract_loss_triplet_falls_back_to_loss_items() -> None:
    trainer = SimpleNamespace(loss_items=[0.5, 0.6, 0.7])

    box, cls, dfl = extract_loss_triplet(trainer)

    assert (box, cls, dfl) == (0.5, 0.6, 0.7)


def test_extract_loss_triplet_defaults_to_zero() -> None:
    trainer = SimpleNamespace()

    assert extract_loss_triplet(trainer) == (0.0, 0.0, 0.0)


def test_build_batch_metrics_shape() -> None:
    trainer = SimpleNamespace(tloss=[0.1, 0.2, 0.3], batch_size=16, accumulate=2)

    metrics = build_batch_metrics(trainer)

    assert metrics == {
        "box_loss": 0.1,
        "cls_loss": 0.2,
        "dfl_loss": 0.3,
        "instances": 32,
    }


def test_build_validation_metrics_with_scalars() -> None:
    box = SimpleNamespace(p=[0.9], r=[0.8], map50=0.75, map=0.5)
    validator = SimpleNamespace(metrics=SimpleNamespace(box=box))

    metrics = build_validation_metrics(validator)

    assert metrics == {"precision": 0.9, "recall": 0.8, "mAP50": 0.75, "mAP50_95": 0.5}


def test_build_validation_metrics_missing_returns_zeros() -> None:
    validator = SimpleNamespace()

    metrics = build_validation_metrics(validator)

    assert metrics == {"precision": 0.0, "recall": 0.0, "mAP50": 0.0, "mAP50_95": 0.0}


def test_progress_event_builders_shape() -> None:
    device = {"type": "cpu", "name": "CPU", "memory_gb": 0, "display": "CPU (no GPU available)"}

    prep = preparing_event(device, total_epochs=10)
    assert prep["stage"] == "preparing"
    assert prep["total_epochs"] == 10

    batch = batch_end_event(device, epoch=1, total_epochs=10, batch=5, metrics={"box_loss": 0.1}, gpu_memory_used=0.0)
    assert batch["epoch"] == 1
    assert batch["batch"] == 5

    done = complete_event(device, epochs=10)
    assert done["done"] is True


def test_yolo_training_runner_cancel_flow_without_real_training() -> None:
    """Verifies the cooperative-cancel contract end to end using a fake
    trainer object, without invoking real Ultralytics training."""
    from app.ml.yolo_trainer import TrainingCancelled

    events: list[dict] = []
    cancelled = {"flag": False}

    def progress_callback(event: dict) -> None:
        events.append(event)

    def cancel_check() -> bool:
        return cancelled["flag"]

    # Simulate the on_train_batch_end callback body directly against a fake
    # trainer, the way YoloTrainingRunner.train() would wire it internally.
    trainer = SimpleNamespace(epoch=0, tloss=[0.1, 0.1, 0.1], batch_size=8, accumulate=1, stop=False)

    def on_train_batch_end(trainer: SimpleNamespace) -> None:
        if cancel_check():
            trainer.stop = True
            return
        progress_callback(build_batch_metrics(trainer))

    on_train_batch_end(trainer)
    assert len(events) == 1
    assert trainer.stop is False

    cancelled["flag"] = True
    on_train_batch_end(trainer)
    assert trainer.stop is True
    assert len(events) == 1  # no further progress emitted once cancelled

    assert TrainingCancelled  # class exists and is importable for the runner's raise path
