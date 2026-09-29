#!/bin/bash
# debian 10

# might be for the android build environment, not sure
export ANDROID_BUILD_TOOLS_VERSION=28.0.2
export ANDROID_TOOLS=commandlinetools-linux-6858069_latest.zip
export ANDROID_SDK_ROOT=$HOME/android_sdk

# i think these are only for p4a
export ANDROIDSDK="$ANDROID_SDK_ROOT"
export ANDROIDAPI=27
export NDKAPI=21
export NDKVER=21.4.7075529
export ANDROIDNDK="$HOME/android_sdk/ndk/$NDKVER"

# debian jvm wont work
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

{
  cd /tmp
  mkdir -p $ANDROID_SDK_ROOT
  mkdir -p $HOME/.android
  [ -e $ANDROID_TOOLS ] || wget https://dl.google.com/android/repository/$ANDROID_TOOLS
  unzip -o -q $ANDROID_TOOLS -d $ANDROID_SDK_ROOT
  cd $ANDROID_SDK_ROOT/cmdline-tools
  mkdir latest
  mv * latest
  touch $HOME/.android/repositories.cfg
}
export PATH="$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$HOME/.local/bin"

sdkmanager --update
yes | sdkmanager "platform-tools" >/dev/null
yes | sdkmanager "platforms;android-$ANDROIDAPI" >/dev/null
yes | sdkmanager "build-tools;$ANDROID_BUILD_TOOLS_VERSION" >/dev/null
yes | sdkmanager "ndk-bundle"
yes | sdkmanager "ndk;21.4.7075529"

# building in a venv gives mixed results, so we are not doing that
python3 -m pip install -U setuptools wheel Cython
python3 -m pip install -U git+https://github.com/pygame/python-for-android.git
# python3 -m pip install -U python-for-android
# --requirements=openssl,pygame,libffi,tuxemon \
cp run_tuxemon.py main.py
# rebuild...
rm -rf ~/.local/share/python-for-android/dists/unnamed_dist_1__armeabi-v7a/_python_bundle/
rm ~/.local/share/python-for-android/packages/tuxemon/development.zip
p4a clean_recipe_build tuxemon
p4a clean_dists
p4a apk --name Tuxemon \
  --private tuxemon \
  --version 0.0 \
  --package=org.tuxemon.tuxemon \
  --requirements=python3,openssl,pygame,libffi,tuxemon,babel,pytmx,pyscroll,natsort,android \
  --bootstrap=sdl2 \
  --orientation=landscape \
  --permission READ_EXTERNAL_STORAGE \
  --permission WRITE_EXTERNAL_STORAGE
mkdir -p dist/android
mv *apk dist/android/tuxemon-development.apk
