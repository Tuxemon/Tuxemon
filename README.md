![build-status](https://travis-ci.org/Tuxemon/Tuxemon.svg?branch=master)

Tuxemon
=========

Tuxemon is a free, open source monster-fighting RPG.

![screenshot](http://www.tuxemon.org/images/featurette-01.png)

Version
----

0.3

Requirements
-----------

Tuxemon uses a number of open source projects to work properly:

* *python* - version 2.7+
* *python-pygame* - python game library
* *python-pytmx* - python library to read Tiled Map Editor's TMX maps.

*Optional*

* *libShake* - rumble library for Linux.

Installation
--------------

**Ubuntu**

```sh

sudo apt-get install python python-pygame python-pip python-imaging git
sudo pip install pytmx
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

**Mac OS X (Yosemite)**

```sh
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew tap Homebrew/python
brew update
brew install python
brew install sdl sdl_image sdl_mixer sdl_ttf portmidi hg git
pip install pytmx
pip install pillow
pip install hg+http://bitbucket.org/pygame/pygame
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon/tuxemon
ulimit -n 10000; python tuxemon.py

```

**Smartphones**

[![Get it on Google Play](https://developer.android.com/images/brand/en_generic_rgb_wo_45.png)](https://play.google.com/store/apps/details?id=naman14.timber)

Controls
--------------

##### Tuxemon
* *Arrow Keys* - Movement
* *Enter* - Select/activate
* *ESC* - Menu/Cancel

##### Map Editor

Use *Tiled* map editor: http://www.mapeditor.org/
