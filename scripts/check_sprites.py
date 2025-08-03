#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014–2025 William Edwards, Benjamin Bean

"""
Sprite Validation Script for Tuxemon

Usage:
-------
Run from terminal:
    python3 check_sprites.py

What this script checks:
-------------------------
Dimensions:
- '-front.png' or '-back.png' must be 64x64 pixels
- '-menu01.png' or '-menu02.png' must be 24x24 pixels

Mode:
- Must be RGB or RGBA

Color Palette:
- Records number of colors
- Warns if color count exceeds 256

Post-conversion checks (ImageMagick):
- Must be in indexed mode ('P')
- Must preserve transparency
- Must have ≤ 256 colors

Violations are printed to the console and saved in a report.
"""

import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image


def save_report_to_txt(report, output_path="sprite_report.txt"):
    with open(output_path, "w", encoding="utf-8") as f:
        if not report:
            f.write("All images passed validation.\n")
            return

        clustered = defaultdict(list)
        for entry in report:
            monster = entry["filename"].split("-")[0]
            clustered[monster].append(entry)

        f.write("Report:\n\n")
        for monster, entries in sorted(clustered.items()):
            f.write(f"Tuxemon: {monster}\n")
            for entry in entries:
                line = f"  - {entry['filename']}: {entry['issue']}"
                f.write(line + "\n")
            f.write("\n")


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
                info = img.info

                # Dimension checks
                if filename.endswith(("-front.png", "-back.png")):
                    if (width, height) != (64, 64):
                        issues.append(
                            {
                                "filename": filename,
                                "issue": f"Expected 64x64, got {width}x{height}",
                                "level": "error",
                            }
                        )

                elif filename.endswith(("-menu01.png", "-menu02.png")):
                    if (width, height) != (24, 24):
                        issues.append(
                            {
                                "filename": filename,
                                "issue": f"Expected 24x24, got {width}x{height}",
                                "level": "error",
                            }
                        )

                # Mode check
                if mode not in ("RGB", "RGBA"):
                    issues.append(
                        {
                            "filename": filename,
                            "issue": f"Unexpected mode: {mode}",
                            "level": "warning",
                        }
                    )

                # Metadata info
                for key, value in info.items():
                    issues.append(
                        {
                            "filename": filename,
                            "issue": f"info: {key}: {value}",
                            "level": "info",
                        }
                    )

                # Color count check
                colors = img.getcolors(maxcolors=256 * 256)
                if colors is None:
                    issues.append(
                        {
                            "filename": filename,
                            "issue": "Too many colors to count",
                            "level": "warning",
                            "num_colors": ">65536",
                        }
                    )
                else:
                    num_colors = len(colors)
                    issues.append(
                        {
                            "filename": filename,
                            "issue": f"{num_colors} colors",
                            "level": "info",
                            "num_colors": num_colors,
                        }
                    )

                # Post-conversion checks (ImageMagick compliance)
                if img.mode != "P":
                    issues.append(
                        {
                            "filename": filename,
                            "issue": "Post-conversion check: Expected indexed mode ('P')",
                            "level": "error",
                        }
                    )

                if "transparency" not in img.info and img.mode != "RGBA":
                    issues.append(
                        {
                            "filename": filename,
                            "issue": "Post-conversion check: Transparency missing or not preserved",
                            "level": "warning",
                        }
                    )

                converted_colors = img.getcolors(maxcolors=256)
                if converted_colors is None:
                    issues.append(
                        {
                            "filename": filename,
                            "issue": "Post-conversion check: Too many colors (over 256)",
                            "level": "error",
                        }
                    )
                else:
                    converted_count = len(converted_colors)
                    if converted_count > 256:
                        issues.append(
                            {
                                "filename": filename,
                                "issue": f"Post-conversion check: {converted_count} colors (exceeds 256)",
                                "level": "error",
                            }
                        )
                    else:
                        issues.append(
                            {
                                "filename": filename,
                                "issue": f"Post-conversion check: {converted_count} colors",
                                "level": "info",
                            }
                        )

        except Exception as e:
            issues.append(
                {
                    "filename": filename,
                    "issue": f"Error opening image: {str(e)}",
                    "level": "error",
                }
            )

    return issues


if __name__ == "__main__":
    report = analyze_battles_images()

    clustered = defaultdict(list)
    issue_counts = defaultdict(int)

    for entry in report:
        monster = entry["filename"].split("-")[0]
        clustered[monster].append(entry)
        issue_counts[entry["issue"]] += 1

    if not report:
        print("All images passed validation.")
    else:
        save_report_to_txt(report)
        print("Validation completed. See 'sprite_report.txt' for details.")
        sys.exit(1)
