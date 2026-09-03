from dataclasses import dataclass
from typing import Optional
import os
import httpx

@dataclass
class GPUJob:
    prompt: str
    duration_seconds: int
    language: str = "en"
    aspect_ratio: str = "16:9"
    input_type: str = "text"
    style: str = "educational"

class RemoteGPUError(RuntimeError):
    pass

class RemoteGPUWorker:
    """Generic worker client. Configure GPU_WORKER_URL in the server environment."""
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("GPU_WORKER_URL", "")).rstrip("/")

    async def submit(self, job: GPUJob) -> dict:
        if not self.base_url:
            raise RemoteGPUError("GPU_WORKER_URL is not configured")
        payload = {
            "prompt": job.prompt,
            "duration_seconds": job.duration_seconds,
            "language": job.language,
            "aspect_ratio": job.aspect_ratio,
            "input_type": job.input_type,
            "style": job.style,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.base_url}/jobs", json=payload)
            response.raise_for_status()
            return response.json()

    async def status(self, job_id: str) -> dict:
        if not self.base_url:
            raise RemoteGPUError("GPU_WORKER_URL is not configured")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/jobs/{job_id}")
            response.raise_for_status()
            return response.json()
