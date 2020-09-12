#!/bin/bash
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y build-essential ccache git zlib1g-dev python3 python3-dev \
libncurses5:i386 libstdc++6:i386 zlib1g:i386 openjdk-8-jdk unzip ant ccache \
autoconf libtool libssl-dev
