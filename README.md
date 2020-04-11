Tuxemon 0.4.20
==============

Tuxemon is a free, open source monster-fighting RPG.

![screenshot](https://www.tuxemon.org/images/featurette-01.png)

Requirements
------------

Tuxemon uses a number of open source projects to work properly:

* *python* - version 2.7, 3.5+
* *python-pygame* - python game library
* *python-pytmx* - python library to read Tiled Map Editor's TMX maps.
* *python-six* - python 2 and 3 compatibility library
* *python-pyscroll* - fast module for animated scrolling maps.
* *[neteria](https://github.com/ShadowBlip/Neteria)* - Game networking framework for Python.

*Optional*

* *libShake* - rumble library for Linux.

Installation
------------

**Windows Source**

Install the latest version of python 3 from [here](https://www.python.org/downloads/)

Run:

```cmd
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
python -m pip install -U -r requirements.txt
python tuxemon.py
```

**Windows Binary**

Check the release page https://github.com/Tuxemon/Tuxemon/releases for binaries.

**Ubuntu**

```sh
sudo apt install python python-pygame python-pip python-imaging python-six git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
sudo pip install -U -r requirements.txt
python tuxemon.py
```

**Debian**

```sh
sudo apt-get install python python-pygame python-pip python-imaging git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
sudo pip install -U -r requirements.txt
python tuxemon.py
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
ulimit -n 10000; python tuxemon.py
```

**Arch Linux**

Tuxemon is available in the [AUR](https://aur.archlinux.org/packages/tuxemon-git/).

**Smartphones**
* [Android](https://www.tuxemon.org/files/builds/tuxemon-unstable-latest.apk) (APK file)


Controls
--------

##### Tuxemon
* *Arrow Keys* - Movement
* *Enter* - Select/activate
* *ESC* - Menu/Cancel
* *Shift* - Sprint

##### Map Editor

Use *Tiled* map editor: http://www.mapeditor.org/

Python 2.7 Notice
-----------------

We will be supporing bugfixes and features for python 2.7+ after it
is EOL starting in 2020.  We do plan on removing support for it
sometime in the future, but there is currently no roadmap to actively
stop supporting it at this time.

License
-------

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
* Google Plus: [+TuxemonOrg](https://plus.google.com/u/0/+TuxemonOrg)
