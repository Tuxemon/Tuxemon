#!/bin/bash
# debian 10
buildconfig/setup_wine_debian10.sh
wine python -m pip install -U setuptools wheel cx_Freeze
wine python -m pip install -U -r requirements.txt
find . -name "*pyc" -delete
wine python buildconfig/setup_cx_freeze.py build
cd build/exe.win*
cp ~/.wine/drive_c/Program\ Files/Python39/python39.dll .
cp ../../LICENSE .
cp ../../CONTRIBUTING.md .
cp ../../CREDITS.md .
cp ../../README.md .
cp ../../SPYDER_README.md .
cd ../../
mkdir -p dist/windows_cx_freeze
cp -a build/exe.win*/* dist/windows_cx_freeze
