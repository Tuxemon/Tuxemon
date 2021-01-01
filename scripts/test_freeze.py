"""

torture test the codebase by importing all the files alone.
* looks for broken references to files in `mods`
* looks for awkward or broken imports

[Tuxemon]$ python scripts/test_freeze.py
"""

import os
import sys
import cx_Freeze

parent = os.path.abspath(os.path.join(__file__, "..", ".."))
sys.path.append(parent)
cm = cx_Freeze.freezer.ConstantsModule()
finder = cx_Freeze.finder.ModuleFinder([], [], constants_module=cm)
finder.IncludePackage("tuxemon")
