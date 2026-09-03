"""Remote GPU worker HTTP API with configurable inference runner."""
import asyncio
import json
import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Anteneh AI Studio GPU Worker", version="0.2.0")
ROOT = Path(os.getenv("WORK_DIR", "/tmp/anteneh-ai-jobs"))
ROOT.mkdir(parents=True, exist_ok=True)
RUNNER = os.getenv("VIDEO_RUNNER_CMD", "")

class Job(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    duration_seconds: int = Field(ge=1, le=3600)
    language: str = "en"
    aspect_ratio: str = "16:9"
    input_type: str = "text"
    image_url: str | None = None
    avatar: bool = False

def write_status(folder: Path, status: str, **extra):
    (folder / "status.json").write_text(json.dumps({"status": status, **extra}), encoding="utf-8")

async def run_job(job_id: str):
    folder = ROOT / job_id
    job_file = folder / "job.json"
    output = folder / "final.mp4"
    write_status(folder, "running")
    if not RUNNER:
        write_status(folder, "waiting_for_runner", message="Configure VIDEO_RUNNER_CMD on the GPU host")
        return
    try:
        cmd = RUNNER.format(job=str(job_file), output=str(output))
        proc = await asyncio.create_subprocess_shell(cmd, cwd=str(folder))
        code = await proc.wait()
        if code == 0 and output.exists() and output.stat().st_size > 0:
            write_status(folder, "completed", output=str(output))
        else:
            write_status(folder, "failed", exit_code=code)
    except Exception as exc:
        write_status(folder, "failed", error=str(exc))

@app.get("/health")
async def health():
    return {"ok": True, "worker": "remote-gpu", "model": os.getenv("VIDEO_MODEL", "Wan2.2-TI2V-5B")}

@app.post("/jobs")
async def create_job(job: Job):
    job_id = str(uuid.uuid4())
    folder = ROOT / job_id
    folder.mkdir()
    (folder / "job.json").write_text(job.model_dump_json(indent=2), encoding="utf-8")
    write_status(folder, "queued")
    asyncio.create_task(run_job(job_id))
    return {"job_id": job_id, "status": "queued"}

@app.get("/jobs/{job_id}")
async def status(job_id: str):
    status_file = ROOT / job_id / "status.json"
    if not status_file.exists():
        raise HTTPException(404, "Job not found")
    return {"job_id": job_id, **json.loads(status_file.read_text(encoding="utf-8"))}
