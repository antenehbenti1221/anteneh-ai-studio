# Production pipeline

The GPU worker is intentionally provider-independent. A remote host should run this service and expose HTTPS to the Vercel API.

Required capabilities:
- open-weight video generation (Wan2.2 TI2V-5B is the default)
- TTS (Piper or another installed open model)
- captions (Whisper/faster-whisper)
- FFmpeg rendering
- persistent job/output storage

Set `VIDEO_RUNNER_CMD` to a command that receives `{job}` and `{output}` and writes the final MP4 to `{output}`.
