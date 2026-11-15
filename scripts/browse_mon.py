#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0

import re
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent

# Input: old frame-based animations
ANIM_DIR = SCRIPT_DIR.parent / "mods" / "tuxemon" / "animations"

# Output: new sheet-based animations
OUT_DIR = SCRIPT_DIR.parent / "mods" / "tuxemon" / "animations_sheet"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FRAME_PATTERN = re.compile(r"(.+?)_(\d+)\.png$")


def collect_animation_slugs(folder: Path) -> dict[str, list[Path]]:
    """
    Collect all frame sequences in a folder.
    Returns: { slug: [frame_paths...] }
    """
    sequences: dict[str, list[Path]] = {}

    for p in folder.glob("*.png"):
        match = FRAME_PATTERN.match(p.name)
        if not match:
            continue

        slug, index = match.groups()
        sequences.setdefault(slug, []).append(p)

    # Sort frames numerically
    for slug in sequences:
        sequences[slug].sort(
            key=lambda p: int(FRAME_PATTERN.match(p.name).group(2))
        )

    return sequences


def build_sheet(slug: str, frames: list[Path], out_folder: Path):
    print(f"\nProcessing animation: {slug}")

    if not frames:
        print(" [X] No frames found")
        return None

    # Load first frame to get reference size
    with Image.open(frames[0]) as img:
        frame_w, frame_h = img.size

    print(f" Frames detected: {len(frames)}")
    print(f" Frame size: {frame_w}x{frame_h}")

    # Validate all frames have the same size
    for frame_path in frames:
        with Image.open(frame_path) as img:
            if img.size != (frame_w, frame_h):
                print(
                    f" [X] Inconsistent frame size in {frame_path.name}: {img.size}"
                )
                return None

    # Compute output sheet size
    sheet_w = frame_w * len(frames)
    sheet_h = frame_h
    print(f" Output sheet size: {sheet_w}x{sheet_h}")

    # Create canvas
    canvas = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

    # Paste frames horizontally
    for i, frame_path in enumerate(frames):
        with Image.open(frame_path) as img:
            canvas.paste(img.convert("RGBA"), (i * frame_w, 0))

    # Save output
    out_folder.mkdir(parents=True, exist_ok=True)
    out_path = out_folder / f"{slug}.png"
    canvas.save(out_path, "PNG")

    print(f" [✓] Saved sheet: {out_path}")

    # Return metadata for manifest
    return {
        "file": out_folder.name,
        "slug": slug,
        "frame_x": frame_w,
        "frame_y": frame_h,
    }


def main():
    success = 0
    fail = 0
    manifest = []

    # Iterate through animation categories
    for category in ANIM_DIR.iterdir():
        if not category.is_dir():
            continue

        print(f"\n=== Category: {category.name} ===")

        sequences = collect_animation_slugs(category)
        if not sequences:
            print(" No animations found.")
            continue

        out_folder = OUT_DIR / category.name

        for slug, frames in sequences.items():
            info = build_sheet(slug, frames, out_folder)
            if info:
                success += 1
                manifest.append(info)
            else:
                fail += 1

    print("\n=== SUMMARY ===")
    print(f" Successful sheets: {success}")
    print(f" Failed: {fail}")

    # Save manifest to file
    manifest_path = OUT_DIR / "manifest.yml"
    with open(manifest_path, "w", encoding="utf-8") as f:
        for entry in manifest:
            f.write(f"- file: {entry['file']}\n")
            f.write(f"  slug: {entry['slug']}\n")
            f.write(f"  frame_x: {entry['frame_x']}\n")
            f.write(f"  frame_y: {entry['frame_y']}\n\n")

    print(f"\nManifest saved to: {manifest_path}")


if __name__ == "__main__":
    main()
