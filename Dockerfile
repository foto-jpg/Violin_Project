# syntax=docker/dockerfile:1.7
# HF Spaces (Docker SDK, port 7860) - one container:
# FastAPI serves the Next.js static export + /api, Audiveris (Java) + CREPE (CPU).

# ============ Stage 1: Next.js static export ============
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
# No lockfile in repo - use install (mirrors frontend/Dockerfile).
RUN npm install
COPY frontend/ ./
# Static export can't host the dynamic proxy route handler; on HF the API is
# same-origin via FastAPI, so the proxy isn't needed.
RUN rm -rf app/api
ENV NEXT_PUBLIC_HF=1 \
    NEXT_PUBLIC_API_BASE=/api
RUN npm run build          # -> /frontend/out

# ============ Stage 2: Audiveris distribution (public, proven build) ============
FROM toprock/audiveris:latest AS audiveris
# provides /audiveris-extract (Audiveris 5.x Java dist) + tessdata

# ============ Stage 3: runtime ============
# Pin bookworm (Debian 12) - it still ships openjdk-17, which the Audiveris
# build from toprock/audiveris was made for (trixie dropped JDK 17).
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    tesseract-ocr tesseract-ocr-eng tesseract-ocr-osd \
    poppler-utils libmagic1 \
    libfreetype6 fontconfig fonts-dejavu \
    libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Audiveris (Java OMR) + its tessdata, copied from the proven image
COPY --from=audiveris /audiveris-extract /opt/audiveris
COPY --from=audiveris /usr/share/tesseract-ocr/tessdata /opt/tessdata
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    TESSDATA_PREFIX=/opt/tessdata

# Non-root user (HF best practice: uid 1000)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"
WORKDIR /app

# Python deps
COPY --chown=user requirements-hf.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Backend code (+ CREPE checkpoint) and the static frontend
COPY --chown=user backend/ ./backend/
COPY --chown=user --from=frontend-builder /frontend/out ./static/

ENV DISABLE_GPU=1 \
    DISABLE_OEMER=1 \
    STATIC_DIR=/app/static \
    AUDIVERIS_BIN=/opt/audiveris/bin/Audiveris \
    CREPE_CHECKPOINT=/app/backend/checkpoints/crepe_violin.pt \
    DATA_DIR=/tmp/data \
    HF_HOME=/tmp/hf_cache \
    MAX_AUDIO_SECONDS=300 \
    OMP_NUM_THREADS=2 \
    MKL_NUM_THREADS=2 \
    PYTHONUNBUFFERED=1

EXPOSE 7860
WORKDIR /app/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
