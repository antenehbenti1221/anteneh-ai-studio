"""Wan2.1 T2V-1.3B adapter for Anteneh AI Studio.

Called as: python wan21_adapter.py JOB_JSON OUTPUT_MP4
"""
import json
import subprocess
import sys
from pathlib import Path

WAN_ROOT = Path("/content/Wan2.1")
MODEL = Path("/content/Wan2.1-T2V-1.3B")
SIZES = {"16:9": "832*480", "9:16": "480*832", "1:1": "480*480"}


def main(job_path: str, output_path: str) -> int:
    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    size = SIZES.get(job.get("aspect_ratio", "16:9"), SIZES["16:9"])

    cmd = [
        sys.executable,
        str(WAN_ROOT / "generate.py"),
        "--task", "t2v-1.3B",
        "--size", size,
        "--ckpt_dir", str(MODEL),
        "--offload_model", "True",
        "--prompt", job["prompt"],
        "--save_file", str(output),
    ]
    print("Starting Wan2.1 T2V-1.3B")
    print("Prompt:", job["prompt"])
    print("Size:", size)
    print("Output:", output)
    subprocess.run(cmd, cwd=WAN_ROOT, check=True)
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("Wan2.1 completed without producing an MP4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
