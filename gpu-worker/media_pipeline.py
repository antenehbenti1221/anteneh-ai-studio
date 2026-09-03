"""End-to-end media assembly primitives for the remote GPU worker."""
import os
import subprocess
from pathlib import Path

FFMPEG = os.getenv("FFMPEG", "ffmpeg")


def mux_video(video: Path, voice: Path, captions: Path | None, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [FFMPEG, "-y", "-i", str(video), "-i", str(voice), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest"]
    if captions:
        # SRT is converted to a subtitle stream rather than burning text into video.
        cmd += ["-i", str(captions), "-map", "2:0", "-c:s", "mov_text"]
    cmd += [str(output)]
    subprocess.run(cmd, check=True)
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("FFmpeg did not produce a valid output MP4")
    return output


def probe(path: Path) -> dict:
    result = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    return {"path": str(path), "bytes": path.stat().st_size if path.exists() else 0, "probe_ok": result.returncode == 1}
