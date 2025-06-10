#!/usr/bin/python
"""
Beautify a single YAML file:
    python yaml_beautifier.py my_data.yaml

Beautify a single YAML file with 2-space indent, without prompting:
    python yaml_beautifier.py my_data.yaml -i 2 -f

Beautify all YAML files in a directory (and its subdirectories):
    python yaml_beautifier.py my_yaml_folder -r

Beautify all YAML files in a directory with 2-space indent, recursively and forced:
    python yaml_beautifier.py my_yaml_folder -r -i 2 -f

Example (moving in scripts folder):
    python yaml_beautifier.py ../mods/tuxemon/PATH/ -r

Get help/usage information:
    python yaml_beautifier.py --help
"""
from argparse import ArgumentParser
from pathlib import Path

import yaml

DEFAULT_INDENT: int = 2


def beautify_yaml_file(file_path: Path, indent: int = DEFAULT_INDENT) -> None:
    """
    Reads a YAML file, pretty-prints its content, and overwrites the original file.
    """
    print(f"Beautifying '{file_path}' with indent={indent}...")
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        with file_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, indent=indent, default_flow_style=False)
        print(f"Successfully beautified '{file_path}'.")
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'.")
    except yaml.YAMLError:
        print(
            f"Error: Invalid YAML format in '{file_path}'. Please check its syntax."
        )
    except Exception as e:
        print(
            f"An unexpected error occurred while processing '{file_path}': {e}"
        )


def beautify_yaml_in_directory(
    directory_path: Path, indent: int = DEFAULT_INDENT
) -> None:
    """
    Walks through a directory and beautifies all .yaml files found.
    """
    print(f"Searching for YAML files in '{directory_path}' to beautify...")
    found_files = False
    for file_path in directory_path.rglob("*.yaml"):
        found_files = True
        beautify_yaml_file(file_path, indent)

    if not found_files:
        print(
            "No YAML files found in the specified directory or its subdirectories."
        )


if __name__ == "__main__":
    parser = ArgumentParser(description="Beautify YAML files.")
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to a single YAML file or a directory containing YAML files.",
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
        help="Recursively process all YAML files in the specified directory and its subdirectories.",
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
            "Usage: python yaml_beautifier.py <file_or_directory_path> [-i <indent>] [-r]"
        )
        print("Use --help for more options.")
    else:
        target_path: Path = Path(args.path)

        if target_path.is_file():
            if not target_path.suffix.lower() == ".yaml":
                print(
                    f"Warning: '{target_path}' does not appear to be a YAML file (missing .yaml extension)."
                )
            if not args.force:
                confirm = input(
                    f"Are you sure you want to beautify and overwrite '{target_path}'? (y/N): "
                )
                if confirm.lower() != "y":
                    print("Operation cancelled.")
                    exit()
            beautify_yaml_file(target_path, args.indent)
        elif target_path.is_dir():
            if not args.force:
                confirm = input(
                    f"Are you sure you want to recursively beautify and overwrite ALL YAML files in '{target_path}'? (y/N): "
                )
                if confirm.lower() != "y":
                    print("Operation cancelled.")
                    exit()
            beautify_yaml_in_directory(target_path, args.indent)
        else:
            print(
                f"Error: Path '{target_path}' is neither a file nor a directory."
            )
