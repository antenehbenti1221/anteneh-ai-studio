# Remote GPU setup

The Studio is provider-independent. The web app only needs an HTTPS worker endpoint; the worker runs the open-weight media stack.

## Required worker environment

- `VIDEO_MODEL=Wan2.2-TI2V-5B` (default)
- `VIDEO_COMMAND=...` command that produces `{output}` from `{prompt_file}` and accepts `{seconds}`, `{aspect_ratio}`, `{language}`, `{voice}`, `{style}`
- `WORK_DIR=/tmp/anteneh-ai-jobs`
- `GPU_WORKER_TOKEN=<long-random-secret>`

## Vercel environment

- `GPU_WORKER_URL=https://<your-worker>/`
- `GPU_WORKER_TOKEN=<same-secret>`

Never put the token in `public/app.js` or other browser-delivered files.

## Open model baseline

Wan2.2 TI2V-5B supports text-to-video and image-to-video at 720p and can fit on a 24 GB GPU with model/CPU offloading. Larger Wan2.2 14B variants need much more VRAM.

## Production pipeline target

1. Prompt → scene plan
2. Visual generation (video/image/animation/avatar as selected)
3. TTS voice-over
4. Whisper/faster-whisper captions
5. Music and SFX mix
6. FFmpeg assembly/export
7. Final MP4 URL

The worker can be moved between GPU hosts without changing the Studio UI or API contract.
