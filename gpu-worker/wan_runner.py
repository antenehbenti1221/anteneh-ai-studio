"""Concrete Wan2.2 TI2V-5B command adapter.

Uses the official Wan2.2 generate.py CLI on the remote GPU host. The control
plane stays provider-independent.
"""
import os
import subprocess
from pathlib import Path

WAN_ROOT = Path(os.getenv("WAN_ROOT", "/opt/Wan2.2"))
WAN_CKPT = Path(os.getenv("WAN_CKPT", "/models/Wan2.2-TI2V-5B"))
WAN_PYTHON = os.getenv("WAN_PYTHON", "python")
SIZES = {"16:9": "1280*704", "9:16": "704*1280", "1:1": "704*704"}


def generate(prompt: str, output_dir: Path, aspect_ratio: str = "16:9", image: Path | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    size = SIZES.get(aspect_ratio, SIZES["16:9"])
    out = output_dir / "wan-output"
    cmd = [WAN_PYTHON, str(WAN_ROOT / "generate.py"), "--task", "ti2v-5B",
           "--size", size, "--ckpt_dir", str(WAN_CKPT),
           "--offload_model", "True", "--convert_model_dtype", "--t5_cpu"]
    if image:
        cmd += ["--image", str(image)]
    cmd += ["--prompt", prompt, "--save_dir", str(out)]
    subprocess.run(cmd, cwd=WAN_ROOT, check=True)
    videos = sorted(out.rglob("*.mp4"))
    if not videos:
        raise RuntimeError("Wan completed without producing an MP4")
    return videos[-1]
