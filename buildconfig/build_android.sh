#!/bin/bash
echo y | sdkmanager "ndk-bundle"
export ANDROIDNDK="$ANDROID_HOME/ndk-bundle"
sudo apt update
sudo apt-get install build-essential pkg-config python3.7 python3.7-dev \
  python3.7-gdbm autoconf automake libtool libffi-dev cmake openssl libssl-dev
sudo ln -fs /usr/bin/python3.7 /usr/bin/python3
sudo ln -fs /usr/bin/python3.7 /usr/bin/python
# do not use a virtualenv
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python get-pip.py
sudo python -m pip install setuptools pygame==2.0.0.dev10 Cython
sudo python -m pip install git+https://github.com/kivy/python-for-android.git
p4a --version
p4a apk --name Tuxemon \
  --private tuxemon \
  --version 0.0 \
  --package=org.tuxemon.Tuxemon \
  --requirements=libffi,python3==3.7.1,pygame2 \
  --bootstrap=sdl2
