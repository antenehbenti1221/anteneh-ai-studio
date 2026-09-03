"""Run Wan2.2 TI2V-5B on a remote CUDA worker.

This wrapper intentionally delegates model inference to the official Wan2.2
repository. It validates inputs, constructs the documented command, and checks
that inference produced a real MP4. The control plane never needs GPU access.
"""
import os
import shlex
import subprocess
from pathlib import Path

MODEL_DIR = Path(os.getenv("WAN_MODEL_DIR", "/models/Wan2.2-TI2V-5B"))
WAN_DIR = Path(os.getenv("WAN_DIR", "/opt/Wan2.2"))

SIZES = {"16:9": "1280*704", "9:16": "704*1280", "1:1": "704*704"}


def run(prompt: str, output_dir: str, image: str | None = None,
        aspect_ratio: str = "16:9") -> Path:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if aspect_ratio not in SIZES:
        raise ValueError(f"unsupported aspect ratio: {aspect_ratio}")
    if not MODEL_DIR.exists():
        raise RuntimeError(f"Wan model not mounted: {MODEL_DIR}")
    if not WAN_DIR.exists():
        raise RuntimeError(f"Wan2.2 source not mounted: {WAN_DIR}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    cmd = ["python", "generate.py", "--task", "ti2v-5B",
           "--size", SIZES[aspect_ratio], "--ckpt_dir", str(MODEL_DIR),
           "--offload_model", "True", "--convert_model_dtype", "--t5_cpu",
           "--prompt", prompt]
    if image:
        cmd += ["--image", image]

    subprocess.run(cmd, cwd=WAN_DIR, check=True)
    mp4s = sorted(out.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mp4s:
        raise RuntimeError("Wan inference completed but produced no MP4")
    return mp4s[0]


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("prompt")
    p.add_argument("--output-dir", default="/outputs")
    p.add_argument("--image")
    p.add_argument("--aspect-ratio", default="16:9", choices=SIZES)
    args = p.parse_args()
    print(run(args.prompt, args.output_dir, args.image, args.aspect_ratio))
