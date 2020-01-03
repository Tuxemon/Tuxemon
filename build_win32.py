#!/usr/bin/python
"""
Responsible for building the Windows binary package of the
game with cx_Freeze and Python 3.6

To build the package on Windows, run the following command on Windows:
    `python build_win32.py build`

DO NOT RUN FROM A VENV.  YOU WILL BE MET WITH INSURMOUNTABLE SORROW.
"""

from cx_Freeze import setup, Executable

includes = ['pkg_resources']
includefiles = ['tuxemon/tuxemon.cfg']
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
