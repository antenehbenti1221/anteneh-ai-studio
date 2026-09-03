"""Concrete remote-GPU model runner boundary.

The container hosts open models locally; the control plane never depends on a
commercial AI inference API. Wan2.2 is the default video model identifier.
"""
import os
import subprocess
from pathlib import Path

MODEL_ID = os.getenv("VIDEO_MODEL_ID", "Wan-AI/Wan2.2-TI2V-5B")


def generate(prompt: str, output_dir: Path, seconds: int, aspect_ratio: str) -> Path:
    """Run the installed model command and verify that it produced an MP4.

    WAN_RUNNER_CMD is deliberately injected by the GPU deployment. The command
    receives VIDEO_PROMPT, VIDEO_DURATION, VIDEO_ASPECT and VIDEO_OUTPUT in its
    environment, allowing the model runtime to be upgraded independently.
    """
    if not prompt.strip():
        raise ValueError("prompt is required")
    if seconds < 1:
        raise ValueError("seconds must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "visual.mp4"
    command = os.getenv("WAN_RUNNER_CMD")
    if not command:
        raise RuntimeError(f"WAN_RUNNER_CMD is not configured for {MODEL_ID}")

    env = os.environ.copy()
    env.update({
        "VIDEO_MODEL_ID": MODEL_ID,
        "VIDEO_PROMPT": prompt,
        "VIDEO_DURATION": str(seconds),
        "VIDEO_ASPECT": aspect_ratio,
        "VIDEO_OUTPUT": str(output),
    })
    subprocess.run(["/bin/sh", "-lc", command], env=env, check=True)

    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("Model runner did not produce a non-empty MP4")
    return output
