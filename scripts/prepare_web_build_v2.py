#!/usr/bin/env python3
"""Prepare temporary web app folder for pygbag build (v2, robust)."""

from __future__ import annotations

import argparse
import os
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


def find_unsupported_audio(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in UNSUPPORTED_AUDIO_EXTENSIONS
    ]


def robust_unlink(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except PermissionError:
        try:
            os.chmod(path, 0o666)
            path.unlink()
            return True
        except Exception:
            return False
    except Exception:
        return False


def remove_unsupported_audio(root: Path) -> tuple[int, list[Path]]:
    removed = 0
    failed: list[Path] = []
    for path in find_unsupported_audio(root):
        if robust_unlink(path):
            removed += 1
        else:
            failed.append(path)
    return removed, failed


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

    mods_dir = web_dir / "mods"
    result = remove_unsupported_audio(mods_dir)
    if isinstance(result, tuple):
        removed = int(result[0])
        failed = list(result[1])
    else:
        # ultra-defensive compatibility, shouldn't happen in v2
        removed = int(result)
        failed = []

    remaining = find_unsupported_audio(mods_dir)

    print(f"Prepared web app folder: {web_dir}")
    print(f"Removed unsupported audio files: {removed}")

    if failed or remaining:
        print("ERROR: Unsupported audio files still present after cleanup:")
        for path in sorted(set(failed + remaining)):
            print(f" - {path}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
