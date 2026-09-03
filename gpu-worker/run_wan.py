"""Concrete Wan2.2 TI2V-5B launcher for the remote GPU container.

The official Wan repository is mounted/cloned at WAN_HOME. This wrapper maps our
normalized job to Wan's generate.py CLI without putting model/vendor logic in
the browser or control plane.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

WAN_HOME = Path(os.getenv("WAN_HOME", "/opt/Wan2.2"))
CKPT_DIR = os.getenv("WAN_CKPT_DIR", "/models/Wan2.2-TI2V-5B")

SIZES = {
    "16:9": "1280*704",
    "9:16": "704*1280",
}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_wan.py request.json output.mp4")
    request = json.loads(Path(sys.argv[1]).read_text())
    output = Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    aspect = request.get("aspect_ratio", "16:9")
    size = SIZES.get(aspect, "1280*704")
    cmd = [
        sys.executable,
        str(WAN_HOME / "generate.py"),
        "--task", "ti2v-5B",
        "--size", size,
        "--ckpt_dir", CKPT_DIR,
        "--offload_model", "True",
        "--convert_model_dtype",
        "--t5_cpu",
        "--prompt", request["prompt"],
    ]
    image = request.get("image")
    if image:
        cmd += ["--image", image]
    subprocess.run(cmd, cwd=WAN_HOME, check=True)
    candidates = sorted(WAN_HOME.glob("**/*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError("Wan completed without producing an MP4")
    candidates[0].replace(output)
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("Generated MP4 is missing or empty")


if __name__ == "__main__":
    main()
