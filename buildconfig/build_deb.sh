#!/bin/bash
export PYBUILD_DISABLE=test
cd tuxemon-*
cp ../dist/* ..
debmake -b':py3'
echo "./mods usr/share/tuxemon/" > debian/install
dpkg-buildpackage -us -uc
cd ..
mv tuxemon*.deb build/tuxemon-$TRAVIS_DIST-$TRAVIS_BRANCH.deb
