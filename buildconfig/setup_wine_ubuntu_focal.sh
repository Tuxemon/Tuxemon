#!/bin/bash
# install winehq-staging and python into wine
set -e
sudo apt install wget
wget -qO - https://dl.winehq.org/wine-builds/winehq.key | sudo apt-key add -
sudo add-apt-repository "deb https://dl.winehq.org/wine-builds/ubuntu/ focal main"
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt -y remove wine wine32 wine64 wine-staging
sudo apt -y install --install-recommends winehq-stable
sudo apt -y install xvfb winetricks
sudo apt -y autoremove
[ -e python-3.9.7-amd64.exe ] || wget -q https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe
rm -rf ~/.wine
wineboot -u
export WINEDLLOVERRIDES="mscoree,mshtml="
xvfb-run winetricks -q win10
xvfb-run wine python-3.9.7-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 SimpleInstall=1
