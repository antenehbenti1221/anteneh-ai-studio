"""GPU-worker media assembly helpers.

FFmpeg performs deterministic assembly after AI inference: clips + narration +
captions are rendered into one MP4. Heavy inference remains in model_runner.
"""
import subprocess
from pathlib import Path


def assemble(clips: list[Path], audio: Path, output: Path, aspect_ratio: str = "16:9") -> Path:
    if not clips:
        raise ValueError("At least one generated clip is required")
    output.parent.mkdir(parents=True, exist_ok=True)
    concat = output.parent / "clips.txt"
    concat.write_text("\n".join(f"file '{p.resolve()}'" for p in clips), encoding="utf-8")
    vf = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2"
    if aspect_ratio == "9:16":
        vf = "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2"
    elif aspect_ratio == "1:1":
        vf = "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-i", str(audio), "-vf", vf, "-c:v", "libx264", "-c:a", "aac",
        "-shortest", str(output)
    ], check=True)
    return output
