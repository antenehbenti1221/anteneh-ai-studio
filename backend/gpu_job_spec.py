"""Portable GPU job specification used by remote workers."""
from dataclasses import asdict, dataclass
from typing import Literal

DurationClass = Literal["short", "medium", "long"]
InputType = Literal["text", "image", "avatar", "mixed"]
AspectRatio = Literal["16:9", "9:16", "1:1"]

@dataclass
class GPUJobSpec:
    prompt: str
    duration_seconds: int
    duration_class: DurationClass
    input_type: InputType
    language: str = "en"
    aspect_ratio: AspectRatio = "16:9"
    style: str = "educational"
    image_url: str | None = None
    avatar_id: str | None = None

    def validate(self) -> None:
        if not self.prompt.strip():
            raise ValueError("prompt is required")
        if self.duration_seconds < 1:
            raise ValueError("duration_seconds must be positive")
        if self.duration_class == "short" and self.duration_seconds > 60:
            raise ValueError("short jobs must be <= 60 seconds")
        if self.duration_class == "medium" and not 180 <= self.duration_seconds <= 300:
            raise ValueError("medium jobs must be 3-5 minutes")
        if self.duration_class == "long" and self.duration_seconds < 600:
            raise ValueError("long jobs must be at least 10 minutes")
        if self.input_type in {"image", "mixed"} and not self.image_url:
            raise ValueError("image_url is required for image/mixed jobs")
        if self.input_type == "avatar" and not self.avatar_id:
            raise ValueError("avatar_id is required for avatar jobs")

    def to_dict(self) -> dict:
        self.validate()
        return asdict(self)
