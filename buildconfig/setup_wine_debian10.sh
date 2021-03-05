#!/bin/bash
# install wine 6.x and python into wine
cd /tmp
sudo apt-get update
sudo apt install wget
wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public | sudo apt-key add -
wget -qO - https://dl.winehq.org/wine-builds/winehq.key | sudo apt-key add -
wget -qO https://download.opensuse.org/repositories/Emulators:/Wine:/Debian/Debian_10/Release.key | sudo apt-key add -
echo "deb https://dl.winehq.org/wine-builds/debian/ buster main" | sudo tee /etc/apt/sources.list.d/wine.list
echo "deb https://download.opensuse.org/repositories/Emulators:/Wine:/Debian/Debian_10 ./" | sudo tee -a /etc/apt/sources.list.d/wine.list
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt -y remove wine wine32 wine64 wine-staging
sudo apt -y install --install-recommends winehq-stable
sudo apt -y install xvfb winetricks
sudo apt -y autoremove
[ -e python-3.9.2-amd64.exe ] || wget -q https://www.python.org/ftp/python/3.9.2/python-3.9.2-amd64.exe
rm -rf ~/.wine
wineboot -u
xvfb-run winetricks win10
xvfb-run wine python-3.9.2-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 SimpleInstall=1
