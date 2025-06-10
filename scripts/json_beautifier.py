#!/usr/bin/python
"""
Beautify a single JSON file:
    python json_beautifier.py my_data.json

Beautify a single JSON file with 2-space indent, without prompting:
    python json_beautifier.py my_data.json -i 2 -f

Beautify all JSON files in a directory (and its subdirectories):
    python json_beautifier.py my_json_folder -r

Beautify all JSON files in a directory with 2-space indent, recursively and forced:
    python json_beautifier.py my_json_folder -r -i 2 -f

Example (moving in scripts folder):
    python yaml_beautifier.py ../mods/tuxemon/PATH/ -r

Get help/usage information:
    python json_beautifier.py --help
"""
import json
from argparse import ArgumentParser
from pathlib import Path

DEFAULT_INDENT: int = 2
SORT_KEYS: bool = True


def beautify_json_file(
    file_path: Path, indent: int = DEFAULT_INDENT, sort_keys: bool = SORT_KEYS
) -> None:
    """
    Reads a JSON file, pretty-prints its content, and overwrites the original file.
    """
    print(f"Beautifying '{file_path}' with indent={indent}...")
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, sort_keys=sort_keys)
        print(f"Successfully beautified '{file_path}'.")
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'.")
    except json.JSONDecodeError:
        print(
            f"Error: Invalid JSON format in '{file_path}'. Please check its syntax."
        )
    except Exception as e:
        print(
            f"An unexpected error occurred while processing '{file_path}': {e}"
        )


def beautify_json_in_directory(
    directory_path: Path, indent: int = DEFAULT_INDENT
) -> None:
    """
    Walks through a directory and beautifies all .json files found.
    """
    print(f"Searching for JSON files in '{directory_path}' to beautify...")
    found_files = False
    for file_path in directory_path.rglob("*.json"):
        found_files = True
        beautify_json_file(file_path, indent)

    if not found_files:
        print(
            "No JSON files found in the specified directory or its subdirectories."
        )


if __name__ == "__main__":
    parser = ArgumentParser(description="Beautify JSON files.")
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to a single JSON file or a directory containing JSON files.",
    )
    parser.add_argument(
        "-i",
        "--indent",
        type=int,
        default=DEFAULT_INDENT,
        help="Number of spaces for indentation (default: DEFAULT_INDENT).",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively process all JSON files in the specified directory and its subdirectories. Implied when a directory is given without -r, if only json files should be processed.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite without prompting (use with caution).",
    )

    args = parser.parse_args()

    if not args.path:
        print(
            "Usage: python json_beautifier.py <file_or_directory_path> [-i <indent>] [-r]"
        )
        print("Use --help for more options.")
    else:
        target_path: Path = Path(args.path)

        if target_path.is_file():
            if not target_path.suffix.lower() == ".json":
                print(
                    f"Warning: '{target_path}' does not appear to be a JSON file (missing .json extension)."
                )
            if not args.force:
                confirm = input(
                    f"Are you sure you want to beautify and overwrite '{target_path}'? (y/N): "
                )
                if confirm.lower() != "y":
                    print("Operation cancelled.")
                    exit()
            beautify_json_file(target_path, args.indent)
        elif target_path.is_dir():
            if not args.force:
                confirm = input(
                    f"Are you sure you want to recursively beautify and overwrite ALL JSON files in '{target_path}'? (y/N): "
                )
                if confirm.lower() != "y":
                    print("Operation cancelled.")
                    exit()
            beautify_json_in_directory(target_path, args.indent)
        else:
            print(
                f"Error: Path '{target_path}' is neither a file nor a directory."
            )
