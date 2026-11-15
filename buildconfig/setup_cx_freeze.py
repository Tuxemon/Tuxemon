#!/usr/bin/python
"""
Build the Windows binary package using cx_Freeze (Python 3.10+).

Do NOT run from a virtual environment.
"""

import logging
import os
import sys
from pathlib import Path

from cx_Freeze import Executable, setup

from tuxemon.database.yaml_utils import load_yaml

# Ensure tuxemon package is discoverable when run from buildconfig/
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

logger = logging.getLogger(__name__)

# Prevent SDL from opening a window during build
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "disk"


def load_config(config_file: str = "build_config.yaml"):
    config_path = BASE_DIR / config_file
    try:
        return load_yaml(config_path)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    config = load_config()

    build_exe_options = {
        "packages": config["packages"],
        "excludes": config["excludes"],
        "includes": config["includes"],
        "include_files": config["include_files"],
    }

    setup(
        name=config["name"],
        version=config["version"],
        description=config["description"],
        options={"build_exe": build_exe_options},
        executables=[
            Executable(
                config["executable"],  # run_tuxemon.py
                base=config["base"],
                icon=config["icon"],
                # No target_name → cx_Freeze outputs run_tuxemon.exe
            )
        ],
    )

    logger.info("Build completed successfully.")
