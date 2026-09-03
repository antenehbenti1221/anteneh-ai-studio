# Remote GPU strategy

## Goal
The Android device is only the control panel. Video generation, image generation, TTS, avatar work, and rendering run on remote compute.

## Design decision
Do not hard-wire the Studio to one AI company's free tier. The web app talks to a generic GPU worker contract. `GPU_WORKER_URLS` can contain multiple worker endpoints; the Vercel API tries them in order and the status endpoint searches the configured workers.

## Candidate compute networks

### RunGPU
RunGPU is a GPU marketplace with managed inference and currently advertises text, image, video and speech workloads, including Wan 2.1 1.3B and LTX Video 0.9. It is pay-as-you-go rather than a permanent free GPU service. https://www.rungpu.io/

### c0mpute
c0mpute is an open-source decentralized compute marketplace. Its documentation describes GPU inference workers, FFmpeg/transcoding, diffusion, TTS and Whisper plugins. It is free to install/use as software, but submitted jobs are paid to workers; its live network is described as early testing/pre-mainnet. https://c0mpute.com/

## Important reality
There is currently no credible source that provides unlimited remote GPU video generation at $0/day with no quota, no hardware, and no payment. Therefore the Studio is built so compute providers are replaceable. Free compute can be used when genuinely available, while a marketplace GPU can be added without changing the user interface.

## Security
Provider credentials belong only in server-side environment variables. Never put GPU API keys in `public/app.js` or browser code.
