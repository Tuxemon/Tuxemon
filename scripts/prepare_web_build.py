#!/usr/bin/env python3
"""Prepare temporary web app folder for pygbag build.

- recreates ./web from source files
- copies run_tuxemon.py as web/main.py
- copies tuxemon/, mods/, requirements.txt
- removes unsupported audio formats recursively
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

UNSUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".m4a",
    ".aac",
    ".wma",
    ".aiff",
    ".alac",
}


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def remove_unsupported_audio(root: Path) -> int:
    removed = 0
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in UNSUPPORTED_AUDIO_EXTENSIONS:
            path.unlink()
            removed += 1
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    web_dir = root / "web"

    if web_dir.exists():
        shutil.rmtree(web_dir)
    web_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(root / "run_tuxemon.py", web_dir / "main.py")
    copy_tree(root / "tuxemon", web_dir / "tuxemon")
    copy_tree(root / "mods", web_dir / "mods")
    shutil.copy2(root / "requirements.txt", web_dir / "requirements.txt")

    removed = remove_unsupported_audio(web_dir / "mods")
    print(f"Prepared web app folder: {web_dir}")
    print(f"Removed unsupported audio files: {removed}")


if __name__ == "__main__":
    main()
