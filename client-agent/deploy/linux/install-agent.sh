#!/usr/bin/env bash
set -euo pipefail

BIN_PATH="${1:-./dist/linux/loginuv-agent}"
CFG_PATH="${2:-./config/agent.example.json}"
INSTALL_DIR="${3:-/opt/loginuv}"

if [[ ! -f "$BIN_PATH" ]]; then
  echo "Binary not found: $BIN_PATH" >&2
  exit 1
fi
if [[ ! -f "$CFG_PATH" ]]; then
  echo "Config not found: $CFG_PATH" >&2
  exit 1
fi

sudo mkdir -p "$INSTALL_DIR"
sudo cp "$BIN_PATH" "$INSTALL_DIR/loginuv-agent"
sudo cp "$CFG_PATH" "$INSTALL_DIR/agent.json"
sudo chmod +x "$INSTALL_DIR/loginuv-agent"

echo "Installed files in $INSTALL_DIR"
echo "Run manually for demo: $INSTALL_DIR/loginuv-agent"
echo "Note: systemd service mode is pending in agent code."
