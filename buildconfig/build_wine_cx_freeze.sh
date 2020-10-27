#!/bin/bash
# for ubuntu 20.04 focal
export WINEARCH=win32
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install wget xvfb wine wine32 wine64 winetricks
rm -rf ~/.wine
xvfb-run wine wineboot
wget -q https://www.python.org/ftp/python/3.8.5/python-3.8.5.exe
xvfb-run wine python-3.8.5.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 SimpleInstall=1
wine python -m pip install -U setuptools wheel cx_Freeze
wine python -m pip install -U -r requirements.txt
wine python buildconfig/setup_windows.py build
cp -a mods build/exe.win32-3.8/
