#!/bin/bash
# debian 10
sudo apt install wget
mkdir -p build/wine_cx_freeze
cd build/wine_cx_freeze
wget -nc https://dl.winehq.org/wine-builds/winehq.key
wget -nc https://download.opensuse.org/repositories/Emulators:/Wine:/Debian/Debian_10/Release.key
sudo apt-key add winehq.key
sudo apt-key add Release.key
echo "deb https://dl.winehq.org/wine-builds/debian/ buster main" | sudo tee /etc/apt/sources.list.d/wine.list
echo "deb https://download.opensuse.org/repositories/Emulators:/Wine:/Debian/Debian_10 ./" | sudo tee -a /etc/apt/sources.list.d/wine.list
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt -y remove wine wine32 wine64 wine-staging
sudo apt -y autoremove
sudo apt -y install --install-recommends winehq-stable
sudo apt -y install xvfb winetricks
[ -e python-3.9.2-amd64.exe ] || wget -q https://www.python.org/ftp/python/3.9.2/python-3.9.2-amd64.exe
rm -rf ~/.wine
wineboot -u
xvfb-run winetricks win10
xvfb-run wine python-3.9.2-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 SimpleInstall=1
cd ../../
wine python -m pip install -U setuptools wheel cx_Freeze
wine python -m pip install -U -r requirements.txt
find . -name "*pyc" -delete
wine python buildconfig/setup_windows.py build
cp .wine/drive_c/Program Files/Python39/python39.dll build/exe.win-amd64-3.9/
