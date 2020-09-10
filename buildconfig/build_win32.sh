#!/bin/bash
# embedded WIP
#cd pywin64
#wget https://www.python.org/ftp/python/3.8.5/python-3.8.5-embed-amd64.zip
#wget https://bootstrap.pypa.io/get-pip.py
#unzip *zip
#echo "import site" >> python38._pth
#wine python get-pip.py
#cd ..
#wine pywin64/Scripts/pip install -r requirements.txt
#wine pywin64/Scripts/pip install cx_freeze
#wine pywin64/python.exe buildconfig/setup_win32.py build

# install with full python installer
wget https://www.python.org/ftp/python/3.8.5/python-3.8.5-amd64.exe
xvfb-run wine python-3.8.5-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 SimpleInstall=1
wine pip install -r requirements.txt
wine pip install cx_freeze
wine python buildconfig/setup_win32.py build
