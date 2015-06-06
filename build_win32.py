#!/usr/bin/python
"""Responsible for building the Windows binary package of the
game with cx_Freeze.

To build the package on Windows, run the following command on Windows:
    `python build_win32.py build`

"""

import sys
from cx_Freeze import setup, Executable

includes = ["twisted.internet", "twisted.internet.protocol", "pkg_resources"]
excludes = []
packages = []
namespace_packages = ["zope"]
build_exe_options = {"packages": packages, "excludes": excludes, "includes": includes,      "namespace_packages": namespace_packages, "append_script_to_exe":True}
base = None

if __name__ == "__main__":
    setup(
        name = "Tuxemon",
        version = "0.1",
        options = {"build_exe": build_exe_options},
        description = "Open source RPG",
        executables = [Executable("tuxemon.py", base=base)],
        )

