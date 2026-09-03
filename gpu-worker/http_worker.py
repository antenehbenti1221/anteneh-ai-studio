"""Remote GPU worker HTTP API with configurable inference runner."""
import asyncio
import json
import os
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Anteneh AI Studio GPU Worker", version="0.4.0")
ROOT = Path(os.getenv("WORK_DIR", "/tmp/anteneh-ai-jobs"))
ROOT.mkdir(parents=True, exist_ok=True)
RUNNER = os.getenv("VIDEO_RUNNER_CMD", "python runner.py {job} {output}")

class Job(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    duration_seconds: int = Field(ge=1, le=3600)
    language: str = "en"
    aspect_ratio: str = "16:9"
    input_type: str = "text"
    image_url: str | None = None
    avatar: bool = False
    voice: str = "default"
    style: str = "educational"

def write_status(folder: Path, status: str, **extra):
    (folder / "status.json").write_text(json.dumps({"status": status, **extra}), encoding="utf-8")

async def run_job(job_id: str):
    folder = ROOT / job_id
    job_file = folder / "job.json"
    output = folder / "final.mp4"
    write_status(folder, "running")
    try:
        cmd = RUNNER.format(job=str(job_file), output=str(output))
        proc = await asyncio.create_subprocess_shell(cmd, cwd=str(folder))
        code = await proc.wait()
        if code == 0 and output.exists() and output.stat().st_size > 0:
            write_status(folder, "completed")
        else:
            write_status(folder, "failed", exit_code=code)
    except Exception as exc:
        write_status(folder, "failed", error=str(exc))

@app.get("/health")
async def health():
    return {"ok": True, "worker": "remote-gpu", "model": os.getenv("VIDEO_MODEL", "Wan2.2-TI2V-5B"), "runner_configured": bool(os.getenv("VIDEO_COMMAND"))}

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
    folder = ROOT / job_id
    status_file = folder / "status.json"
    if not status_file.exists():
        raise HTTPException(404, "Job not found")
    data = json.loads(status_file.read_text(encoding="utf-8"))
    if data.get("status") == "completed":
        data["output_url"] = f"/jobs/{job_id}/video"
    return {"job_id": job_id, **data}

@app.get("/jobs/{job_id}/video")
async def video(job_id: str):
    output = ROOT / job_id / "final.mp4"
    if not output.exists() or output.stat().st_size == 0:
        raise HTTPException(404, "Video is not ready")
    return FileResponse(output, media_type="video/mp4", filename=f"anteneh-{job_id}.mp4")
