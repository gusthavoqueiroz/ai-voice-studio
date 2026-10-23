
FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    runpod \
    chatterbox-tts

COPY handler.py /app/handler.py

CMD ["python", "-u", "handler.py"]
