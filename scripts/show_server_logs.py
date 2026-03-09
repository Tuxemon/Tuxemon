#!/usr/bin/env python3
"""Show recent lines from the latest Tuxemon server log file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tuxemon.constants import paths


def _latest_log_file(log_dir: Path) -> Path | None:
    files = [entry for entry in log_dir.iterdir() if entry.is_file()]
    if not files:
        return None
    return max(files, key=lambda item: item.stat().st_mtime)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print recent lines from the latest server log file.",
    )
    parser.add_argument(
        "-n",
        "--lines",
        type=int,
        default=100,
        help="Number of lines to print (default: 100).",
    )
    args = parser.parse_args()

    log_dir = paths.USER_STORAGE_DIR / "logs"
    if not log_dir.exists():
        print(f"No log directory found at: {log_dir}")
        return 1

    latest = _latest_log_file(log_dir)
    if latest is None:
        print(f"No log files found in: {log_dir}")
        return 1

    lines = latest.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = lines[-max(args.lines, 0):]

    print(f"Showing {len(tail)} lines from: {latest}")
    for line in tail:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
