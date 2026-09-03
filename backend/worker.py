"""Provider-independent remote GPU worker contract and pipeline dispatcher."""
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
    image_path: str | None = None

class VideoWorker(Protocol):
    async def generate(self, job: VideoJob) -> str:
        """Generate and return a final MP4 object/path URL."""

class RemoteGPUWorker:
    """HTTP adapter: the control plane stays independent of the GPU provider."""
    def __init__(self, endpoint: str, token: str | None = None):
        self.endpoint = endpoint.rstrip("/")
        self.token = token

    async def generate(self, job: VideoJob) -> str:
        # The concrete GPU service implements this contract.
        # Keeping the network boundary here means providers can be swapped later.
        raise NotImplementedError("Configure a remote GPU worker endpoint")

async def run_pipeline(job: VideoJob, worker: VideoWorker) -> str:
    """Dispatch one complete production job to remote GPU infrastructure."""
    if job.duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    if job.aspect_ratio not in {"16:9", "9:16", "1:1"}:
        raise ValueError("unsupported aspect ratio")
    return await worker.generate(job)
