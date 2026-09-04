"""One-cell Colab bootstrap for the Anteneh AI Studio Wan2.1 worker."""
import os, subprocess, sys, time
from pathlib import Path

STUDIO = Path("/content/anteneh-ai-studio")
WAN = Path("/content/Wan2.1")
MODEL = Path("/content/Wan2.1-T2V-1.3B")
WORK = Path("/content/anteneh-ai-jobs")

# Pull latest studio code when this bootstrap is run again.
if STUDIO.exists():
    subprocess.run(["git", "-C", str(STUDIO), "pull", "--ff-only"], check=False)
else:
    subprocess.run(["git", "clone", "https://github.com/antenehbenti1221/anteneh-ai-studio.git", str(STUDIO)], check=True)

assert (WAN / "generate.py").exists(), "Wan2.1 is missing"
assert (MODEL / "diffusion_pytorch_model.safetensors").exists(), "Wan2.1 model is missing"

WORK.mkdir(parents=True, exist_ok=True)
os.environ["VIDEO_MODEL"] = "Wan2.1-T2V-1.3B"
os.environ["WORK_DIR"] = str(WORK)
os.environ["VIDEO_COMMAND"] = f"{sys.executable} {STUDIO}/gpu-worker/wan21_adapter.py {{job}} {{output}}"
os.environ["VIDEO_RUNNER_CMD"] = f"{sys.executable} {STUDIO}/gpu-worker/runner.py {{job}} {{output}}"

subprocess.run("pkill -f 'uvicorn.*http_worker' || true", shell=True)
time.sleep(2)
log = open("/content/anteneh-worker.log", "w")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "gpu-worker.http_worker:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=STUDIO, env=os.environ.copy(), stdout=log, stderr=subprocess.STDOUT
)
time.sleep(5)

import requests
r = requests.get("http://127.0.0.1:8000/health", timeout=15)
print("ANTENEH AI STUDIO WORKER READY")
print(r.json())
print("PID:", proc.pid)
print("VIDEO_COMMAND:", os.environ["VIDEO_COMMAND"])
