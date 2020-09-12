#!/bin/bash
sudo apt-get update
sudo apt-get install -y fakeroot debmake debhelper dh-python python3-all python3-setuptools
sudo pip install -r requirements.txt
