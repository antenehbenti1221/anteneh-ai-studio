"""Provider-neutral orchestration for a real GPU deployment."""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass
class Job:
    prompt: str
    duration_seconds: int
    language: str = "en"
    aspect_ratio: str = "16:9"

class Stage(Protocol):
    async def run(self, job: Job, workdir: Path) -> Path: ...

class Pipeline:
    def __init__(self, script: Stage, visuals: Stage, voice: Stage, captions: Stage, render: Stage):
        self.stages = [script, visuals, voice, captions, render]

    async def run(self, job: Job, workdir: Path) -> Path:
        current = workdir
        for stage in self.stages:
            current = await stage.run(job, current)
        return current
