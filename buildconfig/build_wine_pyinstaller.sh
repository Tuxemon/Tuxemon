#!/bin/bash
# debian 10
./setup_wine_debian10.sh
wine python -m pip install -U setuptools wheel pyinstaller
wine python -m pip install -U -r requirements.txt
find . -name "*pyc" -delete
wine pyinstaller buildconfig/pyinstaller/tuxemon.spec
cd dist/tuxemon
cp ../../LICENSE .
cp ../../CONTRIBUTING.md .
cp ../../CREDITS.md .
cp ../../README.md .
cp ../../SPYDER_README.md .
