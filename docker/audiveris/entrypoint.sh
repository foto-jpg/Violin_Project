#!/usr/bin/env bash
# Usage: /entrypoint.sh <input_file> <output_dir>
set -euo pipefail

INPUT="$1"
OUTPUT_DIR="$2"
mkdir -p "$OUTPUT_DIR"

exec /audiveris-extract/bin/Audiveris -batch -export -output "$OUTPUT_DIR" -- "$INPUT"
