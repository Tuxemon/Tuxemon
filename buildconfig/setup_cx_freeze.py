#!/usr/bin/python
"""
Responsible for building the Windows binary package of the
game with cx_Freeze and Python 3.6

To build the package on Windows, run the following command on Windows:
    `python build_win32.py build`

"win32" is just the name used by cx_freeze and doesn't mean it is a 32-bit app.

DO NOT RUN FROM A VENV.  YOU WILL BE MET WITH INSURMOUNTABLE SORROW.
"""
import logging
import os
import sys

import yaml
from cx_Freeze import Executable, setup

# required so that the tuxemon folder can be found
# when run from the buildconfig folder
sys.path.append(os.getcwd())

logger = logging.getLogger(__name__)

# prevent SDL from opening a window
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "disk"

def load_config(config_file="build_config.yaml"):
    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
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
        options={"build_exe": build_exe_options},
        description=config["description"],
        executables=[
            Executable(
                config["executable"],
                base=config["base"],
                icon=config["icon"],
            )
        ],
    )
    logger.info("Build completed successfully.")
