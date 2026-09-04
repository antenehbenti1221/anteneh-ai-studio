# Free GPU lane — Kaggle

This lane keeps the existing Anteneh AI Studio architecture intact. It does **not** replace the control plane, pipeline, or worker contract.

## Why Kaggle instead of RunPod

Kaggle provides free GPU notebook access with a weekly quota (currently 30 hours or sometimes higher depending on demand/resources) and session limits. The quota is not an unlimited production service.

The Studio therefore treats Kaggle as an **on-demand render machine**, not as a permanent HTTP server.

## Important design rule

Do not expose a Kaggle notebook as a permanent public API endpoint. The notebook runs the same job manifest used by the existing GPU worker and returns the final MP4 as a notebook artifact.

## Existing integration reused

- `backend/gpu_router.py` — provider-independent job contract.
- `backend/pipeline.py` — existing production stages.
- `gpu-worker/run_wan.py` — existing Wan launcher and `request.json` format.
- `gpu-worker/media_pipeline.py` — existing FFmpeg media primitives.

No RunPod configuration is required for this free lane.

## Phone workflow

1. Open the Kaggle notebook in `free-gpu/kaggle_worker.ipynb`.
2. Turn on **GPU** in notebook settings.
3. Run the setup cells.
4. Provide a `request.json` containing `prompt`, `duration_seconds`, `language`, and `aspect_ratio`.
5. Run the render cell.
6. Download `final.mp4` to the Android phone.
7. Continue with the existing phone editing/publishing workflow.

For the first 3-minute trial, keep the 16:9 format and use the existing Amharic script/visual workflow. GPU rendering is optional for that trial; Microsoft Designer + CapCut remains the simplest $0 path.

## Reality check

Free GPU availability and quotas can change. The system is therefore finalized around a replaceable worker interface rather than a paid or permanently hosted GPU service.
