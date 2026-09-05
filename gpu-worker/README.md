# Anteneh AI Studio — GPU Worker

The supported free-GPU path is **Lightning AI T4 + Wan2.1 T2V-1.3B**.

Wan2.1's 1.3B T2V model is designed for 480P and is small enough for consumer GPUs; for low-VRAM operation the official guidance is to use model offloading and keep T5 on CPU. citeturn5search1turn2search2

## Lightning one-command setup

From a Lightning Studio terminal:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/antenehbenti1221/anteneh-ai-studio/main/lightning/auto_setup_wan21.sh)
```

The script automatically:

1. checks the NVIDIA GPU;
2. clones the official Wan2.1 repository;
3. creates an isolated Python environment;
4. installs compatible dependencies without requiring `flash_attn`;
5. verifies the Wan2.1 import;
6. downloads/resumes the public Wan2.1 T2V-1.3B model;
7. creates the asynchronous FastAPI worker;
8. exposes port 8000 through Lightning's port system;
9. generates a real smoke-test MP4; and
10. prints the public API URL and worker token location.

The smoke test intentionally uses a short 17-frame/25-step clip. Normal jobs use the official 81-frame/50-step 480P configuration.
