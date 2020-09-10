#!/bin/bash
cd dist
tar xvfz tuxemon*.tar.gz
cd tuxemon*
debmake -b':py3'
dpkg-buildpackage -us -uc
cd ../..
mv ./dist/tuxemon*.deb ./build/tuxemon-unstable-latest.deb
