# Remote GPU Worker

Fast path: keep the web app lightweight and send inference to a CUDA host.

## Wan2.2 TI2V-5B

The official Wan2.2 project documents TI2V-5B for text-to-video and image-to-video at 720p. Its documented single-GPU setup can run with 24GB VRAM using model offloading.

Example:

```bash
python generate.py --task ti2v-5B --size 1280*704 \
  --ckpt_dir ./Wan2.2-TI2V-5B \
  --offload_model True --convert_model_dtype --t5_cpu \
  --prompt "$PROMPT"
```

If an input image is supplied, pass `--image PATH` for image-to-video.

The worker should keep model weights cached on the GPU host; do not download weights for every job.
