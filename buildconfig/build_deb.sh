#!/bin/bash
cd tuxemon-*
cp ../dist/* ..
debmake -b':py3'
dpkg-buildpackage -us -uc
cd ../..
mv ./dist/tuxemon*.deb ./build/tuxemon-unstable-latest.deb
