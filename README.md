Tuxemon 0.4.26
==============

Tuxemon is a free, open source monster-fighting RPG.

[![Build Status](https://travis-ci.org/Tuxemon/Tuxemon.svg?branch=development)](https://travis-ci.org/Tuxemon/Tuxemon)

![screenshot](https://www.tuxemon.org/images/featurette-01.png)

Requirements
------------

Tuxemon uses a number of open source projects to work properly:

* *python* - version 3.6+
* *python-pygame* - python game library
* *python-pytmx* - python library to read Tiled Map Editor's TMX maps.
* *python-pyscroll* - fast module for animated scrolling maps.
* *[neteria](https://github.com/ShadowBlip/Neteria)* - Game networking framework for Python.

*Optional*

* *libShake* - rumble library for Linux.

Installation
------------

If you want to try the game, its recommended to download and try the master branch
first. The default development branch is often more up to date, but might have
breaking bugs. If you want to try the latest version or contribute code changes,
please use the development branch.


**Windows Source**

Install the latest version of python 3 from [here](https://www.python.org/downloads/)

Run:

```cmd
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
python -m pip install -U -r requirements.txt
python run_tuxemon.py
```

**Windows Binary**

Check the [release page](https://github.com/Tuxemon/Tuxemon/releases) for binaries.

**Ubuntu**

```sh
sudo apt install python python-pygame python-pip python-imaging git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
sudo pip install -U -r requirements.txt
python run_tuxemon.py
```

**Ubuntu 18.04 w/venv**

Use this if you don't want to modify your system packages
```sh
sudo apt install git python3-venv
git clone https://github.com/Tuxemon/Tuxemon.git
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run_tuxemon.py
```

**Debian**

```sh
sudo apt-get install python python-pygame python-pip python-imaging git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
sudo pip install -U -r requirements.txt
python run_tuxemon.py
```

*Optional rumble support*

```sh
sudo apt install build-essential
git clone https://github.com/zear/libShake.git
cd libShake/
make BACKEND=LINUX; sudo make install BACKEND=LINUX
```

**Mac OS X (Yosemite)**

```sh
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew tap Homebrew/python
brew update
brew install python
brew install sdl sdl_image sdl_ttf portmidi git
brew install sdl_mixer --with-libvorbis
sudo pip install git+https://github.com/pygame/pygame.git
sudo pip install -U -r requirements.txt 
git clone https://github.com/Tuxemon/Tuxemon.git
ulimit -n 10000; python run_tuxemon.py
```

**Arch Linux**

Tuxemon is available in the [AUR](https://aur.archlinux.org/packages/tuxemon-git/).

**Smartphones**

Android builds are highly experimental.  Download and install the apk from the 
[releases page](https://github.com/Tuxemon/Tuxemon/releases) and install to your
device.  You will need to manually install the mods folder.  Connect your device
to your computer and make a folder called "Tuxemon" in "Internal Storage", then
copy the mods folder.  Tuxemon will also need file system permissions, which you
can set in your phones settings.

**Fedora Linux**

```
sudo dnf install SDL*-devel freetype-devel libjpeg-devel portmidi-devel python3-devel
virtualenv venv
pip install -r requirements.txt
```


Controls
--------

##### Tuxemon
* *Arrow Keys* - Movement
* *Enter* - Select/activate
* *ESC* - Menu/Cancel
* *Shift* - Sprint

##### Map Editor

Use *Tiled* map editor: http://www.mapeditor.org/


Building
--------

There are many scripts for various builds in the buildconfig folder.  These
are meant to be run from the project root directory, for example, to build
the portable pypy build:
```
[user@localhost Tuxemon]$ buildconfig/build_pypy_portable_linux.sh
```
There will be a new directory called build, which will have the package if
everything was successful.

WARNING!  The build scripts are designed to be run in a dedicated VM.  They
will add and remove packages and could leave you OS in a bad state.  You
should not use them on your personal computer.  Use in a vm or container.


License
-------

With the exception of the lib folder which may have
its own license, all code in this project is licenced
under the GPLv3.

GPL v3+

Copyright (C) 2017 William Edwards <shadowapex@gmail.com>,     
Benjamin Bean <superman2k5@gmail.com>

This software is distributed under the GNU General Public Licence as published
by the Free Software Foundation, either version 3 of the License, or (at your
option) any later version.  See the file [LICENSE](LICENSE) for the conditions
under which this software is made available.  Tuxemon also contains code from
other sources.

External links
--------------

* Official website: [tuxemon.org](https://www.tuxemon.org)
* Official forum: [forum.tuxemon.org](https://forum.tuxemon.org/)
* IRC: [#tuxemon](ircs://chat.freenode.net/#tuxemon) on freenode ([webchat](https://webchat.freenode.net/?channels=%23tuxemon))
* Discord: [Tuxemon](https://discord.gg/3ZffZwz)
* Reddit: [/r/Tuxemon](https://www.reddit.com/r/tuxemon)
* YouTube: [Tuxemon](https://www.youtube.com/channel/UC6BJ6H7dB2Dpb8wzcYhDU3w)
