import logging
from typing import Any

from app.ml import progress as progress_events
from app.ml.device import DeviceInfo, get_device_info
from app.ml.progress import CancelCheck, ProgressCallback

logger = logging.getLogger(__name__)


def extract_loss_triplet(trainer: Any) -> tuple[float, float, float]:
    """Pull (box_loss, cls_loss, dfl_loss) off an Ultralytics trainer's
    running-average tloss tensor, matching what Ultralytics prints to
    console. Falls back to loss_items if tloss is unavailable/malformed."""
    tloss = getattr(trainer, "tloss", None)
    if tloss is not None and hasattr(tloss, "__len__") and len(tloss) >= 3:
        try:
            return tuple(  # type: ignore[return-value]
                float(v.item() if hasattr(v, "item") else v) for v in tloss[:3]
            )
        except Exception:
            logger.warning("Could not extract tloss, falling back to loss_items", exc_info=True)

    loss_items = getattr(trainer, "loss_items", None)
    if loss_items is not None:
        return (
            float(loss_items[0]) if len(loss_items) > 0 else 0.0,
            float(loss_items[1]) if len(loss_items) > 1 else 0.0,
            float(loss_items[2]) if len(loss_items) > 2 else 0.0,
        )
    return (0.0, 0.0, 0.0)


def build_batch_metrics(trainer: Any) -> dict[str, float]:
    box_loss, cls_loss, dfl_loss = extract_loss_triplet(trainer)
    instances = getattr(trainer, "batch_size", 0) * getattr(trainer, "accumulate", 1)
    return {
        "box_loss": round(box_loss, 4),
        "cls_loss": round(cls_loss, 4),
        "dfl_loss": round(dfl_loss, 4),
        "instances": instances,
    }


def build_validation_metrics(validator: Any) -> dict[str, float]:
    box_metrics = getattr(getattr(validator, "metrics", None), "box", None)
    if box_metrics is None:
        return {"precision": 0.0, "recall": 0.0, "mAP50": 0.0, "mAP50_95": 0.0}

    def _scalar(value: Any) -> float:
        if isinstance(value, (list, tuple)):
            return float(value[0]) if value else 0.0
        return float(value) if value is not None else 0.0

    try:
        return {
            "precision": _scalar(getattr(box_metrics, "p", None)),
            "recall": _scalar(getattr(box_metrics, "r", None)),
            "mAP50": float(getattr(box_metrics, "map50", 0.0) or 0.0),
            "mAP50_95": float(getattr(box_metrics, "map", 0.0) or 0.0),
        }
    except Exception:
        logger.warning("Could not extract validation metrics", exc_info=True)
        return {"precision": 0.0, "recall": 0.0, "mAP50": 0.0, "mAP50_95": 0.0}


class TrainingCancelled(Exception):
    pass


class YoloTrainingRunner:
    """Thin wrapper around ultralytics.YOLO. Takes a progress_callback and
    cancel_check as plain constructor/method arguments -- no import of
    FastAPI, the job registry, or any app-layer global state, so it is
    unit-testable without a running server or a real training run."""

    def __init__(self, model_name: str, hyperparams: dict[str, Any] | None = None) -> None:
        from ultralytics import YOLO

        self.device_info: DeviceInfo = get_device_info()
        self._model = YOLO(model_name)
        self._model.overrides.update(hyperparams or {})
        if "device" not in self._model.overrides:
            self._model.overrides["device"] = 0 if self.device_info["type"] == "cuda" else "cpu"

    def train(
        self,
        data_yaml_path: str,
        *,
        epochs: int = 10,
        batch: int = 16,
        imgsz: int = 640,
        lr0: float = 0.01,
        progress_callback: ProgressCallback,
        cancel_check: CancelCheck | None = None,
    ) -> dict[str, Any]:
        progress_callback(progress_events.preparing_event(self.device_info, epochs))

        batch_counter = [0]

        def on_train_epoch_start(trainer: Any) -> None:
            batch_counter[0] = 0
            epoch = trainer.epoch + 1
            progress_callback(progress_events.epoch_start_event(self.device_info, epoch, epochs))

        def on_train_batch_end(trainer: Any) -> None:
            if cancel_check is not None and cancel_check():
                trainer.stop = True
                return
            if not hasattr(trainer, "epoch"):
                return
            epoch = trainer.epoch + 1
            batch_counter[0] += 1
            metrics = build_batch_metrics(trainer)
            gpu_memory_used = self._gpu_memory_used()
            progress_callback(
                progress_events.batch_end_event(
                    self.device_info, epoch, epochs, batch_counter[0], metrics, gpu_memory_used
                )
            )

        def on_train_epoch_end(trainer: Any) -> None:
            epoch = trainer.epoch + 1
            box_loss, cls_loss, dfl_loss = extract_loss_triplet(trainer)
            progress_callback(
                progress_events.epoch_end_event(
                    epoch,
                    epochs,
                    {"box_loss": round(box_loss, 4), "cls_loss": round(cls_loss, 4), "dfl_loss": round(dfl_loss, 4)},
                )
            )

        def on_val_end(validator: Any) -> None:
            progress_callback(progress_events.validation_event(build_validation_metrics(validator)))

        self._model.add_callback("on_train_epoch_start", on_train_epoch_start)
        self._model.add_callback("on_train_batch_end", on_train_batch_end)
        self._model.add_callback("on_train_epoch_end", on_train_epoch_end)
        self._model.add_callback("on_val_end", on_val_end)

        results = self._model.train(
            data=data_yaml_path,
            epochs=epochs,
            batch=batch,
            imgsz=imgsz,
            lr0=lr0,
            verbose=True,
            device=self._model.overrides.get("device"),
        )

        if cancel_check is not None and cancel_check():
            progress_callback(progress_events.cancelled_event())
            raise TrainingCancelled("Training was cancelled")

        progress_callback(progress_events.complete_event(self.device_info, epochs))
        return {"results_dir": str(getattr(results, "save_dir", ""))}

    def evaluate(self, data_yaml_path: str) -> Any:
        return self._model.val(data=data_yaml_path, device=self._model.overrides.get("device"))

    def _gpu_memory_used(self) -> float:
        if self.device_info["type"] != "cuda":
            return 0.0
        import torch

        return round(torch.cuda.memory_allocated(0) / (1024**3), 2)
