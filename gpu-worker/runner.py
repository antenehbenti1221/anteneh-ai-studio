"""Reference production runner for the remote GPU worker.

This keeps model-specific commands outside the HTTP API. Set VIDEO_COMMAND to
an installed command template using {prompt_file}, {output}, {seconds}, and
{aspect_ratio}. A deployment can replace this with a Wan/ComfyUI/Diffusers
runner without changing the web application.
"""
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path


def main(job_path: str, output_path: str) -> int:
    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    command = os.getenv("VIDEO_COMMAND")
    if not command:
        print("VIDEO_COMMAND is not configured", file=sys.stderr)
        return 78

    prompt_file = Path(job_path).with_name("prompt.txt")
    prompt_file.write_text(job["prompt"], encoding="utf-8")
    values = {
        "prompt_file": shlex.quote(str(prompt_file)),
        "output": shlex.quote(output_path),
        "seconds": str(job["duration_seconds"]),
        "aspect_ratio": shlex.quote(job.get("aspect_ratio", "16:9")),
        "language": shlex.quote(job.get("language", "en")),
        "voice": shlex.quote(job.get("voice", "default")),
        "style": shlex.quote(job.get("style", "educational")),
    }
    subprocess.run(command.format(**values), shell=True, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
