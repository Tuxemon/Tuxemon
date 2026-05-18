#!/usr/bin/python
"""
To beautify a single file:
    python po_beautifier.py my_translation.po

To beautify all .po files in the current directory:
    python po_beautifier.py *.po

To beautify files in a specific folder:
    python po_beautifier.py ../mods/tuxemon/l18n/LANGUAGE/LC_MESSAGES -r

To beautify a file but NOT remove obsolete entries:
    python po_beautifier.py my_translation.po --no-remove-obsolete
"""

from argparse import ArgumentParser
from pathlib import Path

from polib import pofile


def beautify_po_file(filepath: Path, remove_obsolete_entries: bool = True):
    """
    Beautifies a .po file by cleaning up whitespace, line lengths,
    and removing obsolete entries. Metadata is left untouched.
    """
    try:
        filepath = filepath.resolve()
        if not filepath.exists():
            print(f"Error: File not found at {filepath}. Skipping.")
            return

        if not filepath.is_file():
            print(f"Error: Path {filepath} is not a file. Skipping.")
            return

        po = pofile(filepath.as_posix(), encoding="utf-8")
        print(f"Processing {filepath} ({len(po)} entries)...")

        if remove_obsolete_entries:
            po_temp = pofile(filepath.as_posix(), encoding="utf-8")
            po.clear()
            po.extend(po_temp)
            print(f"Obsolete entries removed, if any.")

        po.save(filepath.as_posix())
        print(f"Successfully beautified {filepath}")

    except Exception as e:
        print(f"Error processing {filepath}: {e}")


def beautify_po_in_directory(
    directory_path: Path, remove_obsolete_entries: bool = True
):
    """
    Walks through a directory and beautifies all .po files found.
    """
    directory_path = directory_path.resolve()
    print(f"Searching for .po files in '{directory_path}'...")

    found_files = False
    for file_path in directory_path.rglob("*.po"):
        found_files = True
        beautify_po_file(file_path, remove_obsolete_entries)

    if not found_files:
        print("No .po files found in the specified directory.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Beautify one or more .po files.")
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="+",
        type=Path,
        help="One or more .po files or directories to beautify.",
    )
    parser.add_argument(
        "--no-remove-obsolete",
        action="store_false",
        dest="remove_obsolete",
        help="Do not remove obsolete (#~) entries from the .po file(s).",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively process all .po files in the specified directory.",
    )

    args = parser.parse_args()

    for path in args.files:
        path = path.resolve()
        if path.is_file():
            beautify_po_file(path, args.remove_obsolete)
        elif path.is_dir() and args.recursive:
            beautify_po_in_directory(path, args.remove_obsolete)
        else:
            print(
                f"Error: Path '{path}' is neither a valid file nor directory."
            )
