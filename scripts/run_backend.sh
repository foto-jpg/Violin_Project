#!/usr/bin/env bash
# Run FastAPI backend on the host using the venv (gives direct GPU access).
# Pinned to GPU 0 (RTX 3070 Ti) - change CUDA_VISIBLE_DEVICES to use the 5090.
set -euo pipefail

cd "$(dirname "$0")/../backend"

if [[ ! -d venv ]]; then
  echo "venv missing - run: python3.11 -m venv venv && venv/bin/pip install -r requirements.txt"
  exit 1
fi

# PyTorch defaults to FASTEST_FIRST ordering - force PCI_BUS_ID so device
# indices match `nvidia-smi`. Then VISIBLE=0 reliably pins to GPU 0 = 3070 Ti.
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0
export PYTHONPATH=.
# Put venv binaries (oemer, etc.) on PATH so subprocess calls find them
export PATH="$(pwd)/venv/bin:$PATH"

# Add CUDA / cuDNN libs from the nvidia-* pip packages so onnxruntime-gpu
# can dlopen them at runtime (host has CUDA driver but no cuDNN system-wide).
NVIDIA_LIBS=$(venv/bin/python -c "import os, glob, nvidia; root=os.path.dirname(nvidia.__file__); print(':'.join(sorted(set(os.path.dirname(p) for p in glob.glob(f'{root}/*/lib/*.so*')))))")
export LD_LIBRARY_PATH="${NVIDIA_LIBS}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# Use the fine-tuned CREPE checkpoint for audio pitch tracking if it exists.
CKPT="$(pwd)/checkpoints/crepe_violin.pt"
[[ -f "$CKPT" ]] && export CREPE_CHECKPOINT="$CKPT" && echo "[run_backend] CREPE_CHECKPOINT=$CKPT"

# Hot-reload by default (manual dev). The systemd service sets UVICORN_RELOAD=0
# so the always-on server doesn't spawn a file-watcher.
RELOAD_FLAG=""
[[ "${UVICORN_RELOAD:-1}" == "1" ]] && RELOAD_FLAG="--reload"

exec ./venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8300 \
    ${RELOAD_FLAG}
