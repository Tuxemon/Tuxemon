#!/bin/bash
sudo apt-get install build-essential pkg-config python3-dev \
  autoconf automake libtool libffi-dev cmake python3-pip
python3 -m pip install setuptools pygame==2.0.0.dev10 Cython
python3 -m pip install git+https://github.com/pygame/python-for-android.git
p4a --version
p4a apk
  --name Tuxemon \
  --private tuxemon \
  --version 0.0 \
  --package=org.tuxemon.Tuxemon \
  --requirements=python3,pygame2,libffi \
  --bootstrap=sdl2
