from typing import Any, Protocol

from app.ml.device import DeviceInfo


class ProgressCallback(Protocol):
    def __call__(self, event: dict[str, Any]) -> None: ...


class CancelCheck(Protocol):
    def __call__(self) -> bool: ...


def preparing_event(device: DeviceInfo, total_epochs: int) -> dict[str, Any]:
    return {
        "stage": "preparing",
        "status": f"Starting training on {device['display']}...",
        "epoch": 0,
        "total_epochs": total_epochs,
        "device": device,
        "metrics": {"box_loss": 0.0, "cls_loss": 0.0, "dfl_loss": 0.0, "instances": 0},
    }


def epoch_start_event(device: DeviceInfo, epoch: int, total_epochs: int) -> dict[str, Any]:
    return {
        "stage": "training",
        "status": f"Epoch {epoch}/{total_epochs} - training on {device['display']}",
        "epoch": epoch,
        "live_data": [],
    }


def batch_end_event(
    device: DeviceInfo,
    epoch: int,
    total_epochs: int,
    batch: int,
    metrics: dict[str, float],
    gpu_memory_used: float,
) -> dict[str, Any]:
    return {
        "stage": "training",
        "status": f"Epoch {epoch}/{total_epochs} - batch {batch} - {device['type'].upper()}",
        "epoch": epoch,
        "batch": batch,
        "metrics": metrics,
        "gpu_memory_used": gpu_memory_used,
    }


def epoch_end_event(
    epoch: int, total_epochs: int, metrics: dict[str, float]
) -> dict[str, Any]:
    return {
        "stage": "validating",
        "status": f"Epoch {epoch}/{total_epochs} complete - validating...",
        "epoch": epoch,
        "last_epoch_metrics": metrics,
    }


def validation_event(validation: dict[str, float]) -> dict[str, Any]:
    return {"stage": "training", "validation": validation}


def complete_event(device: DeviceInfo, epochs: int) -> dict[str, Any]:
    return {
        "stage": "complete",
        "status": f"Training complete on {device['display']}",
        "epoch": epochs,
        "done": True,
    }


def cancelled_event() -> dict[str, Any]:
    return {"stage": "cancelled", "status": "Training cancelled", "done": True}
