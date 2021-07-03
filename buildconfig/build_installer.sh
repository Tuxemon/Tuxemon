#!/bin/bash
export NSIS_DOWNLOAD_LINK="https://netcologne.dl.sourceforge.net/project/nsis/NSIS%203/3.06.1/nsis-3.06.1-setup.exe"

# Download and install NSIS
sudo apt -y install wget
wget $NSIS_DOWNLOAD_LINK -O nsis.exe

wine nsis.exe /S # Should silently install nsis

echo "build_installer.bat" | wine cmd

mkdir ../dist/
mv tuxemon-installer.exe ../dist/.
