#!/usr/bin/env bash
set -euo pipefail

# Build the full Tuxemon pygame client for browsers via pygbag.
# Output is generated under build/web (html/wasm/assets).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_APP_DIR="$ROOT_DIR/web"
OUT_DIR="$ROOT_DIR/build/web"

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

mkdir -p "$OUT_DIR"

if ! "$PY_CMD" -c "import pygbag" >/dev/null 2>&1; then
  echo "Installing pygbag..."
  "$PY_CMD" -m pip install pygbag
fi

# Prepare a lean app folder for browser build.
rm -rf "$WEB_APP_DIR"
mkdir -p "$WEB_APP_DIR"
cp "$ROOT_DIR/run_tuxemon.py" "$WEB_APP_DIR/main.py"
cp -r "$ROOT_DIR/tuxemon" "$WEB_APP_DIR/tuxemon"
cp -r "$ROOT_DIR/mods" "$WEB_APP_DIR/mods"
cp "$ROOT_DIR/requirements.txt" "$WEB_APP_DIR/requirements.txt"

# pygbag rejects some common audio formats (e.g. mp3).
# Remove mp3 files from the temporary web app copy to keep build portable.
if [ -d "$WEB_APP_DIR/mods/tuxemon/music" ]; then
  find "$WEB_APP_DIR/mods/tuxemon/music" -type f -name "*.mp3" -delete
fi

# pygbag builds from an app root that contains main.py.
"$PY_CMD" -m pygbag --build --archive --ume_block 0 --app_name "Tuxemon" --disable-sound-format-error "$WEB_APP_DIR"

# Collect generated output in a predictable place.
if [ -d "$WEB_APP_DIR/build/web" ]; then
  rm -rf "$OUT_DIR"
  mkdir -p "$(dirname "$OUT_DIR")"
  mv "$WEB_APP_DIR/build/web" "$OUT_DIR"
fi

echo "Built browser package at: $OUT_DIR"
