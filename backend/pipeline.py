"""End-to-end production pipeline manifest and stage orchestration."""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Protocol
import json

@dataclass
class RenderManifest:
    prompt: str
    duration_seconds: int
    language: str = "en"
    aspect_ratio: str = "16:9"
    style: str = "educational"
    voice: str = "natural"
    input_type: str = "text"
    image_url: str | None = None
    avatar_id: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

STAGES = ["script", "storyboard", "visuals", "voiceover", "captions", "music_sfx", "ffmpeg_render", "quality_check", "upload"]

class Stage(Protocol):
    async def run(self, job: RenderManifest, workdir: Path) -> Path: ...

def build_manifest(data: dict[str, Any]) -> RenderManifest:
    duration = int(data.get("duration_seconds", 60))
    if duration < 1:
        raise ValueError("duration_seconds must be positive")
    aspect = str(data.get("aspect_ratio", "16:9"))
    if aspect not in {"16:9", "9:16", "1:1"}:
        raise ValueError("aspect_ratio must be 16:9, 9:16, or 1:1")
    return RenderManifest(
        prompt=str(data.get("prompt", "")).strip(),
        duration_seconds=duration,
        language=str(data.get("language", "en")),
        aspect_ratio=aspect,
        style=str(data.get("style", "educational")),
        voice=str(data.get("voice", "natural")),
        input_type=str(data.get("input_type", "text")),
        image_url=data.get("image_url"),
        avatar_id=data.get("avatar_id"),
    )

class Pipeline:
    def __init__(self, *stages: Stage):
        self.stages = stages

    async def run(self, job: RenderManifest, workdir: Path) -> Path:
        current = workdir
        for stage in self.stages:
            current = await stage.run(job, current)
        return current
