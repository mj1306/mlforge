from pydantic import BaseModel


class ImageProcessingSettings(BaseModel):
    brightness: int = 100
    contrast: int = 100
    saturation: int = 100
    hue: int = 0
    blur: float = 0
    sharpness: float = 0
    rotation: int = 0
    flipHorizontal: bool = False
    flipVertical: bool = False
    grayscale: bool = False
    applyToCount: int = 0
    applyToAll: bool = False


class ApplyProcessingRequest(BaseModel):
    dataset_id: str
    settings: ImageProcessingSettings


class ProcessingResult(BaseModel):
    processed_images: int
    total_requested: int
    output_dir: str
    errors: list[str] = []
