#!/usr/bin/env bash
set -euo pipefail

: "${WAN_HOME:=/opt/Wan2.1}"
: "${WAN_CKPT_DIR:=/models/Wan2.1-T2V-1.3B}"

if [ ! -d "$WAN_HOME/.git" ]; then
  git clone --depth 1 https://github.com/Wan-Video/Wan2.1.git "$WAN_HOME"
fi

python -m pip install --upgrade pip
python -m pip install "numpy<2" ftfy dashscope einops imageio imageio-ffmpeg tqdm safetensors transformers tokenizers accelerate easydict opencv-python pillow fastapi "uvicorn[standard]" pydantic huggingface_hub
python -m pip install runpod

echo "Wan2.1 T2V-1.3B worker ready. Model weights: $WAN_CKPT_DIR"
