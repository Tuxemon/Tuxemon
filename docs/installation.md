# Tuxemon Installation Guide

This document contains only the installation instructions.

---

## Overview

This guide describes how to install and run Tuxemon on various platforms, including Windows, Linux distributions, macOS, and experimental Android builds.

Tuxemon is developed in Python and can be run directly from source or through platform‑specific packaging systems.

---

## Windows Installation

### Source Installation (Recommended)

Requires **Python 3.10+** and **Git**.

```shell
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
py -3 -m pip install -U -r requirements.txt
py -3 run_tuxemon.py
```

### Windows Binary

Windows binaries are currently **non‑functional**.

Use the source installation instead.

---

## Flatpak (Linux)

### Standard Install

```shell
flatpak install flathub org.tuxemon.Tuxemon
flatpak run org.tuxemon.Tuxemon
```

### Nightly Builds

```shell
flatpak install Tuxemon.flatpak
flatpak run org.tuxemon.Tuxemon
```

---

## Debian / Ubuntu

### Virtual Environment Install (Recommended)

```shell
sudo apt install git python3-venv
git clone https://github.com/Tuxemon/Tuxemon.git
python3 -m venv venv
source venv/bin/activate
cd Tuxemon
python3 -m pip install -U -r requirements.txt
python3 run_tuxemon.py
```

### System‑Wide Install (Not Recommended)

```shell
sudo apt install python3 python3-pygame python3-pip python3-imaging git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
sudo pip3 install -U -r requirements.txt
python3 run_tuxemon.py
```

### Optional: Rumble Support

```shell
sudo apt install build-essential
git clone https://github.com/zear/libShake.git
cd libShake/
make BACKEND=LINUX; sudo make install BACKEND=LINUX
```

---

## Fedora Linux

```shell
sudo dnf install SDL2*-devel freetype-devel libjpeg-devel portmidi-devel python3-devel
git clone https://github.com/Tuxemon/Tuxemon.git
python3 -m venv venv
source venv/bin/activate
cd Tuxemon
python3 -m pip install -U -r requirements.txt
python3 run_tuxemon.py
```

---

## Arch Linux

Manual installation is recommended.

```shell
sudo pacman -S python python-pip python-pillow python-pygame python-pydantic git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
python -m pip install -U -r requirements.txt
python run_tuxemon.py
```

---

## Android (Experimental)

* Build using scripts in the `buildconfig/` directory.
* Copy the `mods` folder to `Internal Storage/Tuxemon`.
* Grant the app filesystem permissions.

Android support is experimental and may require manual setup.

---

## macOS

### macOS Yosemite

```shell
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

### macOS Sequoia (with uv)

```shell
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
brew update
brew install uv python git sdl sdl2_image sdl2_ttf sdl2_mixer portmidi libvorbis
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
uv sync
uv run python run_tuxemon.py
```

---

## Developer Setup

If you are contributing code, running tests, or performing style checks, install the optional development or test dependencies:

```shell
# Install test dependencies
pip install -e .[test]

# Install full development environment (tests, linters, type checkers)
pip install -e .[dev]
```

Alternatively, use the Makefile targets:

* `make test-setup`: Installs test dependencies.
* `make dev-setup`: Installs development dependencies.
* `make test`: Runs tests via tox.
* `make format`: Automatically formats and fixes code.
* `make lint`: Runs linters.
* `make type`: Runs static type checking.

---

## Notes

* Running from source is the most reliable method across all platforms.
* Build scripts in `buildconfig/` are intended for use inside a VM or container.
* For scripting, debugging, and developer tools, refer to the **CLI Interface** document.

---

## External Resources

* Official Website: [https://www.tuxemon.org](https://www.tuxemon.org)
* Documentation: [https://tuxemon.readthedocs.io/en/latest/](https://tuxemon.readthedocs.io/en/latest/)
* Source Code: [https://github.com/Tuxemon/Tuxemon](https://github.com/Tuxemon/Tuxemon)
