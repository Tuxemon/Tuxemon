#!/bin/bash
cp dist/* .
cd tuxemon-*
debmake -b':py3'
dpkg-buildpackage -us -uc
cd ../..
mv ./dist/tuxemon*.deb ./build/tuxemon-unstable-latest.deb
