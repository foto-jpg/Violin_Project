FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libmagic1 \
        poppler-utils \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Docker CLI only (no daemon) - needed to call `docker run audiveris`
COPY --from=docker:24-cli /usr/local/bin/docker /usr/local/bin/docker

WORKDIR /app

COPY requirements.txt .

# Install deps; then force onnxruntime-gpu over any CPU onnxruntime oemer pulls in
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y onnxruntime || true && \
    pip install --no-cache-dir "onnxruntime-gpu>=1.17.0" --force-reinstall

COPY app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
