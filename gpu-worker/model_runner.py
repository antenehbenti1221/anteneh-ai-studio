"""Model runner boundary for real remote-GPU inference.

The worker accepts an explicit MODEL_ID and delegates inference to a local
open-model runtime installed inside the GPU container. No consumer API key is
required by this interface.
"""
import os
from pathlib import Path
from typing import Any

MODEL_ID = os.getenv("VIDEO_MODEL_ID", "Wan-AI/Wan2.2-TI2V-5B")

class ModelRunner:
    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id
        self._pipeline: Any = None

    def load(self) -> None:
        # Keep imports lazy: CPU control-plane deployments don't need CUDA.
        try:
            import torch  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install the GPU worker dependencies first") from exc
        if not torch.cuda.is_available():
            raise RuntimeError("A CUDA GPU is required for model inference")
        # Concrete Wan pipeline loading is intentionally isolated here so the
        # rest of the system remains provider/model independent.
        raise NotImplementedError(
            f"Install and initialize the selected open model runtime for {self.model_id}"
        )

    def generate(self, prompt: str, output_dir: Path, seconds: int, aspect_ratio: str) -> Path:
        self.load()
        raise NotImplementedError
