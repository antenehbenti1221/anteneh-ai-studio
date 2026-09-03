"""Provider-independent remote GPU worker contract.

Any GPU provider can implement these operations. The web/API layer never needs
provider-specific model code.
"""
from dataclasses import dataclass
from typing import Protocol

@dataclass
class RenderRequest:
    job_id: str
    prompt: str
    duration: str
    input_mode: str
    language: str = "am"
    voice: str = "natural_male"
    style: str = "educational"
    aspect_ratio: str = "16:9"

class GPUWorker(Protocol):
    async def generate_script(self, request: RenderRequest) -> str: ...
    async def plan_scenes(self, script: str) -> list[dict]: ...
    async def generate_visuals(self, scenes: list[dict]) -> list[str]: ...
    async def generate_voice(self, script: str, language: str, voice: str) -> str: ...
    async def generate_captions(self, audio_path: str, language: str) -> str: ...
    async def render(self, scenes: list[str], audio_path: str, captions_path: str, aspect_ratio: str) -> str: ...
