#!/bin/bash
wget -q https://www.python.org/ftp/python/3.8.5/python-3.8.5-amd64.exe
xvfb-run wine64 python-3.8.5-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 SimpleInstall=1
wine64 pip install -r requirements.txt
wine64 pip install cx_freeze
wine64 python buildconfig/setup_win32.py build
