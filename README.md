Tuxemon
==============

Tuxemon is a free, open source monster-fighting RPG. It's in constant
development and improving all the time! Contributors of all skill and
level are welcome to join. 

![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
[![Documentation Status](https://readthedocs.org/projects/tuxemon/badge/?version=latest)](https://tuxemon.readthedocs.io/en/latest/?badge=latest)

[![Discord](https://img.shields.io/badge/Discord-join-blue?logo=discord&logoColor=white)](https://discord.gg/3ZffZwz)
[![Website](https://img.shields.io/badge/website-tuxemon.org-blue)](https://www.tuxemon.org)
[![Reddit](https://img.shields.io/reddit/subreddit-subscribers/Tuxemon?style=social)](https://www.reddit.com/r/tuxemon)
[![YouTube](https://img.shields.io/youtube/channel/subscribers/UC6BJ6H7dB2Dpb8wzcYhDU3w?style=social)](https://www.youtube.com/channel/UC6BJ6H7dB2Dpb8wzcYhDU3w)

![screenshot](https://www.tuxemon.org/images/featurette-01.png)


Features
--------

- Game data is all json, easy to modify and extend
- Game maps are created using the Tiled Map Editor
- Simple game script to write the story
- Dialogs, interactions on map, npc scripting
- Localized in several languages
- Seamless keyboard, mouse, and gamepad input
- Animated maps
- Lots of documentation
- Python code can be modified without a compiler
- CLI interface for live game debugging
- Runs on Windows, Linux, OS X, and some support on Android
- 393 monsters and 18 threats with sprites
- 274 techniques to use in battle
- 208 NPC sprites
- 223 items


Documentation
--------

- [Save System Architecture](docs/save_system.md)


Installation
------------

Complete Installation documentation:

- [docs/installation.md](docs/installation.md)


Mods
------------

Complete Mods documentation:

- [docs/mods.md](docs/mods.md)


Controls
--------

##### Game Controls
###### You can also set inputs in the options menu or config file
* *Arrow Keys* - Movement
* *Enter* - Select/activate
* *ESC* - Menu/Cancel
* *Shift* - Sprint

##### Debugging

You can enable dev_tools by changing `dev_tools` to `True` in the
`tuxemon.yaml` file:

```
[game]
dev_tools = True
```

These keyboard shortcuts are available with dev tools enabled
* *r* - Reload the map tiles
* *n* - No clip

##### Map Editor

Use *Tiled* map editor: https://www.mapeditor.org/


CLI Interface
--------------

Complete CLI documentation:

- [docs/cli.md](docs/cli.md)


Building
--------

There are many scripts for various builds in the buildconfig folder. 
These are meant to be run from the project root directory, for example,
to build the portable pypy build:

```shell
[user@localhost Tuxemon]$ buildconfig/build_pypy_portable_linux.sh
```

There will be a new directory called build, which will have the package
if everything was successful.

WARNING!  The build scripts are designed to be run in a dedicated VM.
They will add and remove packages and could leave your OS in a bad
state.  You should not use them on your personal computer.  Use in a vm
or container.

License
-------

With the exception of the lib folder which may have its own license, all
code in this project is licenced under [the GPLv3](https://www.gnu.org/licenses/gpl-3.0.html).

GPL v3+

Copyright (C) 2014-2026 William Edwards <shadowapex@gmail.com>,
Benjamin Bean <superman2k5@gmail.com>

This software is distributed under the GNU General Public Licence as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.  See the file
[LICENSE](LICENSE) for the conditions under which this software is made
available.  Tuxemon also contains code from other sources.


External links
--------------

* Official website: [tuxemon.org](https://www.tuxemon.org)
* Matrix: [Tuxemon](https://matrix.to/#/!ktrcrHpgkDOGCQOlxX:matrix.org)
* Discord: [Tuxemon](https://discord.gg/3ZffZwz)
* Reddit: [/r/Tuxemon](https://www.reddit.com/r/tuxemon)
* YouTube: [Tuxemon](https://www.youtube.com/channel/UC6BJ6H7dB2Dpb8wzcYhDU3w)
* Readthedocs: https://tuxemon.readthedocs.io/en/latest/
