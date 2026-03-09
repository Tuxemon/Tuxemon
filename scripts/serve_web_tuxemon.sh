#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/build/web"
PORT="${1:-8000}"

if command -v py >/dev/null 2>&1; then
  PY_CMD="py"
elif command -v python >/dev/null 2>&1; then
  PY_CMD="python"
elif command -v python3 >/dev/null 2>&1; then
  PY_CMD="python3"
else
  echo "No Python interpreter found (py/python/python3)."
  exit 1
fi

if [ ! -d "$OUT_DIR" ]; then
  echo "No browser build found at $OUT_DIR"
  echo "Run: scripts/build_web_tuxemon.sh"
  exit 1
fi

cd "$OUT_DIR"
"$PY_CMD" -m http.server "$PORT" --bind 0.0.0.0
