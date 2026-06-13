#!/usr/bin/env bash
# Start all services in dev mode (hot-reload enabled for backend).
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Starting OMR Demo..."
echo "  Frontend : http://localhost:3100"
echo "  Backend  : http://localhost:8300"
echo ""

docker compose up
