#!/bin/bash

set -e
set -x

if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
    sudo apt-get update -qq
    sudo apt-get build-dep -qq python-pygame
    sudo apt-get install -qq python-pygame
elif [[ "$TRAVIS_OS_NAME" == "osx" ]]; then
    brew tap Homebrew/python
    brew update
    brew install python
    brew install sdl sdl_image sdl_mixer sdl_ttf portmidi hg git
fi

echo pip install pytmx
echo pip install Pillow
echo pip install Yapsy
