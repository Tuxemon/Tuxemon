#!/bin/bash

# debian 10

# might be for the android build environment, not sure
export ANDROID_BUILD_TOOLS_VERSION=28.0.2
export ANDROID_TOOLS=commandlinetools-linux-6858069_latest.zip
export ANDROID_HOME=$HOME/android_sdk
export ANDROID_SDK_ROOT=$HOME/android_sdk

# i think these are only for p4a
export ANDROIDSDK="$ANDROID_HOME"
export ANDROIDAPI=27
export NDKAPI=21
export NDKVER=21.4.7075529
export ANDROIDNDK="$HOME/android_sdk/ndk/$NDKVER"

sudo apt remove openjre* openjdk*

# alternative jdk-8 because it is not in debian
wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public | sudo apt-key add -
echo "deb https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/ buster main" | sudo tee /etc/apt/sources.list.d/adoptopenjdk.jfrog.io.list
sudo apt update
sudo apt -y remove --purge man-db  # for faster apt on a build box
sudo apt -y install adoptopenjdk-8-hotspot
sudo apt -y install build-essential pkg-config python3.7-dev python3-distutils \
  python3.7-venv python3-pip autoconf automake libtool libffi-dev cmake zip unzip git \
  ccache libssl-devel libc6:i386 libncurses5:i386 libstdc++6:i386 lib32z1 \
  libbz2-1.0:i386

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
yes | sdkmanager "ndk;21.4.7075529"

python3 -m pip install setuptools wheel Cython
python3 -m pip install git+https://github.com/pygame/python-for-android.git
git clone https://github.com/Tuxemon/Tuxemon.git
cd Tuxemon
p4a --version
p4a apk --name Tuxemon \
  --private tuxemon \
  --version 0.0 \
  --package=org.tuxemon.Tuxemon \
  --requirements=openssl,pygame,pyscroll,pytmx,babel,setuptools,natsort \
  --bootstrap=sdl2 \
  --orientation=landscape
