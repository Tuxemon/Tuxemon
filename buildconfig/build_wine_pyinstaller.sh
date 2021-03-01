#!/bin/bash
# debian 10
./setup_wine_debian10.sh
wine pip install -U setuptools wheel pyinstaller
wine pip install -U -r requirements.txt
find . -name "*pyc" -delete
wine pyinstaller buildconfig/pyinstaller/tuxemon.spec
cd dist
zip -r tuxemon-windows-development.zip tuxemon
mv *zip ../build
