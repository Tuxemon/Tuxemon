#!/usr/bin/env python3
"""Build the Windows binary package of the game with cx_Freeze.

To build on Windows, run this from the project root:
    python buildconfig/setup_windows.py build

Note: this project requires Python 3.10+.
"""
import os
import sys
from cx_Freeze import setup, Executable

# required so that the tuxemon folder can be found
# when run from the buildconfig folder
sys.path.append(os.getcwd())

# prevent SDL from opening a window
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "disk"

includes = ["pkg_resources"]
includefiles = ["mods"]
excludes = ["tkinter", "pyglet"]
packages = ["pytmx", "pyscroll", "pygame", "neteria", "natsort", "tuxemon"]

namespace_packages = []
build_exe_options = {
    "packages": packages,
    "excludes": excludes,
    "includes": includes,
    "include_files": includefiles,
    "namespace_packages": namespace_packages,
}

if __name__ == "__main__":
    setup(
        name="Tuxemon",
        version="0.4.35",
        options={"build_exe": build_exe_options},
        description="Open source RPG",
        executables=[
            Executable("run_tuxemon.py", base="Win32GUI", icon="mods/tuxemon/gfx/icon.ico")
        ],
    )
