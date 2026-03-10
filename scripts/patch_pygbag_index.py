#!/usr/bin/env python3
"""Patch pygbag-generated index.html for reliable autostart behavior."""

from __future__ import annotations

import argparse
from pathlib import Path


def patch_index(index_path: Path) -> bool:
    if not index_path.exists():
        return False

    text = index_path.read_text(encoding="utf-8")
    original = text

    text = text.replace('data-autorun="0"', 'data-autorun="1"')
    text = text.replace("'autorun':0", "'autorun':1")
    text = text.replace('"autorun":0', '"autorun":1')

    if text != original:
        index_path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("index", help="Path to pygbag-generated index.html")
    args = parser.parse_args()

    index_path = Path(args.index).resolve()
    changed = patch_index(index_path)

    if changed:
        print(f"Patched autorun in: {index_path}")
    else:
        print(f"No autorun patch needed: {index_path}")


if __name__ == "__main__":
    main()
