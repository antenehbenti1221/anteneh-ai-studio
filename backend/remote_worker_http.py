"""Async HTTP client for the remote GPU worker."""
import os
import httpx
from .worker import VideoJob

class RemoteWorkerClient:
    def __init__(self, endpoint: str | None = None, token: str | None = None):
        self.endpoint = (endpoint or os.getenv("GPU_WORKER_URL", "")).rstrip("/")
        self.token = token or os.getenv("GPU_WORKER_TOKEN")
        if not self.endpoint:
            raise ValueError("GPU_WORKER_URL is not configured")

    async def submit(self, job: VideoJob) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        payload = {
            "prompt": job.prompt,
            "duration_seconds": job.duration_seconds,
            "language": job.language,
            "aspect_ratio": job.aspect_ratio,
            "input_type": job.input_type,
            "style": job.style,
            "image_path": job.image_path,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.endpoint}/jobs", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def status(self, job_id: str) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.endpoint}/jobs/{job_id}", headers=headers)
            response.raise_for_status()
            return response.json()
