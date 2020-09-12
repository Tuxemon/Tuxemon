#!/bin/bash
sudo apt-get update
sudo apt-get install -y fakeroot debmake debhelper dh-python python3-lxml python3-pil \
python3-babel python3-cbor python3-natsort python3-click python3-pygame python3-all \
python3-setuptools
pip install -r requirements.txt
