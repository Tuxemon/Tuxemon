#!/bin/bash
export WINEARCH=win32
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install wget xvfb wine wine32 wine64 winetricks
rm -rf ~/.wine
xvfb-run wine wineboot
wget -q https://www.python.org/ftp/python/3.8.5/python-3.8.5.exe
xvfb-run wine python-3.8.5.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 SimpleInstall=1
