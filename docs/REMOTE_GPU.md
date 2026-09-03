# Remote GPU integration

The studio is designed so the browser never runs video models locally.

## Worker contract
The router sends a normalized VideoJob to a remote GPU worker. The worker can host open-source models such as Wan-family video generation, an open image model, Piper/another open TTS model, and FFmpeg.

## Required worker stages
1. Script/storyboard generation
2. Image/video scene generation
3. Optional avatar animation
4. Voice-over generation
5. Caption generation
6. Audio mixing and music/SFX
7. FFmpeg assembly
8. MP4 upload and job completion

## Provider independence
The router communicates only with the worker contract. GPU infrastructure can therefore be changed without changing the web UI.

No GPU credentials are stored in the frontend.
