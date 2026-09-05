"""Wan2.1 T2V-1.3B launcher for the Lightning T4 worker."""
import json
import os
import subprocess
import sys
from pathlib import Path

WAN_HOME = Path(os.getenv("WAN_HOME", "/opt/Wan2.1"))
CKPT_DIR = os.getenv("WAN_CKPT_DIR", "/models/Wan2.1-T2V-1.3B")

SIZES = {"16:9": "832*480", "9:16": "480*832"}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_wan.py request.json output.mp4")
    request = json.loads(Path(sys.argv[1]).read_text())
    output = Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    size = SIZES.get(request.get("aspect_ratio", "16:9"), "832*480")
    test = bool(request.get("test", False))
    cmd = [
        sys.executable, str(WAN_HOME / "generate.py"),
        "--task", "t2v-1.3B", "--size", size,
        "--frame_num", "17" if test else "81",
        "--sample_steps", "25" if test else "50",
        "--sample_shift", "8", "--sample_guide_scale", "6",
        "--ckpt_dir", CKPT_DIR,
        "--offload_model", "True", "--t5_cpu",
        "--prompt", request["prompt"], "--save_file", str(output),
    ]
    subprocess.run(cmd, cwd=WAN_HOME, check=True)
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("Wan2.1 completed without producing a valid MP4")


if __name__ == "__main__":
    main()
