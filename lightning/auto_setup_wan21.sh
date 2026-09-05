#!/usr/bin/env bash
set -euo pipefail

# Anteneh AI Studio — Lightning T4 one-command setup
# Installs official Wan2.1 T2V-1.3B, starts the async API, exposes port 8000,
# and runs a small real MP4 smoke test. No Hugging Face token is required.

BASE="${HOME}/anteneh-ai"
WAN_HOME="${BASE}/Wan2.1"
MODEL_DIR="${BASE}/Wan2.1-T2V-1.3B"
API_DIR="${BASE}/api"
WORK_DIR="${BASE}/jobs"
PY="$(command -v python3.11 || command -v python3 || true)"

if [[ -z "${PY}" ]]; then
  echo "ERROR: Python 3.11/3.x not found."
  exit 1
fi

PY_MAJOR="$($PY -c 'import sys; print(sys.version_info.major)')"
PY_MINOR="$($PY -c 'import sys; print(sys.version_info.minor)')"
if (( PY_MAJOR == 3 && PY_MINOR >= 13 )); then
  if command -v python3.11 >/dev/null 2>&1; then PY="$(command -v python3.11)"; else
    echo "ERROR: Python 3.11 is required because Wan2.1 requires NumPy <2 and the current Python is ${PY_MAJOR}.${PY_MINOR}."
    exit 1
  fi
fi

mkdir -p "$BASE" "$API_DIR" "$WORK_DIR"

echo "[1/8] GPU"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

echo "[2/8] Wan2.1 source"
if [[ ! -f "$WAN_HOME/generate.py" ]]; then
  rm -rf "$WAN_HOME"
  git clone --depth 1 https://github.com/Wan-Video/Wan2.1.git "$WAN_HOME"
fi

# Use an isolated environment so Lightning's base Python remains untouched.
VENV="$BASE/.venv"
if [[ ! -x "$VENV/bin/python" ]]; then "$PY" -m venv "$VENV"; fi
PY="$VENV/bin/python"

export PIP_DISABLE_PIP_VERSION_CHECK=1
export HF_HUB_DOWNLOAD_TIMEOUT=60

echo "[3/8] Python dependencies"
"$PY" -m pip install -q --upgrade pip setuptools wheel
"$PY" -m pip install -q "numpy==1.26.4" ftfy dashscope einops imageio imageio-ffmpeg tqdm safetensors transformers tokenizers accelerate easydict opencv-python pillow huggingface_hub "fastapi>=0.115" "uvicorn[standard]>=0.30" "pydantic>=2"

# Reuse Lightning's CUDA-enabled torch when possible; install only if absent.
"$PY" - <<'PY'
import torch
print("TORCH", torch.__version__)
print("CUDA", torch.cuda.is_available())
if not torch.cuda.is_available():
    raise SystemExit("CUDA is not available in this Studio")
PY

export PYTHONPATH="$WAN_HOME${PYTHONPATH:+:$PYTHONPATH}"
"$PY" - <<'PY'
import numpy, ftfy, wan
print("NUMPY", numpy.__version__)
print("FTFY_OK")
print("WAN_IMPORT_OK")
PY

echo "[4/8] Wan2.1 T2V-1.3B model"
if [[ ! -f "$MODEL_DIR/Wan2.1_VAE.pth" || ! -f "$MODEL_DIR/models_t5_umt5-xxl-enc-bf16.pth" || ! -f "$MODEL_DIR/diffusion_pytorch_model.safetensors" ]]; then
  rm -rf "$MODEL_DIR.tmp"
  "$PY" - <<PY
from huggingface_hub import snapshot_download
snapshot_download("Wan-AI/Wan2.1-T2V-1.3B", local_dir="$MODEL_DIR.tmp", resume_download=True)
PY
  rm -rf "$MODEL_DIR"
  mv "$MODEL_DIR.tmp" "$MODEL_DIR"
fi

echo "[5/8] Creating runner"
cat > "$API_DIR/runner.py" <<'PY'
import json, os, subprocess, sys
from pathlib import Path
WAN_HOME = Path(os.environ["WAN_HOME"])
MODEL_DIR = Path(os.environ["WAN_CKPT_DIR"])

def main():
    if len(sys.argv) != 3: raise SystemExit("usage: runner.py job.json output.mp4")
    req = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2]); out.parent.mkdir(parents=True, exist_ok=True)
    aspect = req.get("aspect_ratio", "16:9")
    size = "832*480" if aspect == "16:9" else "480*832"
    # Small smoke-test jobs finish much faster; normal jobs use the official 81-frame/50-step setting.
    test = bool(req.get("test", False))
    frames = 17 if test else 81
    steps = 25 if test else 50
    cmd = [sys.executable, str(WAN_HOME / "generate.py"),
           "--task", "t2v-1.3B", "--size", size,
           "--frame_num", str(frames), "--sample_steps", str(steps),
           "--sample_shift", "8", "--sample_guide_scale", "6",
           "--ckpt_dir", str(MODEL_DIR), "--offload_model", "True", "--t5_cpu",
           "--prompt", req["prompt"], "--save_file", str(out)]
    subprocess.run(cmd, cwd=WAN_HOME, check=True)
    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError("Wan2.1 finished without a valid MP4")

if __name__ == "__main__": main()
PY

cat > "$API_DIR/server.py" <<'PY'
import asyncio, json, os, subprocess, sys, uuid
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(os.environ["WORK_DIR"]); ROOT.mkdir(parents=True, exist_ok=True)
RUNNER = Path(os.environ["RUNNER"])
TOKEN = os.environ.get("GPU_WORKER_TOKEN", "").strip()
app = FastAPI(title="Anteneh AI Studio GPU Worker", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Job(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    duration_seconds: int = Field(default=1, ge=1, le=3600)
    language: str = "en"
    aspect_ratio: str = "16:9"
    test: bool = False

def auth(a):
    if TOKEN and a != f"Bearer {TOKEN}": raise HTTPException(401, "Invalid worker token")

def status(folder, value, **extra):
    (folder/"status.json").write_text(json.dumps({"status": value, **extra}))

async def run(job_id):
    folder=ROOT/job_id; job=folder/"job.json"; out=folder/"final.mp4"
    status(folder,"running")
    log=folder/"generation.log"
    try:
        with log.open("w") as f:
            p=await asyncio.create_subprocess_exec(sys.executable,str(RUNNER),str(job),str(out),stdout=f,stderr=subprocess.STDOUT)
            code=await p.wait()
        if code==0 and out.exists() and out.stat().st_size>0: status(folder,"completed",size_bytes=out.stat().st_size)
        else: status(folder,"failed",exit_code=code,log_url=f"/jobs/{job_id}/log")
    except Exception as e: status(folder,"failed",error=str(e))

@app.get("/health")
def health(): return {"ok":True,"model":"Wan2.1-T2V-1.3B","gpu":"Tesla T4","runner_configured":True}

@app.post("/jobs")
async def create(job:Job, authorization:str|None=Header(default=None)):
    auth(authorization); jid=str(uuid.uuid4()); folder=ROOT/jid; folder.mkdir(); (folder/"job.json").write_text(job.model_dump_json()); status(folder,"queued"); asyncio.create_task(run(jid)); return {"job_id":jid,"status":"queued"}

@app.get("/jobs/{jid}")
def get_status(jid:str, authorization:str|None=Header(default=None)):
    auth(authorization); f=ROOT/jid/"status.json"
    if not f.exists(): raise HTTPException(404,"Job not found")
    d=json.loads(f.read_text()); d={"job_id":jid,**d}
    if d["status"]=="completed": d["video_url"]=f"/jobs/{jid}/video"
    return d

@app.get("/jobs/{jid}/video")
def video(jid:str, authorization:str|None=Header(default=None)):
    auth(authorization); f=ROOT/jid/"final.mp4"
    if not f.exists(): raise HTTPException(404,"Video not ready")
    return FileResponse(f,media_type="video/mp4",filename=f"anteneh-{jid}.mp4")

@app.get("/jobs/{jid}/log")
def log(jid:str, authorization:str|None=Header(default=None)):
    auth(authorization); f=ROOT/jid/"generation.log"
    if not f.exists(): raise HTTPException(404,"Log not ready")
    return FileResponse(f,media_type="text/plain")
PY

echo "[6/8] Starting API"
pkill -f 'anteneh-ai/api/server.py' 2>/dev/null || true
export WAN_HOME WAN_CKPT_DIR="$MODEL_DIR" WORK_DIR RUNNER="$API_DIR/runner.py"
export PYTHONPATH="$WAN_HOME${PYTHONPATH:+:$PYTHONPATH}"
export GPU_WORKER_TOKEN="$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(24))
PY
)"
printf '%s\n' "$GPU_WORKER_TOKEN" > "$BASE/worker_token.txt"
nohup "$PY" -m uvicorn server:app --host 0.0.0.0 --port 8000 > "$BASE/api.log" 2>&1 &
echo $! > "$BASE/api.pid"

for i in {1..60}; do
  if curl -fsS http://127.0.0.1:8000/health >/tmp/anteneh-health.json 2>/dev/null; then break; fi
  sleep 2
done
curl -fsS http://127.0.0.1:8000/health

echo "[7/8] Exposing port 8000"
"$PY" - <<'PY'
from lightning_sdk import Studio
s=Studio()
items=s.add_ports(8000)
print("PUBLIC_API_URL", items[0].urls[0])
PY

echo "[8/8] REAL smoke test"
JOB=$(curl -fsS -X POST http://127.0.0.1:8000/jobs -H "Authorization: Bearer $GPU_WORKER_TOKEN" -H 'Content-Type: application/json' -d '{"prompt":"A cinematic Ethiopian landscape at golden hour, gentle camera movement, realistic film look.","test":true,"duration_seconds":1}')
echo "$JOB"
JOB_ID=$(python -c 'import json,sys; print(json.loads(sys.argv[1])["job_id"])' "$JOB")
for i in {1..120}; do
  S=$(curl -fsS http://127.0.0.1:8000/jobs/$JOB_ID -H "Authorization: Bearer $GPU_WORKER_TOKEN")
  echo "$S"
  echo "$S" | grep -q '"status":"completed"' && break
  echo "$S" | grep -q '"status":"failed"' && { cat "$BASE/api.log"; cat "$WORK_DIR/$JOB_ID/generation.log"; exit 1; }
  sleep 5
done

echo "============================================================"
echo "ANTENEH AI STUDIO READY"
echo "API: use the PUBLIC_API_URL printed above"
echo "TOKEN: saved at $BASE/worker_token.txt"
echo "TEST JOB: $JOB_ID"
echo "VIDEO: /jobs/$JOB_ID/video"
echo "============================================================"
