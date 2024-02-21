#!/bin/bash
# debian 10
buildconfig/setup_wine_debian10.sh
wine python -m pip install -U setuptools wheel pyinstaller
wine python -m pip install -U -r requirements.txt
find . -name "*pyc" -delete
wine pyinstaller buildconfig/pyinstaller/tuxemon.spec
cd build/tuxemon
cp ~/.wine/drive_c/Program\ Files/Python39/python39.dll .
cp ../../LICENSE .
cp ../../CONTRIBUTING.md .
cp ../../CONTRIBUTORS.md .
cp ../../ATTRIBUTIONS.md .
cp ../../README.md .
cp ../../SPYDER_README.md .
