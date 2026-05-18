#!/usr/bin/python
"""
Convert JSON files to YAML.

Examples:

Convert a single JSON file:
    python jsonify_to_yaml.py my_data.json

Convert a single JSON file without prompting:
    python jsonify_to_yaml.py my_data.json -f

Convert all JSON files in a directory (and its subdirectories):
    python jsonify_to_yaml.py my_json_folder -r
    python jsonify_to_yaml.py ../mods/tuxemon/db/monster -r

Convert all JSON files in a directory recursively and forced:
    python jsonify_to_yaml.py my_json_folder -r -f

Get help/usage information:
    python jsonify_to_yaml.py --help
"""

import json
from argparse import ArgumentParser
from pathlib import Path

from tuxemon.database.yaml_utils import dump_yaml_io


def convert_json_to_yaml(json_filepath: Path, force: bool = False) -> None:
    """
    Reads a JSON file, converts its content to YAML format,
    and saves it to a new file with a .yaml extension.
    """
    yaml_filepath = json_filepath.with_suffix(".yaml")
    print(f"Converting '{json_filepath}' → '{yaml_filepath}'...")

    try:
        with json_filepath.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at '{json_filepath}'.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{json_filepath}': {e}")
        return
    except Exception as e:
        print(f"Unexpected error reading '{json_filepath}': {e}")
        return

    if not force and yaml_filepath.exists():
        confirm = input(
            f"YAML file '{yaml_filepath}' already exists. Overwrite? (y/N): "
        )
        if confirm.lower() != "y":
            print("Skipped.")
            return

    try:
        with yaml_filepath.open("w", encoding="utf-8") as f:
            dump_yaml_io(
                f,
                data,
                sort_keys=False,
                default_flow_style=False,
            )
        print(f"Successfully converted '{json_filepath}' → '{yaml_filepath}'.")
    except Exception as e:
        print(f"Error writing YAML to '{yaml_filepath}': {e}")


def convert_json_in_directory(
    directory_path: Path, recursive: bool, force: bool
) -> None:
    """
    Walks through a directory and converts all .json files to YAML.
    """
    print(f"Searching for JSON files in '{directory_path}'...")
    found_files = False
    iterator = (
        directory_path.rglob("*.json")
        if recursive
        else directory_path.glob("*.json")
    )

    for file_path in iterator:
        found_files = True
        convert_json_to_yaml(file_path, force)

    if not found_files:
        print("No JSON files found in the specified directory.")


if __name__ == "__main__":
    parser = ArgumentParser(description="Convert JSON files to YAML.")
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to a single JSON file or a directory containing JSON files.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively process all JSON files in the specified directory and its subdirectories.",
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
            "Usage: python jsonify_to_yaml.py <file_or_directory_path> [-r] [-f]"
        )
        print("Use --help for more options.")
    else:
        target_path: Path = Path(args.path)

        if target_path.is_file():
            if target_path.suffix.lower() != ".json":
                print(
                    f"Warning: '{target_path}' does not appear to be a JSON file."
                )
            convert_json_to_yaml(target_path, args.force)
        elif target_path.is_dir():
            convert_json_in_directory(target_path, args.recursive, args.force)
        else:
            print(
                f"Error: Path '{target_path}' is neither a file nor a directory."
            )
