#!/bin/bash
wget -q https://www.python.org/ftp/python/3.8.5/python-3.8.5-amd64.exe
./python-3.8.5-amd64 /quiet PrependPath=1 Include_doc=0 Include_test=0 SimpleInstall=1
pip install -r requirements.txt
pip install cx_freeze
python buildconfig/setup_win32.py build
