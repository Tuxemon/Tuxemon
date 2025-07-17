# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
"""
Sprite Validation Script for Tuxemon

To run this script:
1. Open a terminal
2. Navigate to the `scripts` folder
3. Run: python3 check_sprites.py

What this script checks:
-------------------------
Dimensions:
- Images ending in '-front.png' or '-back.png' must be 64x64 pixels
- Images ending in '-menu01.png' or '-menu02.png' must be 24x24 pixels

Mode:
- All images must be in RGB or RGBA mode

Color Palette:
- Maximum of 16 unique colors (or whatever is decided)

Any violations will be printed to the console for review.
"""

from collections import defaultdict
from pathlib import Path

from PIL import Image

MAX_COLORS: int = 32


def analyze_battles_images() -> list[dict[str, str]]:
    folder_path = Path("../mods/tuxemon/gfx/sprites/battle")
    issues = []

    for file_path in folder_path.iterdir():
        if file_path.suffix.lower() != ".png":
            continue

        filename = file_path.name

        try:
            with Image.open(file_path) as img:
                width, height = img.size
                mode = img.mode

                # Check dimensions
                if filename.endswith(("-front.png", "-back.png")):
                    if (width, height) != (64, 64):
                        issues.append(
                            {
                                "filename": filename,
                                "issue": f"Expected 64x64, got {width}x{height}",
                            }
                        )

                elif filename.endswith(("-menu01.png", "-menu02.png")):
                    if (width, height) != (24, 24):
                        issues.append(
                            {
                                "filename": filename,
                                "issue": f"Expected 24x24, got {width}x{height}",
                            }
                        )

                # Check mode
                if mode not in ("RGB", "RGBA"):
                    issues.append(
                        {"filename": filename, "issue": f"Invalid mode: {mode}"}
                    )

                # Check color count
                colors = img.getcolors(maxcolors=256 * 256)
                if colors is None:
                    issues.append(
                        {"filename": filename, "issue": "Too many colors to count"}
                    )
                elif len(colors) > MAX_COLORS:
                    issues.append(
                        {
                            "filename": filename,
                            "issue": f"{len(colors)} colors (exceeds {MAX_COLORS})",
                        }
                    )

                rgb_colors = []
                for count, color in colors:
                    if isinstance(color, tuple):
                        rgb_colors.append(color[:3])  # RGB or RGBA
                    else:
                        rgb_colors.append(
                            (color, color, color)
                        )  # Grayscale as fake RGB

        except Exception as e:
            issues.append(
                {"filename": filename, "issue": f"Error opening image: {str(e)}"}
            )

    return issues


if __name__ == "__main__":
    report = analyze_battles_images()

    clustered = defaultdict(list)
    for entry in report:
        monster = entry["filename"].split("-")[0]
        clustered[monster].append(entry)

    if not report:
        print("All images passed validation.")
    else:
        print("Issues found:\n")
        for monster, entries in sorted(clustered.items()):
            print(f"Tuxemon: {monster}")
            for entry in entries:
                print(f"  - {entry['filename']}: {entry['issue']}")
            print()

    output_path = Path("sprite_report.txt")
    with output_path.open("w", encoding="utf-8") as f:
        if not report:
            f.write("All images passed validation.\n")
        else:
            f.write("Issues found:\n\n")
            for monster, entries in sorted(clustered.items()):
                f.write(f"Tuxemon: {monster}\n")
                for entry in entries:
                    f.write(f"  - {entry['filename']}: {entry['issue']}\n")
                f.write("\n")

    print(f"Report saved to: {output_path.resolve()}")
