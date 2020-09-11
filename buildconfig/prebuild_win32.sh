#!/bin/bash
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install wget xvfb
sudo apt-get install -o APT::Immediate-Configure=false wine wine32 wine64
# sudo apt-get -f install
# sudo dpkg --configure -a
# sudo apt-get dist-upgrade
