from typing import TypedDict


class DeviceInfo(TypedDict):
    type: str
    name: str
    memory_gb: float
    display: str


def get_device_info() -> DeviceInfo:
    import torch

    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        memory_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        return {
            "type": "cuda",
            "name": name,
            "memory_gb": memory_gb,
            "display": f"GPU: {name} ({memory_gb}GB)",
        }
    return {
        "type": "cpu",
        "name": "CPU",
        "memory_gb": 0,
        "display": "CPU (no GPU available)",
    }
