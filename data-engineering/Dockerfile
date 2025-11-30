FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    OMP_THREAD_LIMIT=1

# System deps: Tesseract OCR (+ eng), SSL certs, and common headless libs
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-eng \
      ca-certificates \
      libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# App code
COPY main.py /app/main.py

# Drop privileges
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Default entrypoint (ECS can override with "command")
ENTRYPOINT ["python", "-u", "/app/main.py"]
