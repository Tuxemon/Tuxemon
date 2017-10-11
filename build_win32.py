#!/usr/bin/python
"""Responsible for building the Windows binary package of the
game with cx_Freeze.

To build the package on Windows, run the following command on Windows:
    `python build_win32.py build`

"""

import sys
import os
from cx_Freeze import setup, Executable

BASEDIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "tuxemon")) + os.sep
print ("BASEDIR:", BASEDIR)

sys.path.insert(0, os.getcwd() + os.sep + "tuxemon")
os.chdir(os.getcwd() + os.sep + "tuxemon")

# Include all our plugins as well
from core.components.plugin import PluginManager
manager = PluginManager()
manager.setPluginPlaces([BASEDIR + "core/components/event/conditions", BASEDIR + "core/components/event/actions"])
manager.collectPlugins()

includes = ["pkg_resources"] + manager.modules
includefiles = ["tuxemon.cfg"]
excludes = []
packages = ["pygame", "pytmx"]
namespace_packages = []
build_exe_options = {"packages": packages,
                     "excludes": excludes,
					 "includes": includes,
					 "include_files": includefiles,
					 "namespace_packages": namespace_packages,
					 "append_script_to_exe":True}
base = None

# Include all files in the resources directory
for item in os.walk("./resources"):
	if len(item[-1]) > 0:
		for file in item[-1]:
			includefiles.append(item[0] + os.sep + file)
			
# Include plugin files
for item in os.walk("./core"):
	if len(item[1]) == 0:
		for file in item[-1]:
			if ".plugin" in file:
				includefiles.append(item[0] + os.sep + file)

if __name__ == "__main__":
    setup(
        name = "Tuxemon",
        version = "0.3",
        options = {"build_exe": build_exe_options},
        description = "Open source RPG",
        executables = [Executable("tuxemon.py", base=base, icon="resources/gfx/icon.ico")],
        )

