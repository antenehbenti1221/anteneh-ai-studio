#!/usr/bin/env bash
set -euo pipefail

: "${WAN_HOME:=/opt/Wan2.2}"
: "${WAN_CKPT_DIR:=/models/Wan2.2-TI2V-5B}"

if [ ! -d "$WAN_HOME/.git" ]; then
  git clone --depth 1 https://github.com/Wan-Video/Wan2.2.git "$WAN_HOME"
fi

python -m pip install --upgrade pip
python -m pip install -r "$WAN_HOME/requirements.txt"
python -m pip install runpod

echo "Wan2.2 worker ready. Model weights must be mounted/downloaded at: $WAN_CKPT_DIR"
