"""Piper TTS adapter for the remote GPU/CPU worker."""
import os
import subprocess
from pathlib import Path

PIPER_BIN = os.getenv("PIPER_BIN", "piper")
PIPER_MODEL = os.getenv("PIPER_MODEL", "en_US-lessac-medium")


def synthesize(text: str, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [PIPER_BIN, "--model", PIPER_MODEL, "--output_file", str(output)],
        input=text.encode("utf-8"), check=True,
    )
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("Piper did not produce audio")
    return output
