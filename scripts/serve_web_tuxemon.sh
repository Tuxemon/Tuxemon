#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/build/web"
PORT="${1:-8000}"

if [ ! -d "$OUT_DIR" ]; then
  echo "No browser build found at $OUT_DIR"
  echo "Run: scripts/build_web_tuxemon.sh"
  exit 1
fi

cd "$OUT_DIR"
python -m http.server "$PORT" --bind 0.0.0.0
