Tuxemon
=========

Tuxemon is a free, open source monster-fighting RPG.

![screenshot](http://www.tuxemon.org/images/featurette-01.png)

Version
----

0.3.2

Requirements
-----------

Tuxemon uses a number of open source projects to work properly:

* *python* - version 2.7+
* *python-pygame* - python game library
* *python-pytmx* - python library to read Tiled Map Editor's TMX maps.
* *[neteria](https://github.com/ShadowBlip/Neteria)* - Game networking framework for Python.

*Optional*

* *libShake* - rumble library for Linux.

Installation
--------------

**Ubuntu**

```sh
sudo apt-get install python python-pygame python-pip python-imaging git
sudo pip install pytmx
sudo pip install neteria
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon/tuxemon
./tuxemon.py
```

*Optional rumble support*

```sh
sudo apt-get install build-essential
git clone https://github.com/zear/libShake.git
cd libShake/
make; make install
```

**Debian**

```sh
sudo apt-get install python python-pygame python-pip python-imaging git
sudo pip install neteria
git clone https://github.com/bitcraft/PyTMX
cd PyTMX; python setup.py install
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon/tuxemon
./tuxemon.py
```

**Mac OS X (Yosemite)**

```sh
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew tap Homebrew/python
brew update
brew install python
brew install sdl sdl_image sdl_mixer sdl_ttf portmidi hg git
pip install pytmx
pip install pillow
pip install neteria
pip install hg+http://bitbucket.org/pygame/pygame
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon/tuxemon
ulimit -n 10000; python tuxemon.py
```

**Smartphones**
* [Android](http://www.tuxemon.org/files/builds/tuxemon-unstable-latest.apk) (APK file)

Controls
--------------

##### Tuxemon
* *Arrow Keys* - Movement
* *Enter* - Select/activate
* *ESC* - Menu/Cancel

##### Map Editor

Use *Tiled* map editor: http://www.mapeditor.org/

License
----

GNU v3

Copyright (C) 2015 William Edwards <shadowapex@gmail.com>,  
Benjamin Bean <superman2k5@gmail.com>

This software is distributed under the GNU General Public Licence as published
by the Free Software Foundation.  See the file LICENSE for the conditions
under which this software is made available.  Tuxemon also contains code from
other sources.
