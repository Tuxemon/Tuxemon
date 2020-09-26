#!/usr/bin/python
"""
Responsible for building the Windows binary package of the
game with cx_Freeze and Python 3.6

To build the package on Windows, run the following command on Windows:
    `python build_win32.py build`

"win32" is just the name used by cx_freeze and doesn't mean it is a 32-bit app.

DO NOT RUN FROM A VENV.  YOU WILL BE MET WITH INSURMOUNTABLE SORROW.
"""
import os
import sys
from cx_Freeze import setup, Executable

# required so that the tuxemon folder can be found
# when run from the buildscripts folder
sys.path.append(os.getcwd())

# prevent SDL from opening a window
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "disk"

includes = ['pkg_resources']
includefiles = []
excludes = ['email', 'tkinter', 'pyglet']
packages = ['pytmx', 'pyscroll', 'pygame', 'six', 'neteria', 'tuxemon']

namespace_packages = []
build_exe_options = {'packages': packages,
                     'excludes': excludes,
                     'includes': includes,
                     'include_files': includefiles,
                     'namespace_packages': namespace_packages}

if __name__ == '__main__':
    setup(
        name='Tuxemon',
        version='0.4.2',
        options={'build_exe': build_exe_options},
        description='Open source RPG',
        executables=[Executable('tuxemon.py', icon='tuxemon/resources/gfx/icon.ico')],
    )
