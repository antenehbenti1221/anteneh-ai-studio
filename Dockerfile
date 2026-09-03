FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip ffmpeg git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN python3 -m pip install --no-cache-dir runpod
COPY handler.py ./
CMD ["python3", "handler.py"]
