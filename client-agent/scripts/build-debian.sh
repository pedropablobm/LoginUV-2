#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${1:-dist/linux}"

mkdir -p "$PROJECT_DIR/$OUTPUT_DIR"

cd "$PROJECT_DIR"
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w" -o "$OUTPUT_DIR/loginuv-agent" ./cmd/agent

echo "Linux build generated at $OUTPUT_DIR/loginuv-agent"
