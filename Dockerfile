FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime

WORKDIR /app

# Instalar ferramentas necessárias para compilar dependências
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    gcc \
    g++ \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Instalar bibliotecas Python
RUN pip install --no-cache-dir \
    runpod \
    chatterbox-tts \
    requests \
    boto3

COPY handler.py /app/handler.py

CMD ["python", "-u", "handler.py"]