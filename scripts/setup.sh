#!/usr/bin/env bash
# One-shot setup: build all Docker images and verify GPU access.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== OMR Demo Setup ==="

# 1. Prerequisites
command -v docker  >/dev/null 2>&1 || { echo "ERROR: docker not found"; exit 1; }
command -v nvidia-smi >/dev/null 2>&1 || echo "WARNING: nvidia-smi not found - GPU features may not work"

# 2. Create data directories
mkdir -p data/uploads data/results data/logs data/samples

# 3. Build Audiveris image (downloads from GitHub inside Docker)
echo ""
echo "--- Building Audiveris image (may take a few minutes to download) ---"
docker compose --profile build-only build audiveris

# 4. Build backend image (downloads oemer + onnxruntime-gpu inside Docker)
echo ""
echo "--- Building backend image (downloads oemer + onnxruntime-gpu) ---"
docker compose build backend

# 5. Build frontend image (downloads npm packages inside Docker)
echo ""
echo "--- Building frontend image ---"
docker compose build frontend

# 6. Smoke-test: GPU visible inside backend container
echo ""
echo "--- GPU check inside backend container ---"
docker compose run --rm backend python -c "
import pynvml
try:
    pynvml.nvmlInit()
    count = pynvml.nvmlDeviceGetCount()
    print(f'Detected {count} GPU(s)')
    for i in range(count):
        h = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(h)
        print(f'  GPU {i}: {name if isinstance(name, str) else name.decode()}')
except Exception as e:
    print(f'GPU not available: {e} (CPU fallback will be used)')
"

# 7. Smoke-test: oemer CLI available
echo ""
echo "--- oemer availability check ---"
docker compose run --rm backend sh -c "
oemer --help > /dev/null 2>&1 && echo 'oemer: OK' || echo 'oemer: NOT FOUND'
"

# 8. Smoke-test: onnxruntime CUDAExecutionProvider
echo ""
echo "--- onnxruntime CUDA check ---"
docker compose run --rm backend python -c "
import onnxruntime as ort
providers = ort.get_available_providers()
if 'CUDAExecutionProvider' in providers:
    print('onnxruntime CUDAExecutionProvider: OK')
else:
    print(f'WARNING: CUDAExecutionProvider missing. Available: {providers}')
"

echo ""
echo "=== Setup complete. Run: ./scripts/start_dev.sh ==="
