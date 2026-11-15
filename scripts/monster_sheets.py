#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0

from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
SPRITE_DIR = (
    SCRIPT_DIR.parent / "mods" / "tuxemon" / "gfx" / "sprites" / "battle"
)

# Expected filenames per monster base
FILE_MAP = {
    "front": "-front.png",
    "back": "-back.png",
    "menu01": "-menu01.png",
    "menu02": "-menu02.png",
}

ROW_ORDER = ["front", "back", "menu01", "menu02"]


def collect_bases(folder: Path) -> list[str]:
    """
    Detect all monster bases by scanning *-front.png files.
    """
    bases = []
    for p in folder.glob("*-front.png"):
        base = p.name[: -len("-front.png")]
        bases.append(base)
    return sorted(set(bases))


def build_sheet(base: str, folder: Path) -> bool:
    """
    Build a Pokémon-style 2×2 sheet for a monster:
        front  | back
        menu01 | menu02
    """
    print(f"\nProcessing: {base}")

    # Validate required files
    required_paths = {
        key: folder / f"{base}{suffix}" for key, suffix in FILE_MAP.items()
    }

    missing = [p.name for p in required_paths.values() if not p.exists()]
    if missing:
        print(f" [X] Missing frames: {missing}")
        return False

    # Load images
    with Image.open(required_paths["front"]) as img:
        front = img.convert("RGBA")
    with Image.open(required_paths["back"]) as img:
        back = img.convert("RGBA")
    with Image.open(required_paths["menu01"]) as img:
        menu1 = img.convert("RGBA")
    with Image.open(required_paths["menu02"]) as img:
        menu2 = img.convert("RGBA")

    # Sizes
    front_w, front_h = front.size
    back_w, back_h = back.size
    menu_w, menu_h = menu1.size

    # Sheet size:
    # width = max(front_w + back_w, menu_w + menu_w)
    # height = front_h + menu_h
    sheet_w = max(front_w + back_w, menu_w + menu_w)
    sheet_h = front_h + menu_h

    canvas = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

    # Paste top row
    canvas.paste(front, (0, 0))
    canvas.paste(back, (front_w, 0))

    # Paste bottom row
    canvas.paste(menu1, (0, front_h))
    canvas.paste(menu2, (menu_w, front_h))

    # Save sheet
    output_path = folder / f"{base}-sheet.png"
    canvas.save(output_path, "PNG")
    print(f" [✓] Saved sheet: {output_path}")
    return True


def main():
    folder = SPRITE_DIR

    bases = collect_bases(folder)
    if not bases:
        print("No monster sprites found.")
        return

    success = 0
    fail = 0

    for base in bases:
        if build_sheet(base, folder):
            success += 1
        else:
            fail += 1

    print("\n=== SUMMARY ===")
    print(f" Successful sheets: {success}")
    print(f" Failed conversions: {fail}")


if __name__ == "__main__":
    main()
