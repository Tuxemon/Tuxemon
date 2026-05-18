#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0

from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
COMBAT_DIR = (
    SCRIPT_DIR.parent / "mods" / "tuxemon" / "gfx" / "sprites" / "player"
)
OUTPUT_DIR = (
    SCRIPT_DIR.parent / "mods" / "tuxemon" / "gfx" / "sprites" / "sheet"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def collect_bases(folder: Path) -> list[str]:
    """
    Detect combat sprite bases by scanning for:
        base.png
        base_alt1.png
    Back sprites are optional:
        base_back.png
        base_back_alt1.png
    """
    bases = []
    for p in folder.glob("*.png"):
        name = p.stem

        # Skip back sprites
        if name.endswith("_back"):
            continue

        # Skip back variants
        if "_back_" in name:
            continue

        bases.append(name)

    return sorted(set(bases))


def build_combat_sheet(base: str, folder: Path) -> bool:
    """
    Build a 1×2 combat sheet: [ BACK | FRONT ]
    If the back sprite is missing, the back frame is transparent.
    """
    print(f"\nProcessing: {base}")

    back_path = folder / f"{base}_back.png"
    front_path = folder / f"{base}.png"

    # FRONT IS REQUIRED
    if not front_path.exists():
        print(f" [X] Missing required front sprite: {front_path.name}")
        return False

    # Load front
    with Image.open(front_path) as front_img:
        front = front_img.convert("RGBA")

    frame_w, frame_h = front.size

    # Load back or create transparent placeholder
    if back_path.exists():
        with Image.open(back_path) as back_img:
            back = back_img.convert("RGBA")
        if back.size != (frame_w, frame_h):
            print(" [!] Back size mismatch, cropping to 64×64")
            back = back.crop((0, 0, frame_w, frame_h))

    else:
        print(f" [!] Back sprite missing, using transparent placeholder")
        back = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))

    # Create sheet: 1 row × 2 columns
    sheet_w = frame_w * 2
    sheet_h = frame_h
    canvas = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

    # Paste frames
    canvas.paste(back, (0, 0))
    canvas.paste(front, (frame_w, 0))

    # Save output
    output_path = OUTPUT_DIR / f"{base}.png"
    canvas.save(output_path, "PNG")
    print(f" [✓] Saved combat sheet: {output_path}")

    return True


def main():
    folder = COMBAT_DIR

    bases = collect_bases(folder)
    if not bases:
        print("No combat sprites found.")
        return

    success = 0
    fail = 0

    for base in bases:
        if build_combat_sheet(base, folder):
            success += 1
        else:
            fail += 1

    print("\n=== SUMMARY ===")
    print(f" Successful sheets: {success}")
    print(f" Failed sheets: {fail}")


if __name__ == "__main__":
    main()
