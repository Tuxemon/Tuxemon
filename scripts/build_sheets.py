#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0

from pathlib import Path

from PIL import Image

# Direction → (walk1, idle, walk2)
DIRECTION_MAP = {
    "front": ("_front_walk.000.png", "_front.png", "_front_walk.001.png"),
    "left": ("_left_walk.000.png", "_left.png", "_left_walk.001.png"),
    "right": ("_right_walk.000.png", "_right.png", "_right_walk.001.png"),
    "back": ("_back_walk.000.png", "_back.png", "_back_walk.001.png"),
}

ROW_ORDER = ["front", "left", "right", "back"]

SCRIPT_DIR = Path(__file__).resolve().parent
SPRITE_DIR = SCRIPT_DIR.parent / "mods" / "tuxemon" / "sprites"


def is_directional_base(base: str, folder: Path) -> bool:
    """
    A valid directional NPC must have at least the idle frame:
        <base>_front.png
    Ignore files like boss_green.png (no direction suffix).
    """
    return (folder / f"{base}_front.png").exists()


def collect_bases(folder: Path) -> list[str]:
    """
    Detect all NPC bases by scanning *_front.png files.
    """
    bases = []
    for p in folder.glob("*_front.png"):
        base = p.name[: -len("_front.png")]
        bases.append(base)
    return sorted(set(bases))


def build_sheet(base: str, folder: Path) -> bool:
    """
    Build a 4×3 overworld sheet for a single NPC.
    """
    print(f"\nProcessing: {base}")

    # Validate directional set
    required = []
    for direction in ROW_ORDER:
        for suffix in DIRECTION_MAP[direction]:
            required.append(folder / f"{base}{suffix}")

    missing = [p.name for p in required if not p.exists()]
    if missing:
        print(f" [X] Missing frames: {missing}")
        return False

    # Detect frame size from idle frame
    idle_path = folder / f"{base}_front.png"
    with Image.open(idle_path) as idle:
        frame_w, frame_h = idle.size

    # Sheet layout: 4 rows × 3 columns
    sheet_w = frame_w * 3
    sheet_h = frame_h * 4
    canvas = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

    # Paste frames
    for row, direction in enumerate(ROW_ORDER):
        suffixes = DIRECTION_MAP[direction]
        for col, suffix in enumerate(suffixes):
            img_path = folder / f"{base}{suffix}"
            with Image.open(img_path) as img:
                canvas.paste(
                    img.convert("RGBA"), (col * frame_w, row * frame_h)
                )

    # Save sheet in the same folder
    output_path = folder / f"{base}.png"
    canvas.save(output_path, "PNG")
    print(f" [✓] Saved sheet: {output_path}")
    return True


def main():
    folder = SPRITE_DIR

    bases = collect_bases(folder)
    if not bases:
        print("No directional sprites found.")
        return

    success = 0
    fail = 0

    for base in bases:
        if not is_directional_base(base, folder):
            print(f" [!] Skipping non-directional file: {base}")
            continue

        if build_sheet(base, folder):
            success += 1
        else:
            fail += 1

    print("\n=== SUMMARY ===")
    print(f" Successful sheets: {success}")
    print(f" Failed conversions: {fail}")


if __name__ == "__main__":
    main()
