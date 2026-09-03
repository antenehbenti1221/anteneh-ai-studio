"""Minimal HTTP worker endpoint for a remote GPU host.

It intentionally exposes a provider-neutral job contract. Put the concrete
Wan/TTS/FFmpeg execution behind `run_job` on the GPU machine.
"""
import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Anteneh AI Studio GPU Worker", version="0.1.0")
ROOT = Path(os.getenv("WORK_DIR", "/tmp/anteneh-ai-jobs"))
ROOT.mkdir(parents=True, exist_ok=True)

class Job(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    duration_seconds: int = Field(ge=1, le=3600)
    language: str = "en"
    aspect_ratio: str = "16:9"
    input_type: str = "text"
    image_url: str | None = None
    avatar: bool = False

@app.get("/health")
async def health():
    return {"ok": True, "worker": "remote-gpu", "model": os.getenv("VIDEO_MODEL", "Wan2.2-TI2V-5B")}

@app.post("/jobs")
async def create_job(job: Job):
    job_id = str(uuid.uuid4())
    folder = ROOT / job_id
    folder.mkdir()
    (folder / "job.json").write_text(job.model_dump_json(indent=2), encoding="utf-8")
    # A real deployment replaces this handoff with the GPU queue/inference runner.
    return {"job_id": job_id, "status": "queued", "message": "Accepted by remote GPU worker"}

@app.get("/jobs/{job_id}")
async def status(job_id: str):
    folder = ROOT / job_id
    if not folder.exists():
        raise HTTPException(404, "Job not found")
    output = folder / "final.mp4"
    if output.exists() and output.stat().st_size > 0:
        return {"job_id": job_id, "status": "completed", "output": str(output)}
    return {"job_id": job_id, "status": "queued"}
