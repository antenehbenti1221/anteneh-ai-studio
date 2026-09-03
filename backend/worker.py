"""Provider-independent remote GPU worker contract.

A deployment supplies concrete model adapters. The API/router never needs to know
which GPU vendor or model implementation is used.
"""
from dataclasses import dataclass
from typing import Protocol

@dataclass
class VideoJob:
    prompt: str
    duration_seconds: int
    language: str = "en"
    aspect_ratio: str = "16:9"
    input_type: str = "text"
    style: str = "educational"

class VideoWorker(Protocol):
    async def generate(self, job: VideoJob) -> str:
        """Generate and return a final MP4 object/path URL."""

class ModelWorker:
    """Adapter boundary for Wan/video, image, avatar, TTS and FFmpeg stages."""
    async def generate(self, job: VideoJob) -> str:
        raise NotImplementedError("Connect a remote GPU model adapter")

async def run_pipeline(job: VideoJob, worker: VideoWorker) -> str:
    # The orchestrator deliberately knows only the worker contract.
    return await worker.generate(job)
