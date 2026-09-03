"""Open-model adapter boundaries for the remote GPU worker.

Keep model-specific code behind these interfaces so the control plane stays
independent of any single GPU host or AI vendor.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass
class Scene:
    prompt: str
    seconds: float

class VisualGenerator(Protocol):
    async def generate(self, scene: Scene, output_dir: Path) -> Path: ...

class SpeechGenerator(Protocol):
    async def synthesize(self, text: str, language: str, output_dir: Path) -> Path: ...

class CaptionGenerator(Protocol):
    async def transcribe(self, audio: Path, language: str, output_dir: Path) -> Path: ...

class VideoAssembler(Protocol):
    async def render(self, clips: list[Path], audio: Path, captions: Path | None, output: Path, aspect_ratio: str) -> Path: ...

@dataclass
class OpenModelStack:
    """Concrete GPU deployment injects Wan/image/TTS/caption/FFmpeg adapters."""
    visual: VisualGenerator
    speech: SpeechGenerator
    captions: CaptionGenerator
    assembler: VideoAssembler

async def render_video(stack: OpenModelStack, scenes: list[Scene], voice_text: str, language: str, aspect_ratio: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    clips = [await stack.visual.generate(scene, output_dir) for scene in scenes]
    audio = await stack.speech.synthesize(voice_text, language, output_dir)
    captions = await stack.captions.transcribe(audio, language, output_dir)
    return await stack.assembler.render(clips, audio, captions, output_dir / "final.mp4", aspect_ratio)
