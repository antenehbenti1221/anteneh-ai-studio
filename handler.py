import json
import os
import subprocess
import tempfile
from pathlib import Path

import runpod


def _run(cmd):
    subprocess.run(cmd, check=True)


def handler(job):
    inp = job.get("input", job)
    prompt = inp.get("prompt", "")
    duration = int(inp.get("duration_seconds", 60))
    language = inp.get("language", "en")
    aspect = inp.get("aspect_ratio", "16:9")

    if not prompt:
        raise ValueError("prompt is required")
    if duration < 1:
        raise ValueError("duration_seconds must be positive")

    work = Path(tempfile.mkdtemp(prefix="anteneh-ai-"))
    request_file = work / "request.json"
    output_file = work / "final.mp4"
    request_file.write_text(json.dumps({
        "prompt": prompt,
        "duration_seconds": duration,
        "language": language,
        "aspect_ratio": aspect,
    }))

    runner = os.getenv("WORKER_CMD")
    if not runner:
        return {"status": "ready", "message": "GPU worker is connected; model runner is not configured yet."}

    _run(["/bin/sh", "-lc", f"{runner} {request_file} {output_file}"])
    return {"status": "completed", "output": str(output_file)}


runpod.serverless.start(handler)
