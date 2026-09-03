import os
import subprocess
import tempfile
from pathlib import Path


def _run(cmd):
    subprocess.run(cmd, check=True)


def handler(job):
    """RunPod-style handler boundary.

    The first production adapter intentionally accepts a worker command instead
    of embedding provider-specific APIs in the web application. Set WORKER_CMD
    in the GPU container to the model runner used by the deployment.
    """
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
    request_file.write_text(
        __import__("json").dumps({
            "prompt": prompt,
            "duration_seconds": duration,
            "language": language,
            "aspect_ratio": aspect,
        })
    )

    runner = os.getenv("WORKER_CMD")
    if not runner:
        return {
            "status": "configured",
            "message": "GPU worker is ready; set WORKER_CMD to the installed open-model runner.",
            "request_file": str(request_file),
        }

    _run(["/bin/sh", "-lc", f"{runner} {request_file} {work / 'final.mp4'}"])
    return {"status": "completed", "output": str(work / "final.mp4")}


# RunPod imports this symbol when deployed with its serverless handler protocol.
try:
    import runpod
    runpod.serverless.start({"handler": handler})
except ImportError:
    if __name__ == "__main__":
        print("Install runpod in the GPU image to run this handler.")
