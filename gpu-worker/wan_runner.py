"""Concrete Wan2.2 TI2V-5B command adapter.

The GPU image must contain the official Wan2.2 repository and downloaded
checkpoint. This adapter deliberately invokes the official generate.py CLI so
model updates remain isolated from the control plane.
"""
import os
import shlex
import subprocess
from pathlib import Path

WAN_ROOT = Path(os.getenv("WAN_ROOT", "/opt/Wan2.2"))
WAN_CKPT = Path(os.getenv("WAN_CKPT", "/models/Wan2.2-TI2V-5B"))
WAN_PYTHON = os.getenv("WAN_PYTHON", "python")

SIZES = {"16:9": "1280*704", "9:16": "704*1280", "1:1": "704*704"}


def generate(prompt: str, output_dir: Path, aspect_ratio: str = "16:9") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    size = SIZES.get(aspect_ratio, SIZES["16:9"])
    out = output_dir / "wan-output"
    cmd = [
        WAN_PYTHON, str(WAN_ROOT / "generate.py"),
        "--task", "ti2v-5B",
        "--size", size,
        "--ckpt_dir", str(WAN_CKPT),
        "--offload_model", "True",
        "--convert_model_dtype",
        "--t5_cpu",
        "--prompt", prompt,
        "--save_dir", str(out),
    ]
    subprocess.run(cmd, cwd=WAN_ROOT, check=True)
    videos = sorted(out.rglob("*.mp4"))
    if not videos:
        raise RuntimeError("Wan completed without producing an MP4")
    return videos[-1]


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("prompt")
    p.add_argument("output_dir")
    p.add_argument("--aspect-ratio", default="16:9")
    a = p.parse_args()
    print(generate(a.prompt, Path(a.output_dir), a.aspect_ratio))
