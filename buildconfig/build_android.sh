#!/bin/bash
export ANDROID_BUILD_TOOLS_VERSION=28.0.2
export ANDROIDAPI=27
export ANDROID_TOOLS=commandlinetools-linux-6609375_latest.zip
export ANDROID_HOME=$HOME/android_sdk
export ANDROID_SDK_ROOT=$HOME/android_sdk
export ANDROIDNDK=$HOME/android_sdk/ndk-bundle
sudo apt update
sudo apt-get -y remove --purge man-db
sudo apt-get -y install build-essential pkg-config python3.7-dev python3-distutils \
  python3.7-venv autoconf automake libtool libffi-dev cmake openjdk-8-jdk unzip git \
  libssl-devel zip
sudo ln -sf /usr/bin/python3.7 /usr/bin/python3
wget https://dl.google.com/android/repository/$ANDROID_TOOLS
mkdir -p $ANDROID_HOME
unzip -q $ANDROID_TOOLS -d $ANDROID_HOME/cmdline-tools
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/tools/bin
mkdir -p $HOME/.android
touch $HOME/.android/repositories.cfg
sdkmanager --update
yes | sdkmanager "platform-tools" >/dev/null
yes | sdkmanager "platforms;android-$ANDROIDAPI" >/dev/null
yes | sdkmanager "build-tools;$ANDROID_BUILD_TOOLS_VERSION" >/dev/null
yes | sdkmanager "ndk-bundle"
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
python3 -m pip install setuptools wheel pygame==2.0.0.dev12 Cython
python3 -m pip install git+https://github.com/pygame/python-for-android.git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
p4a --version
p4a apk --name Tuxemon \
  --private tuxemon \
  --version 0.0 \
  --package=org.tuxemon.Tuxemon \
  --requirements=openssl,libffi,python3==3.7.1,pygame==2.0.0.dev12 \
  --bootstrap=sdl2,
  --orientation=landscape,
