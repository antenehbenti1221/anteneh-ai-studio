from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Anteneh AI Video Studio API", version="0.1.0")

class Duration(str, Enum):
    short = "short"
    medium = "medium"
    long = "long"

class VideoJob(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)
    duration: Duration = Duration.short
    input_mode: str = "text"
    voice: str = "natural_male"
    style: str = "educational"
    aspect_ratio: str = "16:9"
    language: str = "am"

jobs: dict[str, dict] = {}

@app.get("/health")
def health():
    return {"ok": True, "service": "anteneh-ai-video-studio", "time": datetime.now(timezone.utc)}

@app.post("/api/jobs", status_code=202)
def create_job(request: VideoJob):
    job_id = str(uuid4())
    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request": request.model_dump(),
        "stage": "waiting_for_gpu_worker",
        "progress": 0,
    }
    return jobs[job_id]

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job
