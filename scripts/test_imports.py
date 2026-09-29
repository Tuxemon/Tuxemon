"""
Torture-test the Tuxemon codebase by importing every module.

This catches:
- broken imports
- missing optional dependencies
- syntax errors
- modules that crash at import time
"""

import importlib
import pkgutil
import sys
import traceback
from pathlib import Path


def walk_and_import(package_name: str) -> None:
    print(f"Scanning package: {package_name}")

    try:
        package = importlib.import_module(package_name)
    except Exception as e:
        print(f"FATAL: Cannot import top-level package '{package_name}': {e}")
        traceback.print_exc()
        return

    package_path = Path(package.__file__).parent

    failures = []

    for module_info in pkgutil.walk_packages(
        [str(package_path)], prefix=f"{package_name}."
    ):
        name = module_info.name

        if name.endswith(".__main__"):
            continue

        print(f"Importing: {name}")

        try:
            importlib.import_module(name)
        except Exception as e:
            print(f"ERROR importing {name}: {e}")
            failures.append((name, traceback.format_exc()))

    print("\n=== SUMMARY ===")
    if failures:
        print(f"{len(failures)} modules failed to import:\n")
        for name, tb in failures:
            print(f"--- {name} ---")
            print(tb)
    else:
        print("All modules imported successfully.")

    print("\nImport torture test complete.")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    walk_and_import("tuxemon")
