# Build plan

## Phase 1 — Control plane
- Web creator UI
- Job API
- Provider-independent worker contract
- Status polling

## Phase 2 — Remote GPU worker
- Containerized worker
- Open video model adapter (Wan family)
- Open image model adapter
- Open TTS adapter
- Caption/transcription adapter
- FFmpeg assembler

## Phase 3 — Production modes
- <=1 minute
- 3–5 minutes
- 10+ minutes
- Text, image, avatar and mixed inputs
- 16:9, 9:16 and 1:1
- English and Amharic workflows

## Phase 4 — Reliability
- Retry failed scenes
- Resume jobs
- GPU queue
- Storage cleanup
- Quality checks
- Automatic final MP4 export

The Book Store is intentionally a separate project and is not modified by this system.
